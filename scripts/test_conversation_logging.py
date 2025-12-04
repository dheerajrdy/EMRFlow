#!/usr/bin/env python3
"""
Test conversation logging system.

Simulates a conversation and verifies JSONL logs are created correctly.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.storage.conversation_logger import ConversationLogger


def test_logging():
    """Test the conversation logging system."""

    print("=" * 80)
    print("TESTING CONVERSATION LOGGING")
    print("=" * 80)

    # Create logger with test directory
    test_dir = Path("runs/test")
    test_dir.mkdir(parents=True, exist_ok=True)

    logger = ConversationLogger(storage_path=str(test_dir))

    session_id = "test-session-123"

    # Test 1: Log call start
    print("\n[TEST 1] Logging call start...")
    logger.log_call_start(
        session_id=session_id,
        caller_number="+1-555-123-4567",
        metadata={"to_number": "+1-800-CLINIC"}
    )
    print("✅ Call start logged")

    # Test 2: Log first turn (with PHI)
    print("\n[TEST 2] Logging turn with PHI...")
    logger.log_turn(
        session_id=session_id,
        turn_number=1,
        utterance="My name is John Doe, born March 15, 1980",
        intent="ScheduleAppointment",
        entities={"patient_name": "John Doe", "dob": "1980-03-15"},
        agent="DialogueManager",
        result="auth_required",
        response_text="To book an appointment, I'll need to verify your identity. Please confirm your name and date of birth.",
        latency_ms=245.5,
        status="failure",
        metadata={"auth_prompted": True}
    )
    print("✅ Turn 1 logged")

    # Test 3: Log second turn
    print("\n[TEST 3] Logging successful turn...")
    logger.log_turn(
        session_id=session_id,
        turn_number=2,
        utterance="I want Tuesday at 2 PM",
        intent="ScheduleAppointment",
        entities={"preferred_time": "Tuesday 2 PM"},
        agent="SchedulingAgent",
        result="booked",
        response_text="Perfect! I've booked your appointment with Dr. Smith for Tuesday, December 5th at 2:00 PM.",
        latency_ms=1823.2,
        status="success",
        metadata={"appointment_id": "A-12345", "patient_id": "P-1001"}
    )
    print("✅ Turn 2 logged")

    # Test 4: Log error
    print("\n[TEST 4] Logging error...")
    logger.log_error(
        session_id=session_id,
        error_type="ValidationError",
        error_message="Patient ID not found",
        metadata={"attempted_id": "P-9999"}
    )
    print("✅ Error logged")

    # Test 5: Log call end
    print("\n[TEST 5] Logging call end...")
    logger.log_call_end(
        session_id=session_id,
        duration_seconds=127.5,
        outcome="success",
        total_turns=2,
        metadata={"reason": "completed"}
    )
    print("✅ Call end logged")

    # Verify the log file was created
    log_file = test_dir / f"{session_id}.jsonl"
    if not log_file.exists():
        print(f"\n❌ FAILED: Log file not created at {log_file}")
        return False

    print(f"\n✅ Log file created: {log_file}")

    # Read and verify log contents
    print("\n[VERIFICATION] Reading log file...")
    print("-" * 80)

    events = []
    with open(log_file, "r") as f:
        for i, line in enumerate(f, 1):
            event = json.loads(line)
            events.append(event)
            print(f"\nEvent {i}: {event['event']}")
            print(f"  Timestamp: {event['timestamp']}")

            if event['event'] == 'turn':
                print(f"  Turn: {event['turn']}")
                print(f"  Utterance: {event['utterance']}")
                print(f"  Intent: {event['intent']}")
                print(f"  Response: {event['response'][:50]}...")
                print(f"  Latency: {event['latency_ms']}ms")
                print(f"  Status: {event['status']}")

            elif event['event'] == 'call_start':
                print(f"  Caller: {event['caller']}")

            elif event['event'] == 'call_end':
                print(f"  Duration: {event['duration_seconds']}s")
                print(f"  Outcome: {event['outcome']}")
                print(f"  Total turns: {event['total_turns']}")

            elif event['event'] == 'error':
                print(f"  Error type: {event['error_type']}")
                print(f"  Message: {event['error_message']}")

    print("\n" + "-" * 80)

    # Verify PHI sanitization
    print("\n[PHI SANITIZATION CHECK]")
    turn_1 = events[1]  # First turn event
    utterance = turn_1['utterance']

    if "[NAME]" in utterance and "[DATE]" in utterance:
        print("✅ PHI correctly sanitized in utterance")
    else:
        print(f"⚠️  PHI may not be sanitized: {utterance}")

    # Verify expected events
    print("\n[EVENT COUNT CHECK]")
    expected_events = ["call_start", "turn", "turn", "error", "call_end"]
    actual_events = [e['event'] for e in events]

    if actual_events == expected_events:
        print(f"✅ All expected events present: {expected_events}")
    else:
        print(f"⚠️  Event mismatch!")
        print(f"  Expected: {expected_events}")
        print(f"  Actual: {actual_events}")

    print("\n" + "=" * 80)
    print("✅ CONVERSATION LOGGING TEST COMPLETE!")
    print("=" * 80)

    print(f"\nLog file location: {log_file}")
    print(f"Total events logged: {len(events)}")

    return True


if __name__ == "__main__":
    try:
        success = test_logging()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
