"""
Text-to-Speech Agent.

Uses Google Cloud Text-to-Speech (or injected mock client) to synthesize audio
files from text responses.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from src.agents.base_agent import AgentResult, BaseAgent

try:
    from google.cloud import texttospeech  # type: ignore
except ImportError:  # pragma: no cover - handled in runtime guard
    texttospeech = None


class GoogleTTSClient:
    """Wrapper around google-cloud-texttospeech for easy mocking."""

    def __init__(
        self,
        language_code: str = "en-US",
        voice_name: Optional[str] = None,
        speaking_rate: float = 1.0,
    ):
        if texttospeech is None:
            raise ImportError("google-cloud-texttospeech is not installed. Install per requirements.txt")
        self.language_code = language_code
        self.voice_name = voice_name
        self.speaking_rate = speaking_rate
        self._client = texttospeech.TextToSpeechClient()

    def synthesize_to_file(self, text: str, output_path: str) -> str:
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            language_code=self.language_code,
            name=self.voice_name,
            ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=self.speaking_rate,
        )

        response = self._client.synthesize_speech(
            input=synthesis_input,
            voice=voice_params,
            audio_config=audio_config,
        )
        Path(output_path).write_bytes(response.audio_content)
        return output_path


class TTSAgent(BaseAgent):
    """Agent that turns text responses into audio files."""

    def __init__(
        self,
        model_client,
        tts_client: Optional[Any] = None,
        default_output: str = "tts_output.mp3",
        **kwargs,
    ):
        super().__init__(model_client, **kwargs)
        self.tts_client = tts_client or GoogleTTSClient()
        self.default_output = default_output

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Expected input_data: {"text": "...", "output_path": "..."}.
        """
        self._validate_input(input_data)
        text = input_data.get("text")
        output_path = input_data.get("output_path", self.default_output)

        if not text:
            return self._create_failure_result("text is required for TTS")

        try:
            path = self.tts_client.synthesize_to_file(text, output_path)
            return self._create_success_result({"path": path})
        except Exception as exc:  # pragma: no cover - defensive
            return self._create_failure_result(
                "TTS synthesis failed",
                metadata={"error": str(exc)}
            )
