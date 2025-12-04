# EMRFlow - AI Voice Assistant for Patient Support

**EMRFlow** is a multi-agent voice assistant system for healthcare patient support. Built for the Heidi Health hackathon, it handles patient phone calls for scheduling appointments, answering medical questions, and providing 24/7 assistance through natural voice interactions.

## Project Status

🚀 **~70% Complete** - Core functionality working, ready for demo polish

### ✅ Working
- Multi-agent architecture with specialized AI agents
- Natural language understanding (Gemini-powered)
- End-to-end appointment booking flow
- Patient authentication and records access
- Natural, conversational responses
- Twilio telephony integration
- Comprehensive test suite (46/46 passing)

### 🔄 In Progress
- Conversation logging (JSONL format)
- Live Twilio testing
- Evaluation harness

## Quick Start

### Prerequisites
- Python 3.9+
- Google Cloud API key (for Gemini)
- Twilio account (for voice calls)

### Setup

```bash
# Clone repository
git clone <repo-url>
cd EMRFlow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys:
# - GOOGLE_API_KEY (required)
# - TWILIO_ACCOUNT_SID (optional, for voice calls)
# - TWILIO_AUTH_TOKEN (optional)
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_agents/ -v

# Test with actual Gemini API
python scripts/test_natural_responses.py
```

### Start Voice Server

```bash
# Start Flask server
python -m src.cli.voice_server

# In another terminal, start ngrok
ngrok http 5000

# Configure Twilio webhook to ngrok URL + /voice
```

## Project Structure

```
/
├── src/                      # Application source code
│   ├── agents/              # Multi-agent implementations
│   │   ├── base_agent.py         # Base agent abstraction
│   │   ├── dialogue_manager.py   # Central orchestrator
│   │   ├── nlu_agent.py          # Intent classification
│   │   ├── scheduling_agent.py   # Appointment management
│   │   ├── records_agent.py      # Patient records access
│   │   ├── knowledge_agent.py    # FAQ handler
│   │   ├── asr_agent.py          # Speech-to-text
│   │   └── tts_agent.py          # Text-to-speech
│   ├── orchestration/       # Workflow engine
│   ├── integrations/        # External services (Twilio, Google)
│   ├── models/              # LLM client abstraction
│   ├── utils/               # Utilities (response generation, state management)
│   ├── data/                # Mock patient data
│   ├── storage/             # Run logging
│   └── cli/                 # CLI & voice server
├── tests/                   # Unit & integration tests
│   ├── test_agents/         # Agent tests
│   ├── test_integrations/   # Integration tests
│   ├── test_workflows/      # E2E workflow tests
│   └── evaluation/          # Evaluation scenarios
├── scripts/                 # Development scripts
│   ├── test_auth_flow.py    # Auth flow testing
│   ├── test_full_conversation.py  # Multi-turn testing
│   └── test_natural_responses.py  # Natural language testing
├── docs/                    # Documentation
│   ├── design/              # Architecture & design docs
│   ├── reports/             # Progress & validation reports
│   └── setup/               # Setup guides
├── runs/                    # Conversation logs
├── config/                  # Configuration files
├── CLAUDE.md                # Development guidelines & implementation plan
└── README.md                # This file
```

## Architecture

### Multi-Agent System

EMRFlow uses a **workflow-based orchestration pattern** with specialized agents:

1. **ASR Agent** - Speech-to-text (Google Speech API)
2. **NLU Agent** - Intent classification and entity extraction (Gemini)
3. **Dialogue Manager** - Central orchestrator, conversation flow control
4. **Scheduling Agent** - Appointment booking, rescheduling, cancellation
5. **Records Agent** - Patient data access (mock EHR)
6. **Knowledge Agent** - FAQ and general queries
7. **TTS Agent** - Text-to-speech synthesis

### Conversation Flow

```
1. User calls → Twilio → Flask server
2. ASR transcribes speech
3. NLU extracts intent & entities
4. Dialogue Manager routes to appropriate agent
5. Agent processes request
6. Response Generator creates natural response
7. TTS synthesizes speech
8. Response sent back to user
9. Loop until call ends
```

### Key Features

- **Natural Conversations**: Gemini-powered response generation sounds like a real receptionist
- **Multi-turn Dialogues**: Handles authentication, slot selection, confirmation across multiple turns
- **Patient Safety**: Authentication required before accessing PHI
- **Graceful Fallback**: Clear error messages, offers human assistance when needed
- **Comprehensive Logging**: Structured execution traces for debugging and compliance

## Core Use Cases

1. **Appointment Scheduling**: Book new appointments with available time slots
2. **Appointment Management**: Reschedule or cancel existing appointments
3. **Medical Information**: Query lab results, medications, visit notes (authenticated)
4. **General FAQ**: Clinic hours, location, insurance questions

## Development

### Running Tests

```bash
# Full test suite
pytest tests/ -v --cov=src

# Specific test categories
pytest tests/test_agents/ -v          # Agent tests
pytest tests/test_integrations/ -v    # Integration tests
pytest tests/test_workflows/ -v       # E2E tests

# With coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Scripts

```bash
# Test authentication flow
python scripts/test_auth_flow.py

# Test full conversation (with mocks)
python scripts/test_full_conversation.py

# Test natural responses (with real Gemini)
python scripts/test_natural_responses.py
```

## Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Complete development guide, implementation plan, and coding guidelines
- **[docs/design/design_doc.md](./docs/design/design_doc.md)** - Full PRD and technical architecture
- **[docs/reports/PROGRESS_REPORT.md](./docs/reports/PROGRESS_REPORT.md)** - Current status and progress
- **[docs/setup/SETUP.md](./docs/setup/SETUP.md)** - Detailed setup instructions

## Technology Stack

- **Language**: Python 3.9+
- **LLM**: Google Gemini 2.5 Flash (via google-generativeai)
- **Voice**: Twilio (telephony), Google Speech API (STT/TTS)
- **Testing**: pytest, pytest-asyncio, pytest-cov
- **Server**: Flask
- **Mock Data**: JSON files (patients, schedules, FAQs)

## Configuration

### Environment Variables (.env)

```bash
# Required
GOOGLE_API_KEY=your-api-key-here
GOOGLE_CLOUD_PROJECT=your-project-id

# Optional (for voice calls)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=your-twilio-number

# Optional (configuration)
DEMO_MODE=true  # Enables lenient authentication for testing
PORT=5000       # Flask server port
```

## Hackathon Context

**Challenge**: Heidi Health hackathon - Novel applications of voice agents in healthcare

**Goal**: Demonstrate multi-agent AI proficiency in handling patient phone calls

**Key Differentiators**:
- Natural, empathetic conversation style
- Multi-agent architecture with clear separation of concerns
- Safe handling of PHI with authentication
- Graceful error handling and fallback to human assistance

## Contributing

This is a hackathon project. For development guidelines, see [CLAUDE.md](./CLAUDE.md).

## License

[Your License Here]

---

**Built for Heidi Health Hackathon 2025**
