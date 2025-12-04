"""
Patient Records Agent.

Provides helper methods to retrieve data from the mock patient dataset
and basic identity verification by name and date of birth.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.utils.data_loader import DataLoader


class RecordsAgent(BaseAgent):
    """Agent for querying mock EHR records."""

    def __init__(
        self,
        model_client,
        data_loader: Optional[DataLoader] = None,
        patients: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(model_client, **kwargs)
        self.data_loader = data_loader or DataLoader()
        self.patients = patients if patients is not None else self.data_loader.load_patients()

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Dispatch utility for agent actions.

        Expected input_data: {"action": ..., **kwargs}
        """
        self._validate_input(input_data)
        action = input_data.get("action")

        try:
            if action == "get_patient_by_dob":
                patient = self.get_patient_by_dob(input_data["name"], input_data["dob"])
                if patient:
                    return self._create_success_result({"patient": patient})
                return self._create_failure_result(
                    "Patient not found",
                    metadata={"request": self._protect_phi(f"{input_data.get('name')}|{input_data.get('dob')}")}
                )

            if action == "get_upcoming_appointments":
                appointments = self.get_upcoming_appointments(input_data["patient_id"])
                return self._create_success_result({"appointments": appointments})

            if action == "get_lab_results":
                labs = self.get_lab_results(input_data["patient_id"])
                return self._create_success_result({"lab_results": labs})

            if action == "get_medications":
                meds = self.get_medications(input_data["patient_id"])
                return self._create_success_result({"medications": meds})

            if action == "get_visit_notes":
                notes = self.get_visit_notes(input_data["patient_id"])
                return self._create_success_result({"visit_notes": notes})

            if action == "create_patient":
                patient = self.create_patient(
                    name=input_data["name"],
                    dob=input_data["dob"],
                    phone=input_data["phone"],
                    email=input_data["email"]
                )
                return self._create_success_result({"patient": patient})

            return self._create_failure_result(
                f"Unknown action: {action}",
                metadata={"request": self._protect_phi(str(action))}
            )
        except Exception as exc:  # pragma: no cover - defensive
            return self._create_failure_result(
                "Error during records lookup",
                output={},
                metadata={"error": str(exc)}
            )

    def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Get patient by ID."""
        for patient in self.patients:
            if patient.get("id") == patient_id:
                return patient
        return None

    def get_patient_by_dob(self, name: str, dob: str) -> Optional[Dict[str, Any]]:
        """Authenticate and return patient by name and date of birth."""
        import logging
        logger = logging.getLogger(__name__)

        normalized_name = self._normalize_name(name)
        dob_str = self._normalize_date(dob)

        logger.debug(f"Looking up patient: normalized_name='{normalized_name}', normalized_dob='{dob_str}'")

        for patient in self.patients:
            patient_norm_name = self._normalize_name(patient.get("name"))
            patient_norm_dob = self._normalize_date(patient.get("dob"))

            logger.debug(f"Comparing with patient: name='{patient_norm_name}', dob='{patient_norm_dob}'")

            if patient_norm_name == normalized_name and patient_norm_dob == dob_str:
                logger.info(f"Patient found: {patient.get('id')}")
                return patient

        logger.warning(f"No patient match found for name='{normalized_name}', dob='{dob_str}'")
        return None

    def get_upcoming_appointments(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return future appointments for the patient."""
        patient = self._require_patient(patient_id)
        now = datetime.utcnow()

        upcoming = []
        for appt in patient.get("appointments", []):
            appt_time = self._parse_datetime(appt.get("datetime"))
            if appt_time and appt_time >= now and appt.get("status") != "canceled":
                upcoming.append(appt)
        return sorted(upcoming, key=lambda a: a.get("datetime", ""))

    def get_lab_results(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return lab results for the patient."""
        patient = self._require_patient(patient_id)
        return patient.get("lab_results", [])

    def get_medications(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return medication list for the patient."""
        patient = self._require_patient(patient_id)
        return patient.get("medications", [])

    def get_visit_notes(self, patient_id: str) -> List[Dict[str, Any]]:
        """Return visit notes for the patient."""
        patient = self._require_patient(patient_id)
        return patient.get("visit_notes", [])

    def _require_patient(self, patient_id: str) -> Dict[str, Any]:
        for patient in self.patients:
            if patient.get("id") == patient_id:
                return patient
        masked = self._protect_phi(patient_id)
        raise ValueError(f"Patient not found: {masked}")

    def create_patient(self, name: str, dob: str, phone: str, email: str) -> Dict[str, Any]:
        """
        Create new patient record.

        Args:
            name: Full patient name
            dob: Date of birth (ISO format)
            phone: Phone number
            email: Email address

        Returns:
            New patient dictionary

        Raises:
            ValueError: If validation fails or duplicate detected
        """
        import logging
        from src.utils.validation import validate_name, validate_phone, validate_email

        logger = logging.getLogger(__name__)

        # Validate inputs
        name_valid, name_msg = validate_name(name)
        if not name_valid:
            raise ValueError(name_msg)

        phone_valid, phone_norm = validate_phone(phone)
        if not phone_valid:
            raise ValueError(phone_norm)

        email_valid, email_norm = validate_email(email)
        if not email_valid:
            raise ValueError(email_norm)

        # Check for duplicate
        if self.check_duplicate(name, dob):
            logger.warning(f"Duplicate registration attempt: {self._protect_phi(name)}")
            raise ValueError("Patient already exists")

        # Generate new patient ID
        patient_id = self._generate_patient_id()

        # Create patient record
        new_patient = {
            "id": patient_id,
            "name": name.strip(),
            "dob": dob,
            "contact": {
                "phone": phone_norm,
                "email": email_norm
            },
            "appointments": [],
            "medications": [],
            "lab_results": [],
            "visit_notes": []
        }

        # Add to in-memory list
        self.patients.append(new_patient)

        # Persist to file
        self.data_loader.save_patients(self.patients)

        logger.info(f"Created new patient: {patient_id}")
        return new_patient

    def check_duplicate(self, name: str, dob: str) -> bool:
        """
        Check if patient with same name and DOB already exists.

        Args:
            name: Patient name
            dob: Date of birth (ISO format)

        Returns:
            True if duplicate found, False otherwise
        """
        normalized_name = self._normalize_name(name)
        normalized_dob = self._normalize_date(dob)

        for patient in self.patients:
            if (self._normalize_name(patient.get("name")) == normalized_name and
                self._normalize_date(patient.get("dob")) == normalized_dob):
                return True
        return False

    def _generate_patient_id(self) -> str:
        """
        Generate next sequential patient ID.

        Returns:
            Patient ID in format P-XXXX (e.g., P-1005)
        """
        max_id = 1000  # Start from P-1001
        for patient in self.patients:
            patient_id = patient.get("id", "")
            if patient_id.startswith("P-"):
                try:
                    num = int(patient_id.split("-")[1])
                    max_id = max(max_id, num)
                except (IndexError, ValueError):
                    pass
        return f"P-{max_id + 1}"

    @staticmethod
    def _normalize_name(name: Optional[str]) -> str:
        return (name or "").strip().lower()

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @staticmethod
    def _normalize_date(value: Optional[str]) -> str:
        if not value:
            return ""
        try:
            return datetime.fromisoformat(value).date().isoformat()
        except ValueError:
            return value
