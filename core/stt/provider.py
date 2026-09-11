from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str

class Transcript(BaseModel):
    text: str
    segments: List[TranscriptSegment] = []
    language: Optional[str] = None
    duration: float = 0.0

class STTProvider(ABC):
    """
    Abstract Base Class for Speech-to-Text providers.
    Ensures that the core is agnostic of the underlying STT implementation (e.g. Whisper, FasterWhisper).
    """

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> Transcript:
        """
        Transcribes raw audio bytes into text.
        """
        pass
