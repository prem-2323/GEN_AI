import os
import edge_tts

RECOMMENDED_VOICES = {
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

DEFAULT_VOICE = "en-US-AriaNeural"


from text.tts import generate_audio as text_generate_audio


async def generate_narration(
    text: str,
    output_file: str,
    voice: str = DEFAULT_VOICE,
    rate: str = "+0%",
) -> str:
    """Convert narration text to MP3 using Edge TTS with fallback to Windows SAPI."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    return await text_generate_audio(text=text, output_file=output_file, voice=voice, rate=rate)


async def generate_scene_narrations(
    scenes: list,
    output_dir: str,
    voice: str = DEFAULT_VOICE,
    prefix: str = "scene",
    rate: str = "+0%",
) -> list[str]:
    """Generate one MP3 per scene and return list of output file paths.

    Args:
        scenes: List of scene dicts, each containing a 'narration' key.
        output_dir: Directory to save MP3 files into.
        voice: Edge TTS voice name.
        prefix: Filename prefix (e.g. "scene" → scene_01.mp3).

    Returns:
        Ordered list of MP3 file paths matching the input scenes.
    """
    os.makedirs(output_dir, exist_ok=True)
    audio_files = []

    for i, scene in enumerate(scenes, start=1):
        narration_text = scene.get("narration", "").strip()
        if not narration_text:
            narration_text = f"Scene {i}."

        output_file = os.path.join(output_dir, f"{prefix}_{i:02d}.mp3")
        await generate_narration(narration_text, output_file, voice, rate)
        audio_files.append(output_file)

    return audio_files
