import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.core.exceptions import TTSGenerationError, InvalidVoiceError
from app.schemas import TTSRequest, VoiceInfo
from app.services.tts_service import TTSService, get_tts_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Text-to-Speech"])


@router.post(
    "/tts",
    summary="Convert text to speech",
    response_class=Response,
    responses={
        200: {"content": {"audio/mpeg": {}}, "description": "MP3 audio stream"},
        400: {"description": "Invalid request (bad voice, malformed rate/pitch, etc.)"},
        504: {"description": "Synthesis timed out"},
        500: {"description": "Synthesis failed"},
    },
)
async def text_to_speech(
    request: TTSRequest,
    service: TTSService = Depends(get_tts_service),
    settings: Settings = Depends(get_settings),
) -> Response:
    try:
        audio_bytes = await asyncio.wait_for(
            service.synthesize(request),
            timeout=settings.REQUEST_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Speech synthesis timed out")
    except InvalidVoiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except TTSGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": 'attachment; filename="speech.mp3"'},
    )


@router.get(
    "/voices",
    summary="List available TTS voices",
    response_model=list[VoiceInfo],
)
async def list_voices(
    locale: str | None = Query(default=None, description="Filter by locale, e.g. 'en-US'"),
    service: TTSService = Depends(get_tts_service),
) -> list[VoiceInfo]:
    try:
        return await service.list_voices(locale=locale)
    except TTSGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
