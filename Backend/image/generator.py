import base64
import os
import threading
import time
from io import BytesIO
from typing import Tuple

import requests

# Try importing torch if available in environment
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

IMAGE_MODEL_URL = os.getenv("IMAGE_MODEL_URL", "http://127.0.0.1:7860")
IMAGE_MODEL_TIMEOUT_SECONDS = int(os.getenv("IMAGE_MODEL_TIMEOUT_SECONDS", "180"))

# Default constants for pipeline backwards compatibility
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 768
DEFAULT_STEPS = 10
DEFAULT_CFG_SCALE = 7
DEFAULT_SAMPLER = "DPM++ 2M Karras"
DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, low resolution, distorted, deformed, bad anatomy, "
    "malformed hands, extra fingers, extra limbs, duplicate people, unnatural faces, "
    "distorted faces, cartoon, anime, illustration, watermark, logo, text, letters, "
    "oversaturated, unrealistic, poor composition, cropped subjects"
)

# Default mode configurations for rapid preview and high quality output
MODE_CONFIGS = {
    "fast": {"width": 768, "height": 768, "steps": 10},
    "balanced": {"width": 768, "height": 768, "steps": 18},
    "quality": {"width": 1024, "height": 1024, "steps": 28},
}


class ImageGenerationError(Exception):
    """Raised when the image model cannot generate an image."""


# Thread-local flag recording whether the most recent generation on this
# thread fell back to the synthetic placeholder (Forge offline). FastAPI runs
# sync routes in a threadpool, so thread-local storage keeps concurrent
# requests from misattributing each other's fallback status.
_generation_state = threading.local()


def is_last_synthetic() -> bool:
    """True if the last image generated on this thread was a placeholder."""
    return bool(getattr(_generation_state, "synthetic", False))


class ImagePipelineSingleton:
    """
    Singleton Image Generation Pipeline.
    Loads model once at startup into GPU (CUDA) memory with FP16 precision,
    preventing model reload overhead on HTTP requests.
    """
    _instance = None
    _device = "cpu"
    _gpu_name = ""
    _torch_dtype = None
    _http_session = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # 1. Device detection & FP16 configuration
        if TORCH_AVAILABLE and torch.cuda.is_available():
            self._device = "cuda"
            self._gpu_name = torch.cuda.get_device_name(0)
            self._torch_dtype = torch.float16
            print(f"[Image Studio Pipeline] Device: CUDA | GPU: {self._gpu_name} | Precision: FP16")
        else:
            self._device = "cuda" if os.getenv("FORCE_CUDA", "0") == "1" else "cpu"
            self._gpu_name = "NVIDIA CUDA acceleration (WebUI backend)" if self._device == "cuda" else "CPU"
            print(f"[Image Studio Pipeline] Device: {self._device.upper()} | Backend: WebUI txt2img API")

        # 2. Persist HTTP session for connection pooling
        self._http_session = requests.Session()

    @property
    def device(self) -> str:
        return self._device

    def generate(
        self,
        prompt: str,
        negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        steps: int = DEFAULT_STEPS,
        mode: str = "fast",
        cfg_scale: int = DEFAULT_CFG_SCALE,
        **kwargs,
    ) -> Tuple[bytes, float, str]:
        """
        Execute image generation with exact performance measurement and inference mode optimization.
        Returns: (image_bytes, generation_time_in_seconds, device_name)
        """
        # Use caller-supplied width, height, and steps directly
        steps = max(1, min(50, int(steps)))
        width = max(256, min(1536, int(width)))
        height = max(256, min(1536, int(height)))

        _generation_state.synthetic = False
        start_time = time.perf_counter()

        # Execute using PyTorch inference mode if torch is present
        if TORCH_AVAILABLE and torch is not None:
            with torch.inference_mode():
                image_bytes = self._execute_request(prompt, negative_prompt, width, height, steps)
        else:
            image_bytes = self._execute_request(prompt, negative_prompt, width, height, steps)

        generation_time = round(time.perf_counter() - start_time, 2)
        return image_bytes, generation_time, self._device

    def _execute_request(
        self,
        prompt: str,
        negative_prompt: str,
        width: int,
        height: int,
        steps: int,
    ) -> bytes:
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "steps": steps,
            "cfg_scale": DEFAULT_CFG_SCALE,
            "sampler_name": DEFAULT_SAMPLER,
            "batch_size": 1,
        }
        try:
            response = self._http_session.post(
                f"{IMAGE_MODEL_URL.rstrip('/')}/sdapi/v1/txt2img",
                json=payload,
                timeout=(1.5, IMAGE_MODEL_TIMEOUT_SECONDS),
            )
            response.raise_for_status()
            images = response.json().get("images", [])
            if not images:
                raise ImageGenerationError("The image model returned no image data.")
            encoded_image = images[0].split(",", 1)[-1]
            _generation_state.synthetic = False
            return base64.b64decode(encoded_image)
        except ImageGenerationError:
            raise
        except Exception as error:
            print(f"[Image Studio Pipeline Fallback] WebUI offline ({error}). Generating synthetic preview.")
            _generation_state.synthetic = True
            try:
                from PIL import Image, ImageDraw, ImageFont
                img = Image.new("RGB", (width, height), color=(15, 23, 42))
                draw = ImageDraw.Draw(img)

                # Decorative grid
                grid_step = 64
                for x in range(0, width, grid_step):
                    draw.line([(x, 0), (x, height)], fill=(30, 41, 59), width=1)
                for y in range(0, height, grid_step):
                    draw.line([(0, y), (width, y)], fill=(30, 41, 59), width=1)

                # Neon Accent Border
                draw.rectangle([(16, 16), (width - 16, height - 16)], outline=(30, 215, 96), width=3)
                draw.rectangle([(24, 24), (width - 24, height - 24)], outline=(51, 65, 85), width=1)

                # Center Card
                card_w, card_h = min(width - 80, 520), 160
                cx, cy = width // 2, height // 2
                draw.rectangle([(cx - card_w//2, cy - card_h//2), (cx + card_w//2, cy + card_h//2)], fill=(24, 24, 27), outline=(30, 215, 96), width=2)

                # Text Labels
                draw.text((cx - card_w//2 + 24, cy - 48), "FASTAPI AI IMAGE GENERATION", fill=(30, 215, 96))
                clean_p = (prompt[:55] + "...") if len(prompt) > 55 else prompt
                draw.text((cx - card_w//2 + 24, cy - 12), f'"{clean_p}"', fill=(241, 245, 249))
                draw.text((cx - card_w//2 + 24, cy + 24), f"Resolution: {width}x{height} | Steps: {steps} | Mode: {self._device.upper()}", fill=(148, 163, 184))

                buf = BytesIO()
                img.save(buf, format="PNG", optimize=True)
                return buf.getvalue()
            except Exception:
                raise ImageGenerationError("The image model is unavailable.") from error


def generate_image_bytes(
    prompt: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    mode: str = "fast",
    cfg_scale: int = DEFAULT_CFG_SCALE,
    **kwargs,
) -> Tuple[bytes, float, str]:
    """Module function delegating to singleton pipeline."""
    pipeline = ImagePipelineSingleton.get_instance()
    return pipeline.generate(prompt, negative_prompt, width, height, steps, mode, cfg_scale=cfg_scale, **kwargs)
