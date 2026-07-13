import re
from pydantic import BaseModel, Field, field_validator

_RATE_PITCH_VOLUME_RE = re.compile(r"^[+-]\d+%$")
_PITCH_RE = re.compile(r"^[+-]\d+Hz$")


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: str = Field(default="en-US-AvaNeural", description="Edge TTS voice short name")
    rate: str = Field(default="-10%", description="Speech rate adjustment, e.g. '-10%', '+20%'")
    pitch: str = Field(default="+0Hz", description="Pitch adjustment, e.g. '+0Hz', '-5Hz'")
    volume: str = Field(default="+0%", description="Volume adjustment, e.g. '+0%', '-10%'")

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank or whitespace only")
        return v

    @field_validator("rate", "volume")
    @classmethod
    def validate_percentage_field(cls, v: str) -> str:
        if not _RATE_PITCH_VOLUME_RE.match(v):
            raise ValueError("must be in the form '+N%' or '-N%', e.g. '-10%'")
        return v

    @field_validator("pitch")
    @classmethod
    def validate_pitch_field(cls, v: str) -> str:
        if not _PITCH_RE.match(v):
            raise ValueError("must be in the form '+NHz' or '-NHz', e.g. '+0Hz'")
        return v


class VoiceInfo(BaseModel):
    short_name: str
    gender: str
    locale: str


class ErrorResponse(BaseModel):
    detail: str
