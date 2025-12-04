"""Tests for Twilio voice client helper."""

import pytest
from src.integrations.twilio_client import TwilioVoiceClient


def test_twilio_client_creation():
    """Test basic client creation."""
    client = TwilioVoiceClient()
    assert client.default_action == "/voice/handle"

    client2 = TwilioVoiceClient(default_action="/custom")
    assert client2.default_action == "/custom"


def test_gather_generates_twiml():
    """Test gather method generates valid TwiML."""
    client = TwilioVoiceClient()
    twiml = client.gather("Hello, how can I help?")

    assert '<?xml version="1.0" encoding="UTF-8"?>' in twiml
    assert '<Response>' in twiml
    assert '<Gather' in twiml
    assert 'input="speech"' in twiml
    assert 'action="/voice/handle"' in twiml
    assert 'method="POST"' in twiml
    assert '<Say>Hello, how can I help?</Say>' in twiml
    assert '</Gather>' in twiml
    assert '</Response>' in twiml


def test_gather_with_custom_action():
    """Test gather with custom action URL."""
    client = TwilioVoiceClient()
    twiml = client.gather("What's your name?", action_url="/custom/endpoint")

    assert 'action="/custom/endpoint"' in twiml
    assert '<Say>What\'s your name?</Say>' in twiml


def test_gather_with_timeout():
    """Test gather with custom timeout."""
    client = TwilioVoiceClient()
    twiml = client.gather("Speak now", timeout=10)

    assert 'timeout="10"' in twiml


def test_say_and_gather():
    """Test say_and_gather method."""
    client = TwilioVoiceClient()
    twiml = client.say_and_gather("Processing your request.")

    assert '<Say>Processing your request.</Say>' in twiml
    assert '<Gather' in twiml
    assert '<Say>You can speak after the tone.</Say>' in twiml


def test_say_and_hangup():
    """Test say_and_hangup terminates call."""
    client = TwilioVoiceClient()
    twiml = client.say_and_hangup("Thank you for calling. Goodbye!")

    assert '<Say>Thank you for calling. Goodbye!</Say>' in twiml
    assert '<Hangup' in twiml  # TwiML uses <Hangup /> with space
    assert '<Gather' not in twiml  # Should not gather after hangup
