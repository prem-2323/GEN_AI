from pydantic import BaseModel, model_validator
from typing import Optional, Union, Dict, Any, List


class BrandVoiceProfile(BaseModel):
    brand_name: str = "Enterprise AI"
    brand_tone: str = "Professional, Authoritative & Empathetic"
    preferred_vocabulary: List[str] = ["enterprise-grade", "seamless", "synergy", "grounded intelligence"]
    forbidden_phrases: List[str] = ["game-changer", "revolutionary", "cheap", "unmatched"]
    hashtag_rules: str = "Max 3 hashtags: #AI #Enterprise #Innovation"
    formatting_style: str = "Bulleted headlines, Markdown bold emphasis"
    disclaimer: str = "Confidential & Proprietary. All rights reserved."
    logo_url: Optional[str] = ""
    primary_color: str = "#1ED760"
    secondary_color: str = "#181818"
    accent_color: str = "#9333EA"


class AudienceReframeRequest(BaseModel):
    text: str
    audiences: Optional[List[str]] = [
        "CEO or executives",
        "Technical teams",
        "General public",
        "Students",
        "Customers",
        "Journalists",
        "Government officials"
    ]
    brand_voice: Optional[BrandVoiceProfile] = None


class AudienceReframeResponse(BaseModel):
    status: str = "success"
    source_text_length: int
    reframed_outputs: Dict[str, str]


class TextRequest(BaseModel):
    text: str = ""
    url: Optional[str] = None
    output_type: Optional[str] = None
    output_types: Optional[List[str]] = None
    audience: str = "General public"
    tone: str = "Professional"
    language: str = "English"
    detail_level: str = "Medium"
    objective: str = "Inform"
    duration: Optional[Union[int, str]] = 30
    brand_voice: Optional[BrandVoiceProfile] = None

    @model_validator(mode='after')
    def resolve_output_types(self):
        if not self.output_types:
            if self.output_type:
                self.output_types = [self.output_type]
            else:
                self.output_types = ["summary"]
        if not self.output_type and self.output_types:
            self.output_type = self.output_types[0]
        return self


class TextResponse(BaseModel):
    output_type: Optional[str] = None
    output_types: List[str]
    audience: str
    tone: str
    language: str
    detail_level: str
    objective: str
    outputs: Dict[str, Union[Dict[str, Any], str, Any]]
    generated_content: Optional[Union[Dict[str, Any], str, Any]] = None
    brand_voice: Optional[BrandVoiceProfile] = None
    uckr: Optional[Dict[str, Any]] = None
    validation_report: Optional[Dict[str, Any]] = None
    source_text: Optional[str] = None


class FileTextResponse(TextResponse):
    filename: str
    extracted_text: str


class AudioRequest(BaseModel):
    text: str
    voice: str = "en-US-AriaNeural"
    translate_to_voice_language: bool = True


class VideoAudioRequest(BaseModel):
    video_script: Union[Dict[str, Any], str]
    voice: str = "en-US-AriaNeural"
    translate_to_voice_language: bool = True


class AudioResponse(BaseModel):
    status: str = "success"
    filename: str
    audio_path: str
    download_url: str
    voice: str
    spoken_text: str
    translated: bool = False
