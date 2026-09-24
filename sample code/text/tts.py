import asyncio
import edge_tts
import json
import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any, Union

import pyttsx3

RECOMMENDED_VOICES: Dict[str, str] = {
    # Indian Languages
    "ta-IN-PallaviNeural": "Tamil (India) - Female (Pallavi)",
    "ta-IN-ValluvarNeural": "Tamil (India) - Male (Valluvar)",
    "hi-IN-SwaraNeural": "Hindi (India) - Female (Swara)",
    "hi-IN-MadhurNeural": "Hindi (India) - Male (Madhur)",
    "te-IN-ShrutiNeural": "Telugu (India) - Female (Shruti)",
    "te-IN-MohanNeural": "Telugu (India) - Male (Mohan)",
    "ml-IN-SobhanaNeural": "Malayalam (India) - Female (Sobhana)",
    "ml-IN-MidhunNeural": "Malayalam (India) - Male (Midhun)",
    "kn-IN-SapnaNeural": "Kannada (India) - Female (Sapna)",
    "kn-IN-GaganNeural": "Kannada (India) - Male (Gagan)",
    "bn-IN-TanishaaNeural": "Bengali (India) - Female (Tanishaa)",
    "bn-IN-BashkarNeural": "Bengali (India) - Male (Bashkar)",
    "mr-IN-AarohiNeural": "Marathi (India) - Female (Aarohi)",
    "mr-IN-ManoharNeural": "Marathi (India) - Male (Manohar)",
    "gu-IN-DhwaniNeural": "Gujarati (India) - Female (Dhwani)",
    "gu-IN-NiranjanNeural": "Gujarati (India) - Male (Niranjan)",
    "en-IN-NeerjaNeural": "English (India) - Female (Neerja)",
    "en-IN-PrabhatNeural": "English (India) - Male (Prabhat)",
    # Global Languages
    "en-US-AriaNeural": "English (US) - Female (Aria)",
    "en-US-GuyNeural": "English (US) - Male (Guy)",
    "en-GB-SoniaNeural": "English (UK) - Female (Sonia)",
}


async def generate_audio(
    text: str,
    output_file: str,
    voice: str = "en-US-AriaNeural",
    rate: str = "+0%",
) -> str:
    """Generate MP3 audio, using local Windows speech if Edge TTS is unavailable.

    Args:
        text: Narration text.
        output_file: Destination MP3 path.
        voice: Edge TTS voice name.
        rate: Edge TTS prosody rate (e.g. "+0%", "-10%", "+10%"). Used by the
            video studio to make the selected Tone audible. Ignored by the
            local SAPI fallback.
    """
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    try:
        await asyncio.wait_for(communicate.save(output_file), timeout=15.0)
        return output_file
    except Exception:
        await asyncio.to_thread(_generate_local_audio, text, output_file)
    return output_file


def _generate_local_audio(text: str, output_file: str) -> None:
    """Create an MP3 with the Windows SAPI voice through pyttsx3."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("Edge TTS is unavailable and FFmpeg is not installed for local audio fallback.")

    with tempfile.TemporaryDirectory() as temp_dir:
        wav_path = os.path.join(temp_dir, "voiceover.wav")
        engine = pyttsx3.init()
        engine.save_to_file(text, wav_path)
        engine.runAndWait()
        engine.stop()
        if not os.path.exists(wav_path) or os.path.getsize(wav_path) == 0:
            raise RuntimeError("Local speech synthesis did not produce audio.")

        result = subprocess.run(
            [ffmpeg, "-y", "-loglevel", "error", "-i", wav_path, output_file],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "FFmpeg could not encode the local voiceover.")


def extract_video_script_narration(video_script_input: Union[Dict[str, Any], str]) -> str:
    """
    Extract readable narration/voiceover text from a video script data structure.
    Works with raw string inputs or structured JSON/dict payloads containing storyboards.
    """
    data = video_script_input
    if isinstance(video_script_input, str):
        try:
            data = json.loads(video_script_input)
        except Exception:
            return video_script_input.strip()

    if isinstance(data, dict):
        # 1. If storyboard list is present, concatenate scene narrations
        if "storyboard" in data and isinstance(data["storyboard"], list):
            narrations = []
            for scene in data["storyboard"]:
                if isinstance(scene, dict):
                    scene_num = scene.get("scene", "")
                    narration = scene.get("narration") or scene.get("subtitle") or scene.get("on_screen_text", "")
                    if narration:
                        prefix = f"Scene {scene_num}: " if scene_num else ""
                        narrations.append(f"{prefix}{narration.strip()}")
            if narrations:
                intro = f"Video Title: {data.get('video_title', 'Video Package')}.\n" if "video_title" in data else ""
                return intro + "\n".join(narrations)

        # 2. Fallbacks for other dictionary keys
        if "narration" in data and isinstance(data["narration"], str):
            return data["narration"].strip()
        if "content" in data and isinstance(data["content"], str):
            return data["content"].strip()

    return str(video_script_input).strip()
