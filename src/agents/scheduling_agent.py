"""
Scheduling Agent.

Manages appointment availability, booking, rescheduling, and cancellation
using the mock schedule dataset.
"""

import uuid
from datetime import datetime, date, time
from typing import Any, Dict, List, Optional, Tuple, Union

from src.agents.base_agent import AgentResult, BaseAgent
from src.utils.data_loader import DataLoader


class SchedulingAgent(BaseAgent):
    """Agent for managing the clinic schedule and appointments."""

    def __init__(
        self,
        model_client,
        data_loader: Optional[DataLoader] = None,
        schedule: Optional[Dict[str, Any]] = None,
        patients: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(model_client, **kwargs)
        self.data_loader = data_loader or DataLoader()
        self.schedule = schedule if schedule is not None else self.data_loader.load_schedule()
        self.patients = patients if patients is not None else self.data_loader.load_patients()

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Dispatch scheduling operations.

        Expected input_data: {"action": ..., **kwargs}
        """
        self._validate_input(input_data)
        action = input_data.get("action")

        try:
            if action == "find_available_slots":
                slots = self.find_available_slots(
                    doctor=input_data["doctor"],
                    date_range=input_data.get("date_range")
                )
                return self._create_success_result({"slots": slots})

            if action == "book_appointment":
                appt = self.book_appointment(
                    patient_id=input_data["patient_id"],
                    slot=input_data["slot"]
                )
                return self._create_success_result({"appointment": appt})

            if action == "reschedule_appointment":
                appt = self.reschedule_appointment(
                    appointment_id=input_data["appointment_id"],
                    new_slot=input_data["new_slot"]
                )
                return self._create_success_result({"appointment": appt})

            if action == "cancel_appointment":
                appt = self.cancel_appointment(input_data["appointment_id"])
                return self._create_success_result({"appointment": appt})

            return self._create_failure_result(
                f"Unknown action: {action}",
                metadata={"request": str(action)}
            )
        except Exception as exc:  # pragma: no cover - defensive
            return self._create_failure_result(
                "Error during scheduling operation",
                metadata={"error": str(exc)}
            )

    def find_available_slots(
        self,
        doctor: Union[str, Dict[str, Any]],
        date_range: Optional[Tuple[Union[str, datetime], Union[str, datetime]]] = None
    ) -> List[Dict[str, Any]]:
        """Return available slots for a doctor within an optional date range."""
        doctor_entry = self._find_doctor(doctor)
        start_dt, end_dt = self._normalize_date_range(date_range)
        available: List[Dict[str, Any]] = []

        for slot in doctor_entry.get("availability", []):
            if slot.get("status") != "available":
                continue

            slot_start = self._parse_datetime(slot.get("start"))
            if start_dt and slot_start < start_dt:
                continue
            if end_dt and slot_start > end_dt:
                continue

            merged = {**slot, "doctor": doctor_entry.get("name"), "doctor_id": doctor_entry.get("id")}
            available.append(merged)

        return sorted(available, key=lambda s: s.get("start", ""))

    def book_appointment(
        self,
        patient_id: str,
        slot: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Book an available slot for a patient."""
        patient = self._require_patient(patient_id)
        doctor_entry, slot_ref = self._find_slot(slot)

        if slot_ref.get("status") == "booked":
            raise ValueError("Slot already booked")

        appointment_id = slot_ref.get("appointment_id") or f"A-{uuid.uuid4().hex[:8]}"
        slot_ref["status"] = "booked"
        slot_ref["patient_id"] = patient_id
        slot_ref["appointment_id"] = appointment_id

        appointment = {
            "appointment_id": appointment_id,
            "slot_id": slot_ref.get("slot_id"),
            "doctor_id": doctor_entry.get("id"),
            "doctor": doctor_entry.get("name"),
            "type": slot.get("type") if isinstance(slot, dict) else None,
            "datetime": slot_ref.get("start"),
            "location": slot_ref.get("location"),
            "status": "scheduled",
            "reason": slot.get("reason") if isinstance(slot, dict) else None
        }
        patient.setdefault("appointments", []).append(appointment)
        return appointment

    def reschedule_appointment(
        self,
        appointment_id: str,
        new_slot: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Move an existing appointment to a new available slot."""
        patient, appointment = self._find_patient_appointment(appointment_id)
        old_slot = self._find_slot_by_id(appointment.get("slot_id"))
        new_doctor, new_slot_ref = self._find_slot(new_slot)

        if new_slot_ref.get("status") == "booked":
            raise ValueError("Requested slot is already booked")

        if old_slot:
            old_slot["status"] = "available"
            old_slot.pop("patient_id", None)
            old_slot.pop("appointment_id", None)

        appointment["slot_id"] = new_slot_ref.get("slot_id")
        appointment["doctor_id"] = new_doctor.get("id")
        appointment["doctor"] = new_doctor.get("name")
        appointment["datetime"] = new_slot_ref.get("start")
        appointment["location"] = new_slot_ref.get("location")
        appointment["status"] = "scheduled"

        new_slot_ref["status"] = "booked"
        new_slot_ref["patient_id"] = patient.get("id")
        new_slot_ref["appointment_id"] = appointment_id

        return appointment

    def cancel_appointment(self, appointment_id: str) -> Dict[str, Any]:
        """Cancel an appointment and free the slot."""
        patient, appointment = self._find_patient_appointment(appointment_id)
        slot = self._find_slot_by_id(appointment.get("slot_id"))

        if slot:
            slot["status"] = "available"
            slot.pop("patient_id", None)
            slot.pop("appointment_id", None)

        appointment["status"] = "canceled"
        return appointment

    def _find_doctor(self, doctor_ref: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
        doctor_id = doctor_ref
        doctor_name = doctor_ref
        if isinstance(doctor_ref, dict):
            doctor_id = doctor_ref.get("id")
            doctor_name = doctor_ref.get("name")

        for doctor in self.schedule.get("doctors", []):
            if (doctor_id and doctor.get("id") == doctor_id) or (doctor_name and doctor.get("name") == doctor_name):
                return doctor
        raise ValueError(f"Doctor not found: {doctor_ref}")

    def _find_slot(self, slot_ref: Union[str, Dict[str, Any]]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        slot_id = slot_ref.get("slot_id") if isinstance(slot_ref, dict) else slot_ref

        for doctor in self.schedule.get("doctors", []):
            for slot in doctor.get("availability", []):
                if slot.get("slot_id") == slot_id:
                    return doctor, slot
        raise ValueError(f"Slot not found: {self._protect_phi(str(slot_ref))}")

    def _find_slot_by_id(self, slot_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not slot_id:
            return None
        for doctor in self.schedule.get("doctors", []):
            for slot in doctor.get("availability", []):
                if slot.get("slot_id") == slot_id:
                    return slot
        return None

    def _find_patient_appointment(self, appointment_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        for patient in self.patients:
            for appt in patient.get("appointments", []):
                if appt.get("appointment_id") == appointment_id:
                    return patient, appt
        raise ValueError(f"Appointment not found: {self._protect_phi(appointment_id)}")

    def _require_patient(self, patient_id: str) -> Dict[str, Any]:
        for patient in self.patients:
            if patient.get("id") == patient_id:
                return patient
        raise ValueError(f"Patient not found: {self._protect_phi(patient_id)}")

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        return datetime.fromisoformat(value) if value else None

    @staticmethod
    def _normalize_date_range(date_range: Optional[Tuple[Union[str, datetime], Union[str, datetime]]]) -> Tuple[Optional[datetime], Optional[datetime]]:
        if not date_range:
            return None, None

        start_raw, end_raw = date_range
        start_dt = SchedulingAgent._coerce_to_datetime(start_raw, is_start=True)
        end_dt = SchedulingAgent._coerce_to_datetime(end_raw, is_start=False)
        return start_dt, end_dt

    @staticmethod
    def _coerce_to_datetime(value: Union[str, datetime, date], is_start: bool) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, date):
            return datetime.combine(value, time.min if is_start else time.max)
        return datetime.fromisoformat(value)
