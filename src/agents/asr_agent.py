"""
ASR Agent that wraps Google Speech-to-Text integration.
"""

from typing import Any, Dict, Optional

from src.agents.base_agent import AgentResult, BaseAgent
from src.integrations.google_speech import GoogleSpeechClient


class ASRAgent(BaseAgent):
    """Agent to transcribe audio into text."""

    def __init__(self, model_client, speech_client: Optional[GoogleSpeechClient] = None, **kwargs):
        super().__init__(model_client, **kwargs)
        self.speech_client = speech_client or GoogleSpeechClient()

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Expected input_data: {"audio_path": "..."} or {"audio_content": bytes}
        """
        self._validate_input(input_data)

        try:
            if "audio_path" in input_data:
                transcript, confidence = self.speech_client.transcribe_file(input_data["audio_path"])
            elif "audio_content" in input_data:
                transcript, confidence = self.speech_client.transcribe_content(input_data["audio_content"])
            else:
                return self._create_failure_result("audio_path or audio_content required")

            return self._create_success_result(
                {"transcript": transcript, "confidence": confidence}
            )
        except Exception as exc:  # pragma: no cover - defensive
            return self._create_failure_result(
                "ASR transcription failed",
                metadata={"error": str(exc)}
            )
