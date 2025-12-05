"""
Minimal Flask voice server for Twilio integration.

Routes:
- /voice: entry point for incoming calls, sends greeting and starts gather
- /voice/handle: handles speech input and routes through the Dialogue Manager
"""

import asyncio
import logging
import os
import re
import time
from typing import Any, Dict, Optional, Tuple
import importlib.metadata as importlib_metadata
from pathlib import Path
try:
    from dateutil import parser as date_parser
except Exception:  # pragma: no cover - optional dependency
    date_parser = None
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv()

# Some environments (e.g., older Python) lack packages_distributions; patch to avoid twilio import errors.
if not hasattr(importlib_metadata, "packages_distributions"):  # pragma: no cover - env-specific shim
    def packages_distributions(path=None):
        return {}
    importlib_metadata.packages_distributions = packages_distributions  # type: ignore

from flask import Flask, Response, request, url_for

from src.agents.dialogue_manager import DialogueManager
from src.agents.knowledge_agent import KnowledgeAgent
from src.agents.nlu_agent import NLUAgent
from src.agents.records_agent import RecordsAgent
from src.agents.scheduling_agent import SchedulingAgent
from src.agents.base_agent import AgentStatus
from src.integrations.twilio_client import TwilioVoiceClient
from src.models.model_client import GoogleModelClient, ModelClient, ModelResponse
from src.utils.conversation_state import ConversationState
from src.storage.conversation_logger import get_conversation_logger

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
call_state: Dict[str, ConversationState] = {}
call_metadata: Dict[str, Dict[str, Any]] = {}  # Track call start times and turn counts
voice_client = None
dialogue_manager = None
conversation_logger = get_conversation_logger()


class MockModelClient(ModelClient):
    """Fallback model client if Gemini is not configured."""

    async def generate(self, prompt, system_prompt=None, temperature=None, max_tokens=None, **kwargs):
        return ModelResponse(content="ok", model="mock")

    async def generate_structured(self, prompt, schema, system_prompt=None, **kwargs):
        return {"intent": "Other", "entities": {}}


def build_dialogue_manager():
    """Construct DialogueManager with real Gemini if available, else mock."""
    model_client = None
    config = _load_config()
    conf_cfg = (config.get("confidence_scoring") or {})
    recovery_cfg = (config.get("error_recovery") or {})
    try:
        model_client = GoogleModelClient()
        logger.info("Successfully initialized GoogleModelClient with Gemini API")
    except Exception:  # pragma: no cover - defensive
        logger.exception("Falling back to MockModelClient due to error")
        model_client = MockModelClient()

    nlu = NLUAgent(model_client=model_client)
    records = RecordsAgent(model_client=model_client)
    scheduling = SchedulingAgent(model_client=model_client)
    knowledge = KnowledgeAgent(model_client=model_client)
    return DialogueManager(
        model_client=model_client,
        nlu_agent=nlu,
        scheduling_agent=scheduling,
        records_agent=records,
        knowledge_agent=knowledge,
        enable_confidence_scoring=conf_cfg.get("enabled", True),
        confidence_threshold=conf_cfg.get("threshold", 0.7),
        add_confidence_disclaimer=conf_cfg.get("add_disclaimer", True),
        enable_error_recovery=recovery_cfg.get("enabled", True),
        low_confidence_threshold=recovery_cfg.get("low_confidence_threshold", 0.6),
        max_retry_attempts=recovery_cfg.get("max_retries", 2),
        escalation_phone=recovery_cfg.get("escalation_phone", "(555) 0100"),
    )


def build_voice_client():
    default_action = os.getenv("VOICE_DEFAULT_ACTION", "/voice/handle")
    return TwilioVoiceClient(default_action=default_action)


def _manual_date_parse(date_str: str) -> str:
    """Manual date parser for common formats when dateutil fails."""
    # Try ISO format first
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    # Try MM/DD/YYYY or M/D/YYYY
    m = re.match(r"(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})", date_str)
    if m:
        month, day, year = m.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    # Try "Month Day, Year" format (e.g., "April 12, 1985")
    months = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }
    for month_name, month_num in months.items():
        pattern = rf"{month_name}\s+(\d{{1,2}}),?\s+(\d{{4}})"
        m = re.search(pattern, date_str, re.IGNORECASE)
        if m:
            day, year = m.groups()
            return f"{year}-{month_num:02d}-{int(day):02d}"

    # If all else fails, return original string
    return date_str


def _normalize_date(date_str: Optional[str]) -> Optional[str]:
    """Normalize various date inputs to ISO YYYY-MM-DD where possible."""
    if not date_str:
        return None

    if date_parser:
        try:
            dt = date_parser.parse(date_str)
            return dt.date().isoformat()
        except Exception as e:  # pragma: no cover - defensive
            logger.warning(f"dateutil parse failed: {e}, trying manual parsing")

    return _manual_date_parse(date_str)


