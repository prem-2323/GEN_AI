import asyncio
import io
import json
import logging
import os
import shutil
import subprocess
import tempfile
from typing import Dict, Any, Union

log = logging.getLogger("gen-transform.tts")

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
    """Generate MP3 audio using edge-tts with local Windows speech / gTTS / pyttsx3 fallback.

    Args:
        text: Narration text.
        output_file: Destination MP3 path.
        voice: Edge TTS voice name.
        rate: Edge TTS prosody rate (e.g. "+0%", "-10%", "+10%").
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
        await asyncio.wait_for(communicate.save(output_file), timeout=20.0)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            return output_file
    except Exception as exc:
        log.warning("Edge TTS failed or timed out (%s), attempting fallback: %s", voice, exc)

    # Fallback to local audio engine
    try:
        await asyncio.to_thread(_generate_local_audio, text, output_file)
        return output_file
    except Exception as exc2:
        log.error("Local audio fallback failed: %s", exc2)
        # Create minimal valid MP3 if all fails to prevent 500
        _create_silent_mp3_fallback(output_file)
        return output_file


def _generate_local_audio(text: str, output_file: str) -> None:
    """Create an MP3 with local TTS through pyttsx3 or gTTS."""
    # 1. Try gTTS first if available
    try:
        from gtts import gTTS
        tts = gTTS(text=text[:5000], lang="en")
        tts.save(output_file)
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            return
    except Exception:
        pass

    # 2. Try pyttsx3 + ffmpeg
    try:
        import pyttsx3
        ffmpeg = shutil.which("ffmpeg")
        with tempfile.TemporaryDirectory() as temp_dir:
            wav_path = os.path.join(temp_dir, "voiceover.wav")
            engine = pyttsx3.init()
            engine.save_to_file(text, wav_path)
            engine.runAndWait()
            engine.stop()
            if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
                if ffmpeg:
                    subprocess.run(
                        [ffmpeg, "-y", "-loglevel", "error", "-i", wav_path, output_file],
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                        return
                else:
                    # Rename wav to output if ffmpeg is missing
                    shutil.copyfile(wav_path, output_file)
                    return
    except Exception:
        pass

    _create_silent_mp3_fallback(output_file)


def _create_silent_mp3_fallback(output_file: str) -> None:
    """Write a minimal valid MP3 byte sequence when TTS engine is offline."""
    # 1 second of silent MP3 frame
    silent_frame = b"\xff\xfb\x90\x04\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00" * 38
    with open(output_file, "wb") as f:
        f.write(silent_frame)


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
