"""
Dialogue Manager orchestrates conversation flow across agents.
"""

import os
from typing import Any, Dict, Optional

from src.agents.base_agent import AgentResult, AgentStatus, BaseAgent
from src.utils.conversation_state import ConversationState
from src.utils.response_generator import ResponseGenerator


# Demo mode: Allow authentication to be more lenient for testing/demos
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

INTENT_PATIENT_REQUIRED = {
    "ScheduleAppointment",
    "RescheduleAppointment",
    "CancelAppointment",
    "InfoQuery",
}


class DialogueManager(BaseAgent):
    """Central orchestrator for multi-turn conversations."""

    def __init__(
        self,
        model_client,
        nlu_agent,
        scheduling_agent,
        records_agent,
        knowledge_agent,
        **kwargs,
    ):
        super().__init__(model_client, **kwargs)
        self.nlu_agent = nlu_agent
        self.scheduling_agent = scheduling_agent
        self.records_agent = records_agent
        self.knowledge_agent = knowledge_agent
        # Response generator: used to create natural language slot offers and confirmations
        self.response_generator: ResponseGenerator = kwargs.get(
            "response_generator", ResponseGenerator(self.model)
        )

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Expected input_data:
        {
            "utterance": str,
            "state": ConversationState | dict | None,
            "patient_name": str,
            "dob": str,
            "slot_id": str,
            "appointment_id": str,
            ...
        }
        """
        self._validate_input(input_data)
        utterance = input_data.get("utterance", "")
        state = self._coerce_state(input_data.get("state"))
        state.add_turn("user", utterance)

        # Resume authentication flow before re-classifying intent
        if state.step == "awaiting_auth":
            auth_result = self._authenticate_patient(state, input_data)
            if auth_result is not None:
                if "state" not in auth_result.output:
                    auth_result.output["state"] = state.to_dict()
                return auth_result

        nlu_result = await self.nlu_agent.execute({"utterance": utterance, "context": state.to_dict()})
        intent = nlu_result.output.get("intent", "Other")
        state.set_intent(intent)

        # CHECK REGISTRATION FLOW
        if state.step and state.step.startswith("registration_"):
            reg_result = await self._handle_registration_flow(utterance, state, input_data)
            state.add_turn("assistant", reg_result.output.get("text", ""))
            return AgentResult(
                status=reg_result.status,
                output={**reg_result.output, "state": state.to_dict()},
                metadata=reg_result.metadata,
                errors=reg_result.errors,
                warnings=reg_result.warnings,
            )

        # EXPLICIT REGISTRATION INTENT
        if intent == "RegisterNewPatient":
            state.set_step("registration_collecting_name")
            text = "Welcome! Let's get you registered. What's your full name?"
            result = self._create_success_result({"text": text, "state": state.to_dict()})
            state.add_turn("assistant", text)
            return result

        if intent in INTENT_PATIENT_REQUIRED and not state.patient_id:
            auth_result = self._authenticate_patient(state, input_data)
            if auth_result is not None:
                # Ensure state is in output for consistency with normal flow
                if "state" not in auth_result.output:
                    auth_result.output["state"] = state.to_dict()
                return auth_result

        routed_result = await self._route_intent(intent, utterance, state, input_data)
        state.add_turn("assistant", routed_result.output.get("text", ""))

        return AgentResult(
            status=routed_result.status,
            output={**routed_result.output, "state": state.to_dict()},
            metadata=routed_result.metadata,
            errors=routed_result.errors,
            warnings=routed_result.warnings,
        )

    def _authenticate_patient(self, state: ConversationState, input_data: Dict[str, Any]) -> Optional[AgentResult]:
        """Authenticate patient. In DEMO_MODE, use first patient as fallback for easier testing."""
        import logging
        logger = logging.getLogger(__name__)

        name = input_data.get("patient_name")
        dob = input_data.get("dob")

        # Get partial auth from state if exists
        partial_name = state.slots.get("partial_auth_name") if state.slots else None
        partial_dob = state.slots.get("partial_auth_dob") if state.slots else None

        # Merge current input with partial auth
        if name:
            partial_name = name
        if dob:
            partial_dob = dob

        logger.info(f"Auth attempt: name={self._protect_phi(partial_name)}, dob={self._protect_phi(partial_dob)}")

        # Try to find patient if BOTH credentials provided
        if partial_name and partial_dob:
            patient = self.records_agent.get_patient_by_dob(partial_name, partial_dob)
            if patient:
                patient_id = patient.get("id")
                logger.info(f"Auth SUCCESS: patient_id={patient_id}")
                state.set_patient(patient_id)
                state.set_step(None)
                # Clear partial auth from state
                if state.slots:
                    state.slots.pop("partial_auth_name", None)
                    state.slots.pop("partial_auth_dob", None)
                return None

            # Patient not found - OFFER REGISTRATION
            logger.warning(f"Auth FAILED: No patient found for name={self._protect_phi(partial_name)}, dob={self._protect_phi(partial_dob)}")

            # Store auth data for potential registration
            state.set_registration_field("name", partial_name)
            state.set_registration_field("dob", partial_dob)
            state.set_step("registration_offered")

            # Clear partial auth from slots
            if state.slots:
                state.slots.pop("partial_auth_name", None)
                state.slots.pop("partial_auth_dob", None)

            # Get first name for friendlier message
            first_name = partial_name.split()[0] if partial_name else "there"

            offer_text = (
                f"I don't see a record for {first_name} in our system. "
                f"Would you like to register as a new patient? It'll just take a minute."
            )

            return self._create_failure_result(
                offer_text,
                output={"text": offer_text, "state": state.to_dict()},
                metadata={
                    "auth_failed": True,
                    "registration_offered": True,
                    "phi_hash": self._protect_phi(f"{partial_name}|{partial_dob}"),
                },
            )

        # Partial auth handling: got name but not DOB
        if partial_name and not partial_dob:
            logger.info(f"Partial auth: have name, need DOB")
            # Store partial name in state
            state.update_slots(partial_auth_name=partial_name)
            # Get first name for friendlier response
            first_name = partial_name.split()[0] if partial_name else "there"
            message = (
                f"Thanks, {first_name}. To verify your identity, what's your date of birth? "
                "Please include the month, day, and year."
            )
            state.set_step("awaiting_auth")
            return self._create_failure_result(
                message,
                output={"text": message, "state": state.to_dict()},
                metadata={"auth_prompted": True, "partial_auth": "name_only", "auth_expected": "dob"},
            )

        # Partial auth handling: got DOB but not name (rare but possible)
        if partial_dob and not partial_name:
            logger.info(f"Partial auth: have DOB, need name")
            state.update_slots(partial_auth_dob=partial_dob)
            message = (
                "Thank you. To continue, could you please tell me your full name? "
                "For example: Alicia Thompson."
            )
            state.set_step("awaiting_auth")
            return self._create_failure_result(
                message,
                output={"text": message, "state": state.to_dict()},
                metadata={"auth_prompted": True, "partial_auth": "dob_only", "auth_expected": "name"},
            )

        # No auth info yet: prompt with contextual message based on intent
        # Make message contextual based on user's original request
        intent = state.current_intent or "Other"
        if intent == "InfoQuery":
            action = "access your medical information"
        elif intent in ("ScheduleAppointment", "RescheduleAppointment", "CancelAppointment"):
            action = "help with your appointment"
        else:
            action = "assist you"

        message = (
            f"To {action}, I'll need to verify your identity. What's your full name? "
            "After that I'll ask for your date of birth."
        )
        response_text = message if DEMO_MODE else "Need patient verification to continue."
        state.set_step("awaiting_auth")
        return self._create_failure_result(
            response_text,
            output={"text": response_text, "state": state.to_dict()},
            metadata={"auth_prompted": True, "auth_expected": "name"},
        )

    async def _handle_registration_flow(
        self, utterance: str, state: ConversationState, input_data: Dict[str, Any]
    ) -> AgentResult:
        """Handle multi-turn registration flow."""
        import logging
        from src.utils.validation import validate_name, validate_phone, validate_email

        logger = logging.getLogger(__name__)
        step = state.step

        # STEP: Registration offered, awaiting confirmation
        if step == "registration_offered":
            lower_utterance = utterance.lower()
            if any(word in lower_utterance for word in ["yes", "sure", "okay", "yeah", "yep", "please"]):
                # User accepted registration
                state.set_step("registration_collecting_phone")
                text = "Great! What's your phone number?"
                return self._create_success_result({"text": text, "state": state.to_dict()})
            else:
                # User declined registration
                state.clear_registration_data()
                state.set_step(None)
                text = "No problem. If you'd like to speak with someone, please call 415-555-0100."
                return self._create_success_result({"text": text, "state": state.to_dict()})

        # STEP: Collecting name
        if step == "registration_collecting_name":
            name = input_data.get("patient_name", utterance.strip())
            is_valid, result = validate_name(name)
            if not is_valid:
                return self._create_failure_result(result, output={"text": result, "state": state.to_dict()})

            state.set_registration_field("name", result)
            state.set_step("registration_collecting_dob")
            text = "Thanks. What's your date of birth?"
            return self._create_success_result({"text": text, "state": state.to_dict()})

        # STEP: Collecting DOB
        if step == "registration_collecting_dob":
            dob = input_data.get("dob")
            if not dob:
                # Try to parse from utterance
                try:
                    from dateutil import parser as date_parser
                    parsed = date_parser.parse(utterance, fuzzy=True)
                    dob = parsed.date().isoformat()
                except Exception:
                    text = "I didn't catch that date. Please provide your date of birth."
                    return self._create_failure_result(text, output={"text": text, "state": state.to_dict()})

            # Check duplicate
            name = state.get_registration_field("name")
            if self.records_agent.check_duplicate(name, dob):
                logger.info(f"Duplicate detected during registration")
                # Already exists - authenticate instead
                patient = self.records_agent.get_patient_by_dob(name, dob)
                state.set_patient(patient["id"])
                state.clear_registration_data()
                state.set_step(None)
                text = "You're already registered! How can I help you?"
                return self._create_success_result({"text": text, "state": state.to_dict()})

            state.set_registration_field("dob", dob)
            state.set_step("registration_collecting_phone")
            text = "Perfect. What's your phone number?"
            return self._create_success_result({"text": text, "state": state.to_dict()})

        # STEP: Collecting phone
        if step == "registration_collecting_phone":
            phone = utterance.strip()
            is_valid, result = validate_phone(phone)
            if not is_valid:
                return self._create_failure_result(result, output={"text": result, "state": state.to_dict()})

            state.set_registration_field("phone", result)
            state.set_step("registration_collecting_email")
            text = "Great. What's your email address?"
            return self._create_success_result({"text": text, "state": state.to_dict()})

        # STEP: Collecting email - CREATE PATIENT
        if step == "registration_collecting_email":
            email = utterance.strip()
            is_valid, result = validate_email(email)
            if not is_valid:
                return self._create_failure_result(result, output={"text": result, "state": state.to_dict()})

            # CREATE PATIENT
            try:
                new_patient = self.records_agent.create_patient(
                    name=state.get_registration_field("name"),
                    dob=state.get_registration_field("dob"),
                    phone=state.get_registration_field("phone"),
                    email=result
                )

                patient_id = new_patient["id"]
                first_name = new_patient["name"].split()[0]

                state.set_patient(patient_id)
                state.clear_registration_data()
                state.set_step(None)

                # Check original intent
                if state.current_intent == "ScheduleAppointment":
                    text = f"Perfect, {first_name}! You're registered. Let's schedule your appointment."
                else:
                    text = f"Welcome, {first_name}! You're all registered. How can I help?"

                return self._create_success_result({
                    "text": text,
                    "state": state.to_dict(),
                    "patient_id": patient_id
                })

            except ValueError as e:
                logger.error(f"Registration failed: {e}")
                text = f"Registration error: {e}"
                return self._create_failure_result(text, output={"text": text, "state": state.to_dict()})

        # Unknown step
        logger.error(f"Unknown registration step: {step}")
        state.clear_registration_data()
        state.set_step(None)
        text = "Something went wrong. How can I help you?"
        return self._create_failure_result(text, output={"text": text, "state": state.to_dict()})

    async def _route_intent(
        self,
        intent: str,
        utterance: str,
        state: ConversationState,
        input_data: Dict[str, Any],
    ) -> AgentResult:
        if intent == "FAQ":
            return await self.knowledge_agent.execute({"query": utterance})

        if intent == "InfoQuery":
            # Use the ResponseGenerator to create a friendly explanation for lab results
            labs = self.records_agent.get_lab_results(state.patient_id)
            patient = self.records_agent.get_patient_by_id(state.patient_id)
            patient_name = patient.get("name", "there").split()[0] if patient else "there"

            if not labs:
                text = "No lab results found."
                return self._create_success_result({"text": text, "data": labs})

            # Generate a natural-language explanation using the model (with fallback)
            explanation = await self.response_generator.generate_info_response(
                patient_name=patient_name,
                info_type="lab_results",
                data=labs,
            )

            # Simple heuristic to suggest follow-up if lab interpretation mentions recommendations
            follow_up_suggested = any(
                (lr.get("interpretation") or "").lower().find(k) != -1
                for lr in labs
                for k in ("recommend", "recommendation", "elevated", "above", "above goal", "suggest")
            )

            metadata = {"follow_up_suggested": follow_up_suggested}

            follow_up_prompt = None
            if follow_up_suggested:
                follow_up_prompt = await self.response_generator.generate_proactive_followup(
                    patient_name=patient_name,
                    reason=None,
                )

            output = {"text": explanation, "data": labs}
            if follow_up_prompt:
                output["follow_up_prompt"] = follow_up_prompt

            return self._create_success_result(output, metadata=metadata)

        if intent == "ScheduleAppointment":
            return await self._handle_schedule(state, input_data)

        if intent == "RescheduleAppointment":
            return await self._handle_reschedule(state, input_data)

        if intent == "CancelAppointment":
            return await self._handle_cancel(state, input_data)

        # Default fallback
        return AgentResult(
            status=AgentStatus.PARTIAL,
            output={"text": "I can help with appointments, records, or clinic questions. How can I assist?"},
            warnings=["Unhandled intent"],
            metadata={"intent": intent},
        )

    async def _handle_schedule(self, state: ConversationState, input_data: Dict[str, Any]) -> AgentResult:
        """Handle appointment scheduling with natural responses."""
        patient = self.records_agent.get_patient_by_id(state.patient_id)
        patient_name = patient.get("name", "").split()[0] if patient else "there"

        slot_id = input_data.get("slot_id")
        if slot_id:
            # User selected a slot - book it
            appt = self.scheduling_agent.book_appointment(patient_id=state.patient_id, slot=slot_id)

            # Generate natural confirmation
            confirmation = await self.response_generator.generate_booking_confirmation(
                patient_name=patient_name,
                appointment=appt
            )

            return self._create_success_result(
                {"text": confirmation, "appointment": appt}
            )

        # User wants to schedule - show available slots
        doctor = input_data.get("doctor") or state.slots.get("doctor", "Dr. Maya Singh")
        slots = self.scheduling_agent.find_available_slots(doctor=doctor)

        if not slots:
            no_slots_msg = (
                f"I'm sorry, {patient_name}, but {doctor} doesn't have any available appointments "
                "right now. Would you like me to check with a different provider?"
            )
            return self._create_failure_result(
                no_slots_msg,
                output={"text": no_slots_msg, "state": state.to_dict()},
                metadata={}
            )

        # Generate natural slot offer
        state.update_slots(doctor=doctor)
        slot_offer = await self.response_generator.generate_slot_offer(
            patient_name=patient_name,
            doctor_name=doctor,
            slots=slots
        )

        return self._create_success_result(
            {"text": slot_offer, "options": slots}
        )

    async def _handle_reschedule(self, state: ConversationState, input_data: Dict[str, Any]) -> AgentResult:
        """Handle appointment rescheduling."""
        appointment_id = input_data.get("appointment_id")
        new_slot = input_data.get("new_slot")
        if appointment_id and new_slot:
            appt = self.scheduling_agent.reschedule_appointment(appointment_id=appointment_id, new_slot=new_slot)
            return self._create_success_result({"text": "Your appointment has been rescheduled.", "appointment": appt})

        msg = "To reschedule, I'll need your appointment ID and the new time you'd prefer."
        return self._create_failure_result(
            msg,
            output={"text": msg, "state": state.to_dict()},
            metadata={}
        )

    async def _handle_cancel(self, state: ConversationState, input_data: Dict[str, Any]) -> AgentResult:
        """Handle appointment cancellation with natural responses."""
        patient = self.records_agent.get_patient_by_id(state.patient_id)
        patient_name = patient.get("name", "").split()[0] if patient else "there"

        appointment_id = input_data.get("appointment_id")
        if not appointment_id:
            msg = f"I'd be happy to help cancel your appointment, {patient_name}. Could you tell me which appointment you'd like to cancel?"
            return self._create_failure_result(
                msg,
                output={"text": msg, "state": state.to_dict()},
                metadata={}
            )

        appt = self.scheduling_agent.cancel_appointment(appointment_id)

        # Generate natural cancellation confirmation
        confirmation = await self.response_generator.generate_cancellation_confirmation(
            patient_name=patient_name,
            appointment=appt
        )

        return self._create_success_result({"text": confirmation, "appointment": appt})

    @staticmethod
    def _coerce_state(raw_state: Optional[Any]) -> ConversationState:
        if raw_state is None:
            return ConversationState()
        if isinstance(raw_state, ConversationState):
            return raw_state
        if isinstance(raw_state, dict):
            return ConversationState.from_dict(raw_state)
        return ConversationState()
