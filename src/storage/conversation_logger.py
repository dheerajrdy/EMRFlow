"""
Conversation logging for voice interactions.

Creates structured JSONL logs for each conversation with PHI sanitization.
Required by design doc for debugging, compliance, and demo purposes.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class ConversationLogger:
    """
    Logs conversation turns to JSONL format.

    Creates one file per conversation session in format: runs/{session_id}.jsonl
    Each line is a JSON object representing a turn or event.
    """

    def __init__(self, storage_path: str = "runs"):
        """
        Initialize conversation logger.

        Args:
            storage_path: Directory path for storing conversation logs
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)

    def _sanitize_phi(self, text: str) -> str:
        """
        Sanitize Protected Health Information from text.

        Masks:
        - Names (common patterns)
        - Dates of birth
        - Phone numbers
        - Specific medical values

        Args:
            text: Text that may contain PHI

        Returns:
            Sanitized text safe for logging
        """
        if not text:
            return text

        # Mask phone numbers
        text = re.sub(r'\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE]', text)

        # Mask dates (various formats)
        text = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]', text)
        text = re.sub(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', '[DATE]', text)

        # Mask "born [date]" patterns
        text = re.sub(r'born\s+[\w\s,]+\d{1,4}', 'born [DATE]', text, flags=re.IGNORECASE)

        # Mask "My name is [Name]" patterns
        text = re.sub(r'(my name is|I am|I\'m)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)',
                     r'\1 [NAME]', text, flags=re.IGNORECASE)

        # Mask specific lab values (numbers with units)
        text = re.sub(r'\b\d+\.?\d*\s*(mg/dL|mmHg|%|IU)\b', '[LAB_VALUE]', text)

        return text

    def log_call_start(
        self,
        session_id: str,
        caller_number: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log the start of a phone call.

        Args:
            session_id: Unique session/call identifier
            caller_number: Caller's phone number (will be sanitized)
            metadata: Additional metadata (e.g., Twilio call SID)
        """
        event = {
            "session_id": session_id,
            "event": "call_start",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "caller": self._sanitize_phi(caller_number) if caller_number else None,
            "metadata": metadata or {}
        }

        self._write_event(session_id, event)
        logger.info(f"Call started: {session_id}")

    def log_turn(
        self,
        session_id: str,
        turn_number: int,
        utterance: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        agent: Optional[str] = None,
        result: Optional[str] = None,
        response_text: Optional[str] = None,
        latency_ms: Optional[float] = None,
        status: Optional[str] = None,
        confidence_score: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a single conversation turn.

        Args:
            session_id: Session identifier
            turn_number: Turn number (1-indexed)
            utterance: User's utterance (will be sanitized)
            intent: Classified intent
            entities: Extracted entities
            agent: Backend agent that handled this turn
            result: Agent result/action
            response_text: System response (will be sanitized)
            latency_ms: Processing time in milliseconds
            status: Turn status (success, failure, partial)
            metadata: Additional turn metadata
        """
        event = {
            "session_id": session_id,
            "event": "turn",
            "turn": turn_number,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "utterance": self._sanitize_phi(utterance) if utterance else None,
            "intent": intent,
            "entities": entities or {},
            "agent": agent,
            "result": result,
            "response": self._sanitize_phi(response_text) if response_text else None,
            "latency_ms": latency_ms,
            "status": status,
            "confidence_score": confidence_score,
            "error": error,
            "metadata": metadata or {}
        }

        self._write_event(session_id, event)
        logger.debug(f"Turn {turn_number} logged for session {session_id}")

    def log_error(
        self,
        session_id: str,
        error_type: str,
        error_message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error during the conversation.

        Args:
            session_id: Session identifier
            error_type: Type/category of error
            error_message: Error description
            metadata: Additional error context
        """
        event = {
            "session_id": session_id,
            "event": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error_type": error_type,
            "error_message": error_message,
            "metadata": metadata or {}
        }

        self._write_event(session_id, event)
        logger.warning(f"Error logged for session {session_id}: {error_type}")

    def log_call_end(
        self,
        session_id: str,
        duration_seconds: Optional[float] = None,
        outcome: Optional[str] = None,
        total_turns: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log the end of a phone call.

        Args:
            session_id: Session identifier
            duration_seconds: Call duration in seconds
            outcome: Call outcome (success, failure, abandoned)
            total_turns: Total number of turns in conversation
            metadata: Additional call metadata
        """
        event = {
            "session_id": session_id,
            "event": "call_end",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "duration_seconds": duration_seconds,
            "outcome": outcome,
            "total_turns": total_turns,
            "metadata": metadata or {}
        }

        self._write_event(session_id, event)
        logger.info(f"Call ended: {session_id} (outcome: {outcome}, turns: {total_turns})")

    def _write_event(self, session_id: str, event: Dict[str, Any]) -> None:
        """
        Write an event to the session's JSONL file.

        Args:
            session_id: Session identifier
            event: Event data to log
        """
        try:
            log_file = self.storage_path / f"{session_id}.jsonl"

            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")

        except Exception as e:
            logger.error(f"Failed to write event to {log_file}: {str(e)}")
            # Don't raise - logging failures shouldn't crash the app

    def get_conversation(self, session_id: str) -> Optional[list]:
        """
        Retrieve all events for a conversation.

        Args:
            session_id: Session identifier

        Returns:
            List of event dictionaries, or None if not found
        """
        log_file = self.storage_path / f"{session_id}.jsonl"

        if not log_file.exists():
            return None

        try:
            events = []
            with open(log_file, "r") as f:
                for line in f:
                    events.append(json.loads(line))

            return events

        except Exception as e:
            logger.error(f"Failed to read conversation {session_id}: {str(e)}")
            return None

    def list_conversations(self, limit: Optional[int] = None) -> list:
        """
        List all conversation session IDs.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session IDs, most recent first
        """
        try:
            # Get all .jsonl files
            log_files = sorted(
                self.storage_path.glob("*.jsonl"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            if limit:
                log_files = log_files[:limit]

            # Extract session IDs from filenames
            return [f.stem for f in log_files]

        except Exception as e:
            logger.error(f"Failed to list conversations: {str(e)}")
            return []


# Singleton instance for easy access
_logger_instance = None


def get_conversation_logger(storage_path: str = "runs") -> ConversationLogger:
    """
    Get or create the singleton conversation logger instance.

    Args:
        storage_path: Directory path for storing logs

    Returns:
        ConversationLogger instance
    """
    global _logger_instance

    if _logger_instance is None:
        _logger_instance = ConversationLogger(storage_path)

    return _logger_instance
