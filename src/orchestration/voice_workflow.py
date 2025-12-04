"""
Voice workflow orchestration.

Runs a single turn of the ASR -> NLU/Dialog -> TTS loop and can be reused
inside a larger WorkflowEngine pipeline.
"""

from typing import Any, Dict, Optional

from src.utils.conversation_state import ConversationState


class VoiceWorkflow:
    """Lightweight voice workflow runner."""

    def __init__(self, asr_agent, dialogue_manager, tts_agent, logger=None):
        self.asr_agent = asr_agent
        self.dialogue_manager = dialogue_manager
        self.tts_agent = tts_agent
        self.logger = logger or (lambda msg: None)

    async def run_turn(
        self,
        audio_path: str,
        state: Optional[ConversationState] = None,
    ) -> Dict[str, Any]:
        """Run a single voice turn."""
        asr_result = await self.asr_agent.execute({"audio_path": audio_path})
        transcript = asr_result.output.get("transcript", "")

        dm_result = await self.dialogue_manager.execute(
            {"utterance": transcript, "state": state}
        )
        response_text = dm_result.output.get("text") or dm_result.output.get("answer") or "Okay."

        tts_result = await self.tts_agent.execute(
            {"text": response_text, "output_path": "turn.mp3"}
        )

        self.logger(
            {
                "transcript": transcript,
                "response": response_text,
                "state": dm_result.output.get("state"),
            }
        )

        return {
            "transcript": transcript,
            "response": response_text,
            "audio_path": tts_result.output.get("path"),
            "state": dm_result.output.get("state"),
        }
