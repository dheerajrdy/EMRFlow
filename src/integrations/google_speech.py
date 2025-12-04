"""
Thin wrapper around Google Cloud Speech-to-Text.

Designed to be easily mocked in tests while providing a clean interface for agents.
"""

from pathlib import Path
from typing import Optional, Tuple

try:
    from google.cloud import speech  # type: ignore
except ImportError:  # pragma: no cover - handled in runtime guard
    speech = None


class GoogleSpeechClient:
    """Speech-to-text client using Google Cloud."""

    def __init__(self, language_code: str = "en-US", sample_rate_hertz: Optional[int] = None, encoding: str = "LINEAR16"):
        self.language_code = language_code
        self.sample_rate_hertz = sample_rate_hertz
        self.encoding = encoding
        self._client = None

    def transcribe_file(self, file_path: str) -> Tuple[str, float]:
        """Transcribe an audio file path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        content = path.read_bytes()
        return self.transcribe_content(content)

    def transcribe_content(self, content: bytes) -> Tuple[str, float]:
        """Transcribe raw audio bytes."""
        self._ensure_client()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=getattr(speech.RecognitionConfig.AudioEncoding, self.encoding),
            sample_rate_hertz=self.sample_rate_hertz,
            language_code=self.language_code,
            enable_automatic_punctuation=True,
        )

        response = self._client.recognize(config=config, audio=audio)
        transcript, confidence = self._extract_best(response)
        if confidence < 0.6:
            raise ValueError("Audio unclear or confidence too low")
        return transcript, confidence

    @staticmethod
    def _extract_best(response) -> Tuple[str, float]:
        if not response.results:
            return "", 0.0
        best_alt = response.results[0].alternatives[0]
        return getattr(best_alt, "transcript", ""), getattr(best_alt, "confidence", 0.0)

    def _ensure_client(self):
        if speech is None:
            raise ImportError("google-cloud-speech is not installed. Install per requirements.txt")
        if self._client is None:
            self._client = speech.SpeechClient()
