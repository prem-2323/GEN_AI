import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from text.document_extractor import extract_docx, extract_pdf, extract_txt
from text.qwen_service import QwenServiceError

from .generator import ImageGenerationError, is_last_synthetic
from .prompt_engine import generate_scene_prompts
from .schemas import ImageRequest, ImageResponse, SceneImageRequest, SceneImageResponse
from .service import generate_and_save_image, image_path


router = APIRouter(tags=["Image Generation"])


FORGE_OFFLINE_WARNING = (
    "Stable Diffusion Forge is offline at 127.0.0.1:7860 — this is a preview "
    "placeholder, not AI-generated imagery. Run start_forge.bat (or "
    "start-all-services.bat window 2 / stable-diffusion-webui-forge/start-image-api.bat), "
    "then regenerate."
)


def _check_forge_health() -> dict:
    """Probe the Forge WebUI API to report whether real image generation is available."""
    import requests

    base_url = os.getenv("IMAGE_MODEL_URL", "http://127.0.0.1:7860").rstrip("/")
    try:
        response = requests.get(f"{base_url}/sdapi/v1/options", timeout=2.0)
        online = response.status_code == 200
    except Exception:
        online = False
    return {
        "forge_url": base_url,
        "online": online,
        "message": (
            "Forge is online — real Stable Diffusion generation enabled."
            if online
            else "Forge is offline — generations will return preview placeholders. "
            "Run start_forge.bat to start it."
        ),
    }


@router.get("/status", summary="Forge image-generation status")
def image_studio_status():
    """Report whether Stable Diffusion Forge is reachable at IMAGE_MODEL_URL."""
    return _check_forge_health()


def _generate(request: ImageRequest, prefix: str = "image") -> ImageResponse:
    try:
        filename, generation_time, device = generate_and_save_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            steps=request.steps,
            mode=request.mode,
            prefix=prefix,
        )
    except ImageGenerationError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error

    synthetic = is_last_synthetic()

    return ImageResponse(
        status="success",
        filename=filename,
        image_path=f"generated_images/{filename}",
        image_url=f"/image/{filename}",
        generation_time=generation_time,
        device=device,
        steps=request.steps,
        width=request.width,
        height=request.height,
        synthetic=synthetic,
        warning=FORGE_OFFLINE_WARNING if synthetic else None,
    )


@router.post("/generate-image", response_model=ImageResponse)
def generate_image(request: ImageRequest):
    """Generate one image directly from a user-supplied prompt with performance tracking."""
    return _generate(request)


@router.post("/generate-scene-images", response_model=SceneImageResponse)
def generate_scene_images(request: SceneImageRequest):
    """Turn a video script into Qwen-engineered prompts and generate one image per scene."""
    try:
        scenes = generate_scene_prompts(request.script)
    except QwenServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    images = []
    for index, scene in enumerate(scenes, 1):
        image_request = ImageRequest(
            prompt=scene["prompt"],
            negative_prompt=request.negative_prompt,
            mode=request.mode,
            width=request.width,
            height=request.height,
            steps=request.steps,
        )
        images.append(_generate(image_request, prefix=f"scene_{index:02d}"))
    return SceneImageResponse(images=images)


def _extract_uploaded_text(upload: UploadFile) -> str:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix == ".txt":
        return extract_txt(upload)
    if suffix == ".pdf":
        return extract_pdf(upload)
    if suffix == ".docx":
        return extract_docx(upload)
    raise HTTPException(status_code=400, detail="Only TXT, PDF and DOCX files are supported.")


@router.post("/generate-scene-images-from-file", response_model=SceneImageResponse)
async def generate_scene_images_from_file(file: UploadFile = File(...)):
    """Extract a document, have Qwen create a storyboard, then generate its scene images."""
    content = _extract_uploaded_text(file)
    if not content.strip():
        raise HTTPException(status_code=400, detail="The uploaded document contains no text.")
    return generate_scene_images(SceneImageRequest(script=content))


@router.get("/image/{filename}", response_class=FileResponse)
def get_image(filename: str, download: bool = False):
    """Retrieve a generated PNG by filename (inline for <img>, or forced download)."""
    path = image_path(filename)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not found.")
    if download:
        return FileResponse(path, media_type="image/png", filename=path.name)
    return FileResponse(path, media_type="image/png")
