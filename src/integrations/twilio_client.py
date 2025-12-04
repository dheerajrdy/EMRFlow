"""
Twilio helper for building voice TwiML responses.
"""

from typing import Optional

try:
    from twilio.twiml.voice_response import VoiceResponse
except ImportError:  # pragma: no cover - handled at runtime
    VoiceResponse = None


class TwilioVoiceClient:
    """Lightweight helper for common Twilio voice responses."""

    def __init__(self, default_action: str = "/voice/handle"):
        if VoiceResponse is None:
            raise ImportError("twilio is not installed. Install per requirements.txt")
        self.default_action = default_action

    def gather(self, prompt: str, action_url: Optional[str] = None, timeout: int = 5) -> str:
        """Return TwiML that plays a prompt then gathers speech input."""
        vr = VoiceResponse()
        gather = vr.gather(
            input="speech",
            action=action_url or self.default_action,
            method="POST",
            timeout=timeout,
            speech_timeout="auto",
        )
        gather.say(prompt)
        return str(vr)

    def say_and_gather(self, message: str, action_url: Optional[str] = None, timeout: int = 5) -> str:
        """Speak a message then gather another speech response."""
        vr = VoiceResponse()
        vr.say(message)
        gather = vr.gather(
            input="speech",
            action=action_url or self.default_action,
            method="POST",
            timeout=timeout,
            speech_timeout="auto",
        )
        gather.say("You can speak after the tone.")
        return str(vr)

    def say_and_hangup(self, message: str) -> str:
        """Speak a message and end the call."""
        vr = VoiceResponse()
        vr.say(message)
        vr.hangup()
        return str(vr)
