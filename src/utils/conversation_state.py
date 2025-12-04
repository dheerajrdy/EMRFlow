"""
Conversation state tracking for multi-turn dialogue.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


MAX_HISTORY = 20


@dataclass
class ConversationState:
    """Tracks dialogue context across turns."""

    current_intent: Optional[str] = None
    patient_id: Optional[str] = None
    slots: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict[str, str]] = field(default_factory=list)
    step: Optional[str] = None
    registration_data: Dict[str, Any] = field(default_factory=dict)

    def add_turn(self, role: str, text: str) -> None:
        """Append a dialogue turn, trimming to max history."""
        self.history.append({"role": role, "text": text})
        if len(self.history) > MAX_HISTORY:
            self.history = self.history[-MAX_HISTORY:]

    def set_intent(self, intent: str) -> None:
        self.current_intent = intent

    def set_patient(self, patient_id: str) -> None:
        self.patient_id = patient_id

    def update_slots(self, **kwargs) -> None:
        self.slots.update({k: v for k, v in kwargs.items() if v is not None})

    def set_step(self, step: Optional[str]) -> None:
        self.step = step

    def get_registration_field(self, field: str) -> Optional[str]:
        """Get registration field value."""
        return self.registration_data.get(field)

    def set_registration_field(self, field: str, value: str) -> None:
        """Set registration field value."""
        self.registration_data[field] = value

    def clear_registration_data(self) -> None:
        """Clear all registration data."""
        self.registration_data = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_intent": self.current_intent,
            "patient_id": self.patient_id,
            "slots": self.slots,
            "history": self.history,
            "step": self.step,
            "registration_data": self.registration_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        return cls(
            current_intent=data.get("current_intent"),
            patient_id=data.get("patient_id"),
            slots=data.get("slots", {}),
            history=data.get("history", []),
            step=data.get("step"),
            registration_data=data.get("registration_data", {}),
        )
