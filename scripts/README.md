# Test & Utility Scripts

This directory contains test scripts and utilities for development and debugging.

## Test Scripts

### Authentication & Flow Testing
- **test_auth_flow.py** - Tests authentication prompt flow (single turn)
- **test_full_conversation.py** - Tests complete multi-turn conversation (mock model)
- **test_natural_responses.py** - Tests natural response generation with Gemini

### Model Testing
- **test_gemini_setup.py** - Tests Gemini API connection and configuration
- **test_google_model_client.py** - Tests GoogleModelClient implementation

## Usage

Run from project root with virtual environment activated:

```bash
source .venv/bin/activate

# Test authentication flow
python scripts/test_auth_flow.py

# Test full conversation with mocks
python scripts/test_full_conversation.py

# Test natural responses with real Gemini
python scripts/test_natural_responses.py
```

## Note

These are development/debugging scripts. For unit tests, see `/tests/` directory.
For integration tests, run: `pytest tests/`