def _extract_name_dob_regex(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Lightweight regex-based extraction of name and DOB."""
    logger.info(f"Extracting name/DOB from: '{text}'")
    name = None
    dob = None

    # Pattern 1: My name is <name>, born <date>
    m = re.search(r"my name is\s+([A-Za-z\-\' ]+),?\s+born\s+(.+)", text, re.IGNORECASE)
    if m:
        name = m.group(1).strip()
        dob = _normalize_date(m.group(2).strip())
        return name, dob

    # Pattern 2: look for 'born <date>' or 'I was born <date>' and extract name separately
    m2 = re.search(r"(?:I was )?born\s+(.+?)(?:\.|$)", text, re.IGNORECASE)
    if m2:
        dob = _normalize_date(m2.group(1).strip())

    m3 = re.search(r"name is\s+([A-Za-z\-\' ]+?)(?:\.|,|$)", text, re.IGNORECASE)
    if m3:
        name = m3.group(1).strip()

    # Pattern 3: Direct format without keywords - "Alicia Thompson April 12, 1985"
    if not (name and dob):
        date_start = re.search(
            r"\b(january|february|march|april|may|june|july|august|september|october|november|december|\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}|\d{4})",
            text,
            re.IGNORECASE,
        )
        if date_start:
            candidate_name = text[: date_start.start()].strip()
            date_part = text[date_start.start() :].strip()

            # Only accept if name has at least 2 words (first + last name)
            if len(candidate_name.split()) >= 2:
                name = candidate_name
                dob = _normalize_date(date_part)

    logger.info(f"Extracted via regex: name='{name}', dob='{dob}'")
    return name, dob


def _run_async(coro):
    """Run an async coroutine, reusing existing loop if needed."""
    try:
        return asyncio.run(coro)
    except RuntimeError:
        return asyncio.get_event_loop().run_until_complete(coro)


def _extract_name_dob_with_nlu(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Fallback extraction using the model for flexible parsing."""
    global dialogue_manager
    if not text or not text.strip():
        return None, None

    if dialogue_manager is None:
        return None, None

    model_client = getattr(dialogue_manager, "model", None)
    if model_client is None:
        return None, None

    schema = {
        "type": "object",
        "properties": {
            "patient_name": {"type": "string"},
            "dob": {"type": "string"},
        },
    }
    system_prompt = (
        "Extract patient_name and dob (date of birth) from the caller's sentence. "
        "Return dob in YYYY-MM-DD if possible. Use 'patient_name' as the key for the name."
    )
    prompt = f'Caller said: "{text}"'

    try:
        structured = _run_async(
            model_client.generate_structured(
                prompt=prompt,
                schema=schema,
                system_prompt=system_prompt,
            )
        )
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"LLM extraction failed: {e}")
        return None, None

    name = structured.get("patient_name") or structured.get("name")
    dob = _normalize_date(structured.get("dob") or structured.get("date_of_birth"))

    logger.info(f"Extracted via NLU: name='{name}', dob='{dob}'")
    return name, dob


def _load_config() -> Dict[str, Any]:
    """Load YAML config if present."""
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        return {}
    try:
        with open(config_path) as f:
            return yaml.safe_load(f) or {}
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to load config.yaml: %s", exc)
        return {}


def _extract_name_and_dob(text: str) -> Tuple[Optional[str], Optional[str]]:
    """Try regex extraction first, then fall back to LLM-based parsing."""
    name, dob = _extract_name_dob_regex(text)

    # If either field is missing, try to backfill with NLU
    if not name or not dob:
        nlu_name, nlu_dob = _extract_name_dob_with_nlu(text)
        name = name or nlu_name
        dob = dob or nlu_dob

    return name, dob


def _get_action_url(endpoint_name: str) -> str:
    """Build absolute URL for Twilio callbacks."""
    try:
        return url_for(endpoint_name, _external=True)
    except RuntimeError:
        # In case app context is missing
        return f"/{endpoint_name.replace('_', '/')}"


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}


@app.route("/voice", methods=["GET", "POST"])
def voice():
    global dialogue_manager, voice_client, conversation_logger
    if dialogue_manager is None:
        dialogue_manager = build_dialogue_manager()
    if voice_client is None:
        voice_client = build_voice_client()

    call_sid = request.values.get("CallSid")
    caller_number = request.values.get("From")

    # Initialize call state
    call_state[call_sid] = ConversationState()
    call_metadata[call_sid] = {
        "start_time": time.time(),
        "turn_count": 0
    }

    # Log call start
    conversation_logger.log_call_start(
        session_id=call_sid,
        caller_number=caller_number,
        metadata={
            "to_number": request.values.get("To"),
            "direction": request.values.get("Direction"),
            "call_status": request.values.get("CallStatus")
        }
    )

    greeting = os.getenv("VOICE_GREETING", "Thanks for calling the clinic. How can I help you today?")
    action_url = _get_action_url("voice_handle")
    twiml = voice_client.gather(prompt=greeting, action_url=action_url)
    return Response(twiml, mimetype="text/xml")


