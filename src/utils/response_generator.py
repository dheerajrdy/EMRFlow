"""
Natural response generation using Gemini for conversational voice interactions.

Transforms structured data and context into friendly, natural-sounding responses.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from src.models.model_client import ModelClient


class ResponseGenerator:
    """Generates natural language responses from structured data."""

    def __init__(self, model_client: ModelClient):
        """
        Initialize response generator.

        Args:
            model_client: Model client for LLM-based generation
        """
        self.model = model_client

    async def generate_auth_prompt(self, patient_name: Optional[str] = None) -> str:
        """
        Generate friendly authentication prompt.

        Args:
            patient_name: Partial name if provided

        Returns:
            Natural auth prompt
        """
        if patient_name:
            return (
                f"Thanks {patient_name}! To confirm your identity, "
                "could you please tell me your full name and date of birth? "
                "For example: My name is Alicia Thompson, born April 12, 1985."
            )

        return (
            "To help you with that, I'll need to verify your identity first. "
            "Could you please tell me your name and date of birth? "
            "For example: My name is Alicia Thompson, born April 12, 1985."
        )

    async def generate_greeting(self, patient_name: Optional[str] = None) -> str:
        """
        Generate personalized greeting.

        Args:
            patient_name: Patient name if authenticated

        Returns:
            Natural greeting
        """
        if patient_name:
            return f"Hi {patient_name}! How can I help you today?"
        return "Thanks for calling the clinic. How can I help you today?"

    async def generate_slot_offer(
        self,
        patient_name: str,
        doctor_name: str,
        slots: List[Dict[str, Any]],
        max_slots: int = 3
    ) -> str:
        """
        Generate natural offer of available appointment slots.

        Args:
            patient_name: Patient's first name
            doctor_name: Doctor's name
            slots: List of available slot dicts
            max_slots: Maximum slots to offer verbally

        Returns:
            Natural slot offering
        """
        if not slots:
            return (
                f"I'm sorry, {patient_name}, but {doctor_name} doesn't have any "
                "available appointments in the next few weeks. Would you like me to "
                "check with a different provider or put you on a waitlist?"
            )

        # Format slots naturally
        slot_descriptions = []
        for slot in slots[:max_slots]:
            try:
                dt = datetime.fromisoformat(slot["start"])
                day = dt.strftime("%A, %B %d")
                time = dt.strftime("%I:%M %p").lstrip("0")
                slot_descriptions.append(f"{day} at {time}")
            except (KeyError, ValueError):
                # Fallback for malformed slot data
                slot_descriptions.append(f"slot {slot.get('slot_id', 'unknown')}")

        prompt = (
            f"Generate a friendly, natural response offering appointment slots to a patient. "
            f"Context:\n"
            f"- Patient name: {patient_name}\n"
            f"- Doctor: {doctor_name}\n"
            f"- Available times: {', '.join(slot_descriptions)}\n\n"
            f"Generate a warm, conversational response that:\n"
            f"1. Acknowledges the request\n"
            f"2. Presents the options clearly\n"
            f"3. Asks which time works best\n"
            f"4. Keeps it concise (2-3 sentences max)\n\n"
            f"Response:"
        )

        try:
            response = await self.model.generate(
                prompt=prompt,
                system_prompt="You are a friendly clinic receptionist having a phone conversation.",
                temperature=0.7,
                max_tokens=150
            )
            return response.content.strip()
        except Exception:
            # Fallback to template-based response
            if len(slot_descriptions) == 1:
                slots_text = slot_descriptions[0]
            elif len(slot_descriptions) == 2:
                slots_text = f"{slot_descriptions[0]} or {slot_descriptions[1]}"
            else:
                slots_text = ", ".join(slot_descriptions[:-1]) + f", or {slot_descriptions[-1]}"

            return (
                f"Great, {patient_name}! I have some available appointments with {doctor_name}. "
                f"I can offer you {slots_text}. Which one works best for you?"
            )

    async def generate_booking_confirmation(
        self,
        patient_name: str,
        appointment: Dict[str, Any]
    ) -> str:
        """
        Generate natural booking confirmation.

        Args:
            patient_name: Patient's first name
            appointment: Appointment details

        Returns:
            Natural confirmation message
        """
        try:
            dt = datetime.fromisoformat(appointment["datetime"])
            day = dt.strftime("%A, %B %d")
            time = dt.strftime("%I:%M %p").lstrip("0")
            doctor = appointment.get("doctor", "the doctor")
            location = appointment.get("location", "the clinic")

            prompt = (
                f"Generate a friendly appointment confirmation message. "
                f"Context:\n"
                f"- Patient name: {patient_name}\n"
                f"- Doctor: {doctor}\n"
                f"- Date/time: {day} at {time}\n"
                f"- Location: {location}\n\n"
                f"Generate a warm confirmation that:\n"
                f"1. Confirms the booking\n"
                f"2. Includes all key details\n"
                f"3. Mentions they'll get a reminder\n"
                f"4. Asks if they need anything else\n"
                f"5. Keeps it friendly and concise (2-3 sentences)\n\n"
                f"Response:"
            )

            response = await self.model.generate(
                prompt=prompt,
                system_prompt="You are a helpful clinic receptionist confirming an appointment.",
                temperature=0.7,
                max_tokens=150
            )
            return response.content.strip()
        except Exception:
            # Fallback to template
            return (
                f"Perfect! I've booked your appointment with {appointment.get('doctor', 'the doctor')} "
                f"for {day} at {time}. You'll receive a reminder the day before. "
                f"Is there anything else I can help you with?"
            )

    async def generate_cancellation_confirmation(
        self,
        patient_name: str,
        appointment: Dict[str, Any]
    ) -> str:
        """
        Generate natural cancellation confirmation.

        Args:
            patient_name: Patient's first name
            appointment: Cancelled appointment details

        Returns:
            Natural cancellation message
        """
        try:
            dt = datetime.fromisoformat(appointment["datetime"])
            day = dt.strftime("%A, %B %d")
            time = dt.strftime("%I:%M %p").lstrip("0")

            return (
                f"I've cancelled your appointment for {day} at {time}. "
                f"If you need to reschedule, just give us a call anytime. "
                f"Is there anything else I can help you with today, {patient_name}?"
            )
        except Exception:
            return (
                f"I've cancelled your appointment, {patient_name}. "
                f"Feel free to call us if you'd like to reschedule. "
                f"Is there anything else I can help you with?"
            )

    async def generate_info_response(
        self,
        patient_name: str,
        info_type: str,
        data: Any
    ) -> str:
        """
        Generate natural response for information queries.

        Args:
            patient_name: Patient's first name
            info_type: Type of info (lab_results, medications, appointments)
            data: The actual data to present

        Returns:
            Natural info response
        """
        prompt = (
            f"Generate a friendly, clear response to a patient asking about their {info_type}. "
            f"Context:\n"
            f"- Patient name: {patient_name}\n"
            f"- Info type: {info_type}\n"
            f"- Data: {data}\n\n"
            f"Generate a response that:\n"
            f"1. Presents the information clearly\n"
            f"2. Explains any medical terms simply\n"
            f"3. Offers to schedule follow-up if relevant\n"
            f"4. Stays warm and professional\n"
            f"5. Keeps it concise (3-4 sentences max)\n\n"
            f"Response:"
        )

        try:
            response = await self.model.generate(
                prompt=prompt,
                system_prompt="You are a knowledgeable clinic receptionist explaining medical information.",
                temperature=0.7,
                max_tokens=200
            )
            return response.content.strip()
        except Exception:
            # Fallback
            return f"Here's the information you requested, {patient_name}: {data}"

    async def generate_fallback(self, patient_name: Optional[str] = None) -> str:
        """
        Generate friendly fallback for unclear input.

        Args:
            patient_name: Patient name if known

        Returns:
            Natural fallback message
        """
        name_part = f", {patient_name}" if patient_name else ""
        return (
            f"I'm sorry{name_part}, I didn't quite catch that. "
            f"Could you please repeat what you need help with?"
        )

    async def generate_goodbye(self, patient_name: Optional[str] = None) -> str:
        """
        Generate friendly goodbye message.

        Args:
            patient_name: Patient name if known

        Returns:
            Natural goodbye
        """
        name_part = f" {patient_name}" if patient_name else ""
        return (
            f"Thanks for calling{name_part}! "
            f"If you need anything else, don't hesitate to call us back. Take care!"
        )

    async def generate_proactive_followup(self, patient_name: str, reason: Optional[str] = None) -> str:
        """
        Generate a short follow-up suggestion prompt.

        Args:
            patient_name: Patient's first name
            reason: Optional short reason for follow-up

        Returns:
            Natural follow-up suggestion
        """
        if reason:
            return (
                f"{patient_name}, based on these results I recommend a follow-up visit to discuss {reason}. "
                "Would you like me to schedule that for you?"
            )

        return (
            f"{patient_name}, I can schedule a follow-up appointment to discuss these results if you'd like. "
            "Would you like me to check availability now?"
        )
