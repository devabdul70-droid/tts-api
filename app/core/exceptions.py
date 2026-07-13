class TTSError(Exception):
    """Base exception for TTS-related failures."""


class TTSGenerationError(TTSError):
    """Raised when edge-tts fails to synthesize audio."""


class InvalidVoiceError(TTSError):
    """Raised when the requested voice is not recognized by edge-tts."""