@app.route("/voice/handle", methods=["GET", "POST"])
def voice_handle():
    global dialogue_manager, voice_client, conversation_logger
    if dialogue_manager is None:
        dialogue_manager = build_dialogue_manager()
    if voice_client is None:
        voice_client = build_voice_client()

    call_sid = request.values.get("CallSid")
    utterance = request.values.get("SpeechResult", "") or request.values.get("Digits", "")
    state = call_state.get(call_sid, ConversationState())

    # Track turn number
    if call_sid not in call_metadata:
        call_metadata[call_sid] = {"start_time": time.time(), "turn_count": 0}
    call_metadata[call_sid]["turn_count"] += 1
    turn_number = call_metadata[call_sid]["turn_count"]

    logger.info(f"Processing turn {turn_number} for call {call_sid}: '{utterance}'")

    # Build input_data and always try to extract patient_name/dob from the utterance.
    input_data = {"utterance": utterance, "state": state}
    name, dob = _extract_name_and_dob(utterance)
    if name:
        input_data["patient_name"] = name
    if dob:
        input_data["dob"] = dob

    # Measure latency
    start_time = time.time()

    try:
        dm_result = _run_async(dialogue_manager.execute(input_data))
    except Exception as e:
        # Log error
        conversation_logger.log_error(
            session_id=call_sid,
            error_type=type(e).__name__,
            error_message=str(e),
            metadata={"turn": turn_number, "utterance_length": len(utterance)}
        )
        raise

    latency_ms = (time.time() - start_time) * 1000

    logger.info(f"DM result status: {dm_result.status}, output: {dm_result.output}, metadata: {dm_result.metadata}")

    new_state = ConversationState.from_dict(dm_result.output.get("state", {}))

    # If DM asked for authentication, set a step to expect credentials next turn
    if dm_result.metadata.get("auth_prompted"):
        new_state.set_step("awaiting_auth")

    # If authentication succeeded, clear any awaiting step
    if new_state.patient_id:
        new_state.set_step(None)

    call_state[call_sid] = new_state

    response_text = (
        dm_result.output.get("text")
        or dm_result.output.get("answer")
        or "I didn't catch that. Could you repeat?"
    )
    logger.info(f"Response text: {response_text}")

    # Log this turn
    conversation_logger.log_turn(
        session_id=call_sid,
        turn_number=turn_number,
        utterance=utterance,
        intent=new_state.current_intent,
        entities={},  # Could extract from DM if needed
        agent=dm_result.metadata.get("agent", "DialogueManager"),
        result=dm_result.status.value,
        response_text=response_text,
        latency_ms=latency_ms,
        status=dm_result.status.value,
        confidence_score=dm_result.metadata.get("confidence_score"),
        error=dm_result.errors[0] if dm_result.errors else None,
        metadata={
            "auth_prompted": dm_result.metadata.get("auth_prompted", False),
            "patient_id": new_state.patient_id if new_state.patient_id else None,
            "flagged_for_review": dm_result.metadata.get("flagged_for_review", False),
            "retry_count": getattr(new_state, "retry_count", None),
        },
    )

    # Hang up if user says goodbye. If DM asked for auth (auth_prompted), keep the call open
    lower = (utterance or "").lower()
    auth_prompted = bool(dm_result.metadata.get("auth_prompted"))
    should_end = "goodbye" in lower or (dm_result.status == AgentStatus.FAILURE and not auth_prompted)

    if should_end:
        # Log call end
        if call_sid in call_metadata:
            duration_seconds = time.time() - call_metadata[call_sid]["start_time"]
            total_turns = call_metadata[call_sid]["turn_count"]
            outcome = "success" if dm_result.status == AgentStatus.SUCCESS else "failure"

            conversation_logger.log_call_end(
                session_id=call_sid,
                duration_seconds=duration_seconds,
                outcome=outcome,
                total_turns=total_turns,
                metadata={"reason": "goodbye" if "goodbye" in lower else "failure"}
            )

            # Clean up
            call_metadata.pop(call_sid, None)

        twiml = voice_client.say_and_hangup(response_text)
        call_state.pop(call_sid, None)
    else:
        action_url = _get_action_url("voice_handle")
        twiml = voice_client.say_and_gather(response_text, action_url=action_url)

    return Response(twiml, mimetype="text/xml")


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
