import json
import re
from typing import Any, Dict, List, Union

from text.qwen_service import QwenServiceError, generate_with_qwen


PROMPT_ENGINE_INSTRUCTIONS = """
You are an expert visual prompt engineer. Turn the supplied content into a concise
JSON array of cinematic image prompts. Return only JSON in this shape:
{"scenes":[{"scene":1,"prompt":"..."}]}
Create one scene for each storyboard scene when a storyboard is supplied, otherwise
create three distinct scenes. Each prompt must describe subject, setting, action,
composition, lighting, mood, and realistic visual style. Do not include readable text,
logos, watermarks, or camera metadata in the prompt.

CONTENT:
"""


def _parse_json(candidate: str) -> Dict[str, Any]:
    cleaned = re.sub(r"<think>.*?</think>", "", candidate or "", flags=re.IGNORECASE | re.DOTALL).strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", cleaned, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        cleaned = fenced.group(1)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise QwenServiceError("Qwen returned an invalid image-scene response.")
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as error:
            raise QwenServiceError("Qwen returned an invalid image-scene response.") from error
    if not isinstance(payload, dict) or not isinstance(payload.get("scenes"), list):
        raise QwenServiceError("Qwen returned no image scenes.")
    return payload


def _fallback_scenes(script: Union[Dict[str, Any], str]) -> List[Dict[str, Any]]:
    if isinstance(script, dict):
        storyboard = script.get("storyboard", [])
        if isinstance(storyboard, list) and storyboard:
            return [
                {"scene": item.get("scene", index), "prompt": item.get("visuals", "")}
                for index, item in enumerate(storyboard, 1)
                if isinstance(item, dict) and item.get("visuals")
            ]
    return [{"scene": 1, "prompt": str(script)}]


def generate_scene_prompts(script: Union[Dict[str, Any], str]) -> List[Dict[str, Any]]:
    try:
        source = json.dumps(script, ensure_ascii=True) if isinstance(script, dict) else script
        response = generate_with_qwen(PROMPT_ENGINE_INSTRUCTIONS + source[:12000])
        scenes = _parse_json(response).get("scenes", [])
        valid_scenes = [
            {"scene": item.get("scene", index), "prompt": str(item.get("prompt", "")).strip()}
            for index, item in enumerate(scenes, 1)
            if isinstance(item, dict) and str(item.get("prompt", "")).strip()
        ]
        if valid_scenes:
            return valid_scenes
    except Exception as err:
        print(f"[Prompt Engine Fallback] Qwen prompt engineering offline/failed ({err}). Using fallback storyboard scenes.")

    return _fallback_scenes(script)
