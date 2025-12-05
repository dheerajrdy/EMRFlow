"""
Natural Language Understanding Agent for intent classification and entity extraction.

Uses Gemini via ModelClient for structured parsing, with a simple keyword
fallback to keep behavior predictable in tests/offline scenarios.
"""

from typing import Any, Dict, List, Optional

from src.agents.base_agent import AgentResult, BaseAgent

INTENTS = [
    "ScheduleAppointment",
    "RescheduleAppointment",
    "CancelAppointment",
    "InfoQuery",
    "FAQ",
    "RegisterNewPatient",
    "Other",
]


class NLUAgent(BaseAgent):
    """Agent to classify intents and extract structured entities."""

    def __init__(self, model_client, **kwargs):
        super().__init__(model_client, **kwargs)
        self.schema = {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": INTENTS},
                "entities": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "time": {"type": "string"},
                        "doctor": {"type": "string"},
                        "test_type": {"type": "string"},
                        "patient_name": {"type": "string"},
                    },
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "required": ["intent"],
        }

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Expected input_data: {"utterance": "...", "context": {...}}
        """
        self._validate_input(input_data)
        utterance = input_data.get("utterance", "")
        context = input_data.get("context", {})

        try:
            structured = await self._analyze_with_model(utterance, context)
        except Exception:
            structured = self._fallback_rules(utterance)

        confidence = structured.get("confidence")
        if confidence is None:
            confidence = self._estimate_confidence(structured.get("intent"), utterance)

        return self._create_success_result(
            {
                "intent": structured.get("intent", "Other"),
                "entities": structured.get("entities", {}),
                "raw": structured,
                "confidence": confidence,
            }
        )

    async def _analyze_with_model(self, utterance: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        system_prompt = (
            "You are an NLU classifier for a healthcare clinic voice assistant. "
            "Classify the user's intent and extract relevant entities.\n\n"
            f"Valid intents: {', '.join(INTENTS)}\n\n"
            "Intent definitions:\n"
            "- FAQ: General clinic questions (hours, location, services) - NO patient data\n"
            "- InfoQuery: Patient-specific medical info (lab results, medications, records)\n"
            "- ScheduleAppointment: Book new appointment\n"
            "- RescheduleAppointment: Change existing appointment\n"
            "- CancelAppointment: Cancel existing appointment\n"
            "- RegisterNewPatient: New patient signup\n"
            "- Other: Greetings, unclear, or out-of-scope\n\n"
            "Entity extraction:\n"
            "- patient_name: Full name (e.g., 'John Smith', 'Alicia Thompson')\n"
            "- date: Any date mentioned (normalize to YYYY-MM-DD if possible)\n"
            "- time: Appointment time (e.g., '2:00 PM', '14:00')\n"
            "- doctor: Doctor name (e.g., 'Dr. Singh', 'Dr. Maya Singh')\n"
            "- test_type: Medical test (e.g., 'lab results', 'blood work')\n\n"
            "Examples:\n"
            "User: 'What are your clinic hours?'\n"
            "-> {\"intent\": \"FAQ\", \"entities\": {}}\n\n"
            "User: 'I need to check my lab results'\n"
            "-> {\"intent\": \"InfoQuery\", \"entities\": {\"test_type\": \"lab results\"}}\n\n"
            "User: 'Book appointment with Dr. Singh on April 15th'\n"
            "-> {\"intent\": \"ScheduleAppointment\", \"entities\": {\"doctor\": \"Dr. Singh\", \"date\": \"2025-04-15\"}}\n\n"
            "User: 'My name is John Smith, born April 12, 1985'\n"
            "-> {\"intent\": \"Other\", \"entities\": {\"patient_name\": \"John Smith\", \"date\": \"1985-04-12\"}}\n\n"
            "Return ONLY valid JSON matching the schema."
        )
        prompt = f"User utterance: {utterance}\nContext: {context or {}}"
        return await self.model.generate_structured(
            prompt=prompt,
            schema=self.schema,
            system_prompt=system_prompt,
        )

    @staticmethod
    def _fallback_rules(utterance: str) -> Dict[str, Any]:
        """Keyword-based fallback when model is unavailable. More specific checks first."""
        lower = utterance.lower()
        # Check for registration intent FIRST (most specific)
        if any(word in lower for word in ["new patient", "register", "sign up", "first time"]):
            return {"intent": "RegisterNewPatient", "entities": {}, "confidence": 0.8}
        # Check more specific intents before general "appointment"
        if "cancel" in lower:
            return {"intent": "CancelAppointment", "entities": {}, "confidence": 0.85}
        if "reschedule" in lower or "move" in lower:
            return {"intent": "RescheduleAppointment", "entities": {}, "confidence": 0.8}
        if any(word in lower for word in ["book", "schedule", "appointment"]):
            return {"intent": "ScheduleAppointment", "entities": {}, "confidence": 0.8}
        if any(word in lower for word in ["lab", "result", "medication", "test"]):
            return {"intent": "InfoQuery", "entities": {}, "confidence": 0.75}
        if any(word in lower for word in ["hours", "location", "insurance", "faq"]):
            return {"intent": "FAQ", "entities": {}, "confidence": 0.7}
        return {"intent": "Other", "entities": {}, "confidence": 0.4}

    @staticmethod
    def _estimate_confidence(intent: Optional[str], utterance: str) -> float:
        """Lightweight heuristic confidence when model does not supply one."""
        if not utterance or not utterance.strip():
            return 0.2
        if intent in ("Other", None):
            return 0.5
        # Simple heuristic: longer, specific utterances yield higher confidence
        word_count = len(utterance.split())
        if word_count > 10:
            return 0.8
        if word_count > 5:
            return 0.7
        return 0.6
