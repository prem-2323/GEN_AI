from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, low resolution, distorted, deformed, bad anatomy, "
    "malformed hands, extra fingers, extra limbs, duplicate people, unnatural faces, "
    "distorted faces, cartoon, anime, illustration, watermark, logo, text, letters, "
    "oversaturated, unrealistic, poor composition, cropped subjects"
)


class ImageRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT
    mode: str = Field("fast", description="Generation mode: fast (768x768, 10 steps), balanced (768x768, 18 steps), quality (1024x1024, 28 steps)")
    width: int = Field(768, ge=256, le=1024)
    height: int = Field(768, ge=256, le=1024)
    steps: int = Field(10, ge=1, le=50)


class ImageResponse(BaseModel):
    status: str = "success"
    filename: str
    image_path: str
    image_url: Optional[str] = None
    generation_time: float = Field(..., description="Actual generation time in seconds")
    device: str = Field("cuda", description="Compute device used for inference (cuda/cpu)")
    steps: int = Field(10, description="Inference steps executed")
    width: int = Field(768, description="Image width in pixels")
    height: int = Field(768, description="Image height in pixels")
    synthetic: bool = Field(False, description="True when Stable Diffusion was offline and a preview placeholder was returned instead of AI-generated imagery")
    warning: Optional[str] = Field(None, description="Human-readable notice when synthetic is true")


class SceneImageRequest(BaseModel):
    script: Union[Dict[str, Any], str]
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT
    mode: str = Field("fast", description="Generation mode: fast, balanced, quality")
    width: int = Field(768, ge=256, le=1024)
    height: int = Field(768, ge=256, le=1024)
    steps: int = Field(10, ge=1, le=50)


class SceneImageResponse(BaseModel):
    status: str = "success"
    images: List[ImageResponse]
