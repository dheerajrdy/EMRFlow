"""Tests for Flask voice server endpoints."""

import pytest
from src.cli.voice_server import app


@pytest.fixture
def client():
    """Create Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_voice_endpoint_get(client):
    """Test /voice endpoint handles GET requests."""
    response = client.get('/voice?CallSid=test123')
    assert response.status_code == 200
    assert response.mimetype == 'text/xml'
    assert b'<?xml version="1.0" encoding="UTF-8"?>' in response.data
    assert b'<Response>' in response.data
    assert b'<Gather' in response.data
    assert b'Thanks for calling the clinic' in response.data


def test_voice_endpoint_post(client):
    """Test /voice endpoint handles POST requests (Twilio format)."""
    response = client.post('/voice', data={'CallSid': 'test456'})
    assert response.status_code == 200
    assert response.mimetype == 'text/xml'
    assert b'<Response>' in response.data
    assert b'<Gather' in response.data


def test_voice_endpoint_initializes_call_state(client):
    """Test /voice creates conversation state for call."""
    from src.cli.voice_server import call_state

    # Clear any existing state
    call_state.clear()

    call_sid = 'test789'
    client.post('/voice', data={'CallSid': call_sid})

    # Verify state was created
    assert call_sid in call_state
    assert call_state[call_sid].current_intent is None


def test_voice_handle_endpoint(client):
    """Test /voice/handle processes speech input."""
    # First initialize a call
    call_sid = 'test_handle_123'
    client.post('/voice', data={'CallSid': call_sid})

    # Then handle speech input
    response = client.post('/voice/handle', data={
        'CallSid': call_sid,
        'SpeechResult': 'What are your hours?'
    })

    assert response.status_code == 200
    assert response.mimetype == 'text/xml'
    assert b'<Response>' in response.data
    # Should either gather again or hangup
    assert b'<Say>' in response.data


def test_voice_handle_goodbye_ends_call(client):
    """Test saying goodbye hangs up the call."""
    from src.cli.voice_server import call_state

    call_sid = 'test_goodbye'
    client.post('/voice', data={'CallSid': call_sid})

    response = client.post('/voice/handle', data={
        'CallSid': call_sid,
        'SpeechResult': 'goodbye'
    })

    assert response.status_code == 200
    assert b'<Hangup' in response.data
    # Call state should be cleaned up
    assert call_sid not in call_state


def test_voice_handle_empty_speech(client):
    """Test handling empty or missing speech input."""
    call_sid = 'test_empty'
    client.post('/voice', data={'CallSid': call_sid})

    response = client.post('/voice/handle', data={
        'CallSid': call_sid,
        'SpeechResult': ''
    })

    assert response.status_code == 200
    assert b'<Response>' in response.data
    # Should provide fallback response
    assert b'<Say>' in response.data


def test_voice_handle_persists_conversation_state(client):
    """Test conversation state is maintained across turns."""
    from src.cli.voice_server import call_state

    call_sid = 'test_state_123'

    # Initialize call
    client.post('/voice', data={'CallSid': call_sid})
    initial_history_len = len(call_state[call_sid].history)

    # First turn
    client.post('/voice/handle', data={
        'CallSid': call_sid,
        'SpeechResult': 'hello'
    })

    # Verify state was updated with user and assistant turns
    updated_state = call_state[call_sid]
    assert len(updated_state.history) > initial_history_len
    assert updated_state.current_intent is not None  # Intent should be set


def test_custom_greeting_from_env(client, monkeypatch):
    """Test custom greeting can be set via environment variable."""
    monkeypatch.setenv('VOICE_GREETING', 'Custom greeting here')

    response = client.post('/voice', data={'CallSid': 'custom123'})

    assert b'Custom greeting here' in response.data
