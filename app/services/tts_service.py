import asyncio
import io
import logging

import edge_tts

from app.core.exceptions import TTSGenerationError, InvalidVoiceError
from app.schemas import TTSRequest, VoiceInfo

logger = logging.getLogger(__name__)

# Simple in-process cache so we don't hit the edge-tts voice list endpoint on every request.
_voice_cache: list[VoiceInfo] | None = None
_voice_cache_lock = asyncio.Lock()


class TTSService:
    """Encapsulates all interaction with edge-tts."""

    async def list_voices(self, locale: str | None = None) -> list[VoiceInfo]:
        global _voice_cache

        if _voice_cache is None:
            async with _voice_cache_lock:
                if _voice_cache is None:  # re-check after acquiring lock
                    try:
                        raw_voices = await edge_tts.list_voices()
                    except Exception as exc:
                        logger.exception("Failed to fetch voice list from edge-tts")
                        raise TTSGenerationError("Unable to retrieve voice list") from exc

                    _voice_cache = [
                        VoiceInfo(
                            short_name=v["ShortName"],
                            gender=v["Gender"],
                            locale=v["Locale"],
                        )
                        for v in raw_voices
                    ]

        if locale:
            return [v for v in _voice_cache if v.locale.lower() == locale.lower()]
        return _voice_cache

    async def _is_valid_voice(self, voice: str) -> bool:
        voices = await self.list_voices()
        return any(v.short_name == voice for v in voices)

    async def synthesize(self, request: TTSRequest) -> bytes:
        """Generate MP3 audio bytes for the given request. Raises TTSError subclasses on failure."""

        if not await self._is_valid_voice(request.voice):
            raise InvalidVoiceError(f"Unknown voice: '{request.voice}'")

        communicate = edge_tts.Communicate(
            text=request.text,
            voice=request.voice,
            rate=request.rate,
            pitch=request.pitch,
            volume=request.volume,
        )

        buffer = io.BytesIO()
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])
        except Exception as exc:
            logger.exception("edge-tts synthesis failed")
            raise TTSGenerationError("Speech synthesis failed") from exc

        audio_bytes = buffer.getvalue()
        if not audio_bytes:
            raise TTSGenerationError("Synthesis produced no audio output")

        return audio_bytes


def get_tts_service() -> TTSService:
    return TTSService()
