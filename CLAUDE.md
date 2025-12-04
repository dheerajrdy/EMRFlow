# CLAUDE.md

This file provides guidance to Claude Code when working with EMRFlow - an AI Voice Assistant for Patient Support.

## Project Overview

**EMRFlow** is a multi-agent voice assistant system for healthcare patient support. The system handles patient phone calls for scheduling appointments, answering medical questions, and providing 24/7 assistance through natural voice interactions.

**Challenge**: Heidi Health hackathon - Novel applications of voice agents in healthcare to improve patient care and service efficiency.

**Key Architecture**: Multi-agent system using Google Cloud Platform (GCP) Agent Development Kit with specialized AI agents for speech recognition, NLU, scheduling, patient records, and dialogue management.

## Hackathon Scope

To avoid overbuilding and stay focused on delivering a working demo, we explicitly define what is in scope vs out of scope:

### ✅ In Scope (Must Have for Hackathon)
- **Voice → Text → Intent → Response** pipeline working end-to-end
- **2-3 main use cases** fully implemented:
  1. Appointment scheduling (book new appointment)
  2. Appointment management (reschedule/cancel)
  3. Medical information query (lab results, medications)
- **Mock data** for patients, schedules, FAQs (no real EHR integration)
- **Text-based testing** (voice is nice-to-have, not required)
- **Sequential + Conditional workflow** orchestration
- **Basic evaluation harness** with 5-10 test scenarios
- **Conversation logging** for demo and debugging
- **Web-based voice UI** OR Twilio integration (pick one)
- **PHI protection** in logs (sanitize sensitive data)

### ❌ Out of Scope (Future Work)
- Complex triage logic (medical decision trees)
- Real EHR/EMR system integration
- FHIR/HL7 message parsing
- Rich staff dashboards
- Multi-language support
- Advanced NLU (semantic search, embeddings)
- Production-grade security (OAuth, encryption at rest)
- Billing integration
- Prescription management
- Advanced analytics/reporting
- Multi-tenant architecture
- Load testing/scalability optimization

### 🎯 Success Criteria for Hackathon
1. **Functional demo**: Complete 3 end-to-end conversation scenarios
2. **Architecture clarity**: Clearly show multi-agent design in presentation
3. **Healthcare value**: Demonstrate patient experience improvement
4. **Technical soundness**: Clean code, tests passing, no crashes
5. **Bonus points**: Voice UI working, eval metrics shown

Start simple, iterate. Don't build features "just in case." Only implement what's needed for the 3 core demo scenarios.

## Core Components (Multi-Agent Architecture)

### Agents
1. **ASR Agent**: Speech-to-Text (Google Speech API or Whisper)
2. **NLU Agent**: Natural Language Understanding (Gemini/Claude)
3. **Dialogue Manager**: Central orchestrator and conversation controller
4. **Appointment Scheduling Agent**: Manages bookings, reschedules, cancellations
5. **Patient Records Agent**: Accesses mock EHR data
6. **Knowledge Base Agent**: Handles FAQs and general queries
7. **TTS Agent**: Text-to-Speech synthesis

**Implementation Note - Agent vs Tool:**
ASR and TTS are implemented as thin agent wrappers around deterministic tools/services (Google Speech API, Google TTS). Conceptually, they function as **tools** in the agent toolset rather than reasoning agents. The cognitive agents (NLU, Dialogue Manager, Scheduling, Records, Knowledge) use these tools to interact with voice I/O. This distinction helps maintain clear separation between:
- **Agents**: Components that reason, plan, and make decisions (NLU, Dialogue Manager, domain agents)
- **Tools**: Deterministic services that perform specific actions (speech recognition, text-to-speech, API calls)

### Key Use Cases
- **Appointment Scheduling**: Book, reschedule, cancel appointments
- **Appointment Management**: Modify existing appointments
- **Medical Information Query**: Lab results, medications, visit notes
- **General FAQ**: Clinic hours, location, procedures

## Orchestration Pattern

**EMRFlow uses a Workflow-based Orchestration Pattern** combining Sequential and Conditional workflows:

### Pattern: Sequential + Conditional Workflow
For each conversation turn, the system follows a **sequential pipeline**:

1. **ASR** (Speech-to-Text) → Transcribe user audio to text
2. **NLU** (Intent Classification) → Extract intent and entities
3. **Routing** (Dialogue Manager) → Route to appropriate backend agent based on intent
4. **Backend Agent** → Execute domain-specific logic
5. **Response Generation** → Format response for user
6. **TTS** (Text-to-Speech) → Synthesize speech output
7. **Loop** → Return to step 1 for next turn

### Conditional Branching in Dialogue Manager
The Dialogue Manager implements **conditional routing logic**:

```
if intent ∈ {ScheduleAppointment, RescheduleAppointment, CancelAppointment}:
    → Route to SchedulingAgent
elif intent == InfoQuery:
    → Route to RecordsAgent
elif intent == FAQ:
    → Route to KnowledgeAgent
else:
    → Fallback (offer human assistance)
```

### Why This Pattern?
- **Explicit control**: Predictable conversation flow for healthcare context
- **Easy to debug**: Clear trace of which agent handled each turn
- **Safety**: Well-defined boundaries prevent unintended behavior
- **Extensibility**: Easy to add new intents/agents by extending conditional logic

For the hackathon prototype, we use **explicit orchestration** rather than autonomous agent-to-agent communication. This ensures:
- Deterministic behavior for patient safety
- Clear audit trail for compliance
- Lower latency (no multi-agent negotiation overhead)

## Project Structure

```
/
├── src/
│   ├── agents/                    # Agent implementations
│   │   ├── base_agent.py         # Base agent abstraction ✅
│   │   ├── asr_agent.py          # Speech-to-Text agent
│   │   ├── nlu_agent.py          # Natural Language Understanding
│   │   ├── dialogue_manager.py   # Conversation orchestrator
│   │   ├── scheduling_agent.py   # Appointment management
│   │   ├── records_agent.py      # Patient records access
│   │   ├── knowledge_agent.py    # FAQ handler
│   │   └── tts_agent.py          # Text-to-Speech
│   ├── orchestration/            # Workflow engine
│   │   ├── workflow_engine.py    # Workflow runner ✅
│   │   ├── workflow_context.py   # Shared context ✅
│   │   └── voice_workflow.py     # Voice-specific workflow
│   ├── integrations/             # External integrations
│   │   ├── twilio_client.py      # Twilio telephony
│   │   ├── google_speech.py      # Google Speech API
│   │   └── google_gemini.py      # Gemini LLM client
│   ├── models/                   # Model abstractions
│   │   └── model_client.py       # LLM client interface ✅
│   ├── data/                     # Mock data
│   │   ├── patients.json         # Mock patient records
│   │   ├── schedule.json         # Mock clinic schedule
│   │   └── faq.json              # FAQ knowledge base
│   ├── storage/                  # Run metadata
│   │   └── run_storage.py        # Conversation logging ✅
│   ├── cli/                      # CLI interface
│   │   └── run_workflow.py       # CLI commands ✅
│   └── utils/                    # Utilities
│       ├── phi_protection.py     # PHI sanitization
│       └── conversation_state.py # Dialogue state management
├── tests/                        # Test suite
│   ├── test_agents/              # Agent tests
│   ├── test_integrations/        # Integration tests
│   └── test_workflows/           # E2E workflow tests
├── docs/
│   └── design/
│       ├── design_doc.md         # Complete PRD ✅
│       └── CODEFLOW_LEARNINGS.md # Pattern reference ✅
├── runs/                         # Conversation logs
├── config/                       # Configuration
│   └── config.template.yaml      # Config template ✅
└── .env                          # Environment variables ✅
```

## IMPLEMENTATION PLAN - STEP-BY-STEP

This is your roadmap. We will build each step, validate, and move to the next.

---

### **PHASE 1: Foundation & Mock Data** (Day 1-2)

#### Step 1.1: Set Up Mock Data
**Goal**: Create realistic mock patient records, schedules, and FAQ data

**Tasks**:
- [ ] Create `src/data/patients.json` with 3-5 fictional patients
  - Include: name, DOB, ID, appointments, medications, lab results, visit notes
- [ ] Create `src/data/schedule.json` with doctor availability
  - 2-3 doctors, 2 weeks of available time slots
- [ ] Create `src/data/faq.json` with common questions
  - Clinic hours, location, insurance, procedures
- [ ] Create data loading utilities in `src/utils/data_loader.py`

**Validation**: Load mock data and print samples to verify structure

**Files to Create**:
- `src/data/patients.json`
- `src/data/schedule.json`
- `src/data/faq.json`
- `src/utils/data_loader.py`

---

#### Step 1.2: Implement Patient Records Agent
**Goal**: Build agent to query mock EHR data

**Tasks**:
- [ ] Create `src/agents/records_agent.py` extending `BaseAgent`
- [ ] Implement methods:
  - `get_patient_by_dob(name, dob)` - Authenticate patient
  - `get_upcoming_appointments(patient_id)` - Fetch appointments
  - `get_lab_results(patient_id)` - Retrieve test results
  - `get_medications(patient_id)` - Get medication list
  - `get_visit_notes(patient_id)` - Fetch doctor notes
- [ ] Add PHI protection for logging (use `_protect_phi()`)
- [ ] Write unit tests in `tests/test_agents/test_records_agent.py`

**Validation**: Test each method with mock patient data

**Files to Create**:
- `src/agents/records_agent.py`
- `tests/test_agents/test_records_agent.py`

---

#### Step 1.3: Implement Scheduling Agent
**Goal**: Build agent to manage appointments

**Tasks**:
- [ ] Create `src/agents/scheduling_agent.py` extending `BaseAgent`
- [ ] Implement methods:
  - `find_available_slots(doctor, date_range)` - Search availability
  - `book_appointment(patient_id, slot)` - Reserve time slot
  - `reschedule_appointment(appointment_id, new_slot)` - Change appointment
  - `cancel_appointment(appointment_id)` - Cancel booking
- [ ] Ensure no double-booking logic
- [ ] Write unit tests in `tests/test_agents/test_scheduling_agent.py`

**Validation**: Test booking, rescheduling, and cancellation flows

**Files to Create**:
- `src/agents/scheduling_agent.py`
- `tests/test_agents/test_scheduling_agent.py`

---

#### Step 1.4: Implement Knowledge Base Agent
**Goal**: Build agent to answer FAQs

**Tasks**:
- [ ] Create `src/agents/knowledge_agent.py` extending `BaseAgent`
- [ ] Implement FAQ lookup (keyword matching or semantic search)
- [ ] Handle "not found" cases gracefully
- [ ] Write unit tests in `tests/test_agents/test_knowledge_agent.py`

**Validation**: Test with various FAQ queries

**Files to Create**:
- `src/agents/knowledge_agent.py`
- `tests/test_agents/test_knowledge_agent.py`

---

### **PHASE 2: Google Cloud Integration** (Day 3-4)

#### Step 2.1: Implement Google Gemini Model Client
**Goal**: Integrate Gemini for NLU and response generation

**Tasks**:
- [ ] Update `src/models/model_client.py` with actual Gemini implementation
- [ ] Use `google-generativeai` SDK
- [ ] Implement `generate()` method for text generation
- [ ] Implement `generate_structured()` for intent extraction
- [ ] Test with GCP project: `affable-zodiac-458801-b0`
- [ ] Write unit tests with mocked responses

**Validation**: Test Gemini API calls with simple prompts

**Files to Update**:
- `src/models/model_client.py`

---

#### Step 2.2: Implement NLU Agent
**Goal**: Build intent classification and entity extraction

**Tasks**:
- [ ] Create `src/agents/nlu_agent.py` extending `BaseAgent`
- [ ] Design prompt templates for intent classification:
  - Intents: `ScheduleAppointment`, `RescheduleAppointment`, `CancelAppointment`, `InfoQuery`, `FAQ`, `Other`
- [ ] Implement entity extraction (dates, times, doctor names, test types)
- [ ] Use Gemini via `ModelClient`
- [ ] Create structured output schema for intents
- [ ] Write comprehensive tests

**Validation**: Test with sample patient utterances

**Files to Create**:
- `src/agents/nlu_agent.py`
- `tests/test_agents/test_nlu_agent.py`

---

#### Step 2.3: Implement ASR Agent (Google Speech-to-Text)
**Goal**: Integrate speech recognition

**Tasks**:
- [ ] Create `src/integrations/google_speech.py`
- [ ] Use Google Cloud Speech-to-Text API
- [ ] Create `src/agents/asr_agent.py` extending `BaseAgent`
- [ ] Handle audio input (file or stream)
- [ ] Return transcribed text
- [ ] Add error handling for unclear audio
- [ ] Write tests with sample audio files

**Validation**: Test with recorded voice samples

**Files to Create**:
- `src/integrations/google_speech.py`
- `src/agents/asr_agent.py`
- `tests/test_agents/test_asr_agent.py`

---

#### Step 2.4: Implement TTS Agent
**Goal**: Integrate text-to-speech synthesis

**Tasks**:
- [ ] Create `src/agents/tts_agent.py` extending `BaseAgent`
- [ ] Use Google Cloud Text-to-Speech API (or gTTS for simplicity)
- [ ] Generate natural-sounding voice output
- [ ] Support streaming or file output
- [ ] Choose appropriate voice (friendly, professional)
- [ ] Write tests

**Validation**: Generate and play sample audio

**Files to Create**:
- `src/agents/tts_agent.py`
- `tests/test_agents/test_tts_agent.py`

---

### **PHASE 3: Dialogue Management** (Day 5-6)

#### Step 3.1: Implement Conversation State Management
**Goal**: Track dialogue context across turns

**Tasks**:
- [ ] Create `src/utils/conversation_state.py`
- [ ] Define `ConversationState` class:
  - Current intent
  - Patient ID (authenticated)
  - Conversation history (last N turns)
  - Slots filled (date, time, doctor, etc.)
  - Current step in multi-turn dialogue
- [ ] Implement state update methods
- [ ] Add state serialization (for logging)

**Validation**: Test state transitions for various dialogue flows

**Files to Create**:
- `src/utils/conversation_state.py`
- `tests/test_utils/test_conversation_state.py`

---

#### Step 3.2: Implement Dialogue Manager
**Goal**: Build central orchestrator for conversation flow

**Tasks**:
- [ ] Create `src/agents/dialogue_manager.py`
- [ ] Implement conversation loop:
  1. Receive user utterance (from ASR)
  2. Update conversation state
  3. Call NLU agent for intent
  4. Route to appropriate backend agent (Scheduling, Records, FAQ)
  5. Manage multi-turn dialogues (ask follow-up questions)
  6. Generate response (template or LLM)
  7. Return text to TTS
- [ ] Handle authentication flow (verify patient with DOB)
- [ ] Implement error recovery and fallback
- [ ] Add context switching (user changes topic mid-conversation)
- [ ] Write comprehensive dialogue flow tests

**Validation**: Test end-to-end conversation scenarios

**Files to Create**:
- `src/agents/dialogue_manager.py`
- `tests/test_agents/test_dialogue_manager.py`

---

#### Step 3.3: Implement Voice Workflow
**Goal**: Create workflow for complete voice interaction

**Tasks**:
- [ ] Create `src/orchestration/voice_workflow.py`
- [ ] Define workflow steps:
  1. Greet user
  2. Listen (ASR)
  3. Understand (NLU)
  4. Process (Dialogue Manager routes to agents)
  5. Respond (TTS)
  6. Loop until call ends
- [ ] Integrate with `WorkflowEngine`
- [ ] Add conversation logging to `run_storage`
- [ ] Implement graceful exit on goodbye or timeout

**Validation**: Run simulated voice conversations

**Files to Create**:
- `src/orchestration/voice_workflow.py`
- `tests/test_workflows/test_voice_workflow.py`

---

### **PHASE 3.5: Evaluation Harness** (Day 5) ✅ COMPLETE

#### Step 3.4: Build Evaluation Framework
**Goal**: Create systematic evaluation of conversation trajectories

**Why This Matters**:
You can't improve what you don't measure. MAS systems must be evaluated on end-to-end trajectories, not just individual components. This evaluation harness will help us:
- Verify correct behavior before the hackathon demo
- Debug failures quickly
- Measure system performance (accuracy, latency)

**Tasks**:
- [x] Create `tests/evaluation/test_scenarios.py` ✅
- [x] Define 13 scripted conversation scenarios (expanded from 8 to 13):
  1. **New appointment booking**
     - Input: "I need to schedule an appointment"
     - Expected: Successfully books appointment with correct slot
  2. **Reschedule appointment**
     - Input: "I need to change my appointment"
     - Expected: Successfully reschedules to new slot, frees old slot
  3. **Cancel appointment**
     - Input: "I need to cancel my appointment"
     - Expected: Successfully cancels, frees slot
  4. **Lab result query + follow-up scheduling**
     - Input: "What were my lab results?" → "Can I schedule a follow-up?"
     - Expected: Returns correct lab data, then books appointment
  5. **Clinic hours FAQ**
     - Input: "What are your hours?"
     - Expected: Returns correct clinic hours
  6. **Unrecognized patient**
     - Input: Wrong DOB for authentication
     - Expected: Graceful error, no PHI released
  7. **Unavailable time slot**
     - Input: Request appointment at unavailable time
     - Expected: Offers alternative times
  8. **Multi-turn dialogue**
     - Input: Incomplete information, system asks follow-up questions
     - Expected: Completes task after gathering all info
  9. **Multiple slot selection** (NEW)
     - Input: "Show me all available times for Dr. Singh"
     - Expected: Returns multiple slot options
  10. **Context switch FAQ to booking** (NEW)
     - Input: User switches from FAQ to appointment booking mid-conversation
     - Expected: System handles context transition smoothly
  11. **Incomplete booking info** (NEW)
     - Input: User provides appointment details across multiple turns
     - Expected: System collects all required info before booking
  12. **Invalid time request** (NEW)
     - Input: "I want an appointment at 11 PM"
     - Expected: Gracefully handles unavailable time, offers alternatives
  13. **Lab query with proactive followup** (NEW)
     - Input: Lab results query triggers automatic follow-up suggestion
     - Expected: Returns results + proactive follow-up offer

- [x] For each scenario, define: ✅
  - Input utterances (text for now, audio later)
  - Expected final outcome (appointment booked, correct data returned, etc.)
  - Assertions to verify correctness
- [x] Implement eval runner: ✅
  - `run_eval_scenario()` - Runs single scenario through dialogue manager
  - `run_eval_suite()` - Runs all scenarios
  - `run_eval_with_metrics()` - Runs with detailed metrics collection
- [x] Add eval metrics tracking: ✅
  - Success rate (% scenarios passing)
  - Average latency per scenario
  - Per-scenario pass/fail status
  - Error tracking for failed scenarios

**Validation**: ✅ All 13 scenarios passing (100% success rate)

**Files Created**:
- `tests/evaluation/test_scenarios.py` ✅
- `tests/evaluation/eval_runner.py` ✅
- `scripts/run_eval_demo.py` ✅ (demo script for metrics display)

**Output Format**: Simple report showing pass/fail for each scenario:
```
Evaluation Results:
  ✓ Scenario 1: New appointment booking (2.3s)
  ✓ Scenario 2: Reschedule appointment (1.8s)
  ✓ Scenario 3: Cancel appointment (1.5s)
  ✓ Scenario 4: Lab query + follow-up (3.2s)
  ✓ Scenario 5: Clinic hours FAQ (0.9s)
  ✗ Scenario 6: Unrecognized patient (FAILED: released PHI)

  Overall: 5/6 passing (83%)
  Average latency: 1.95s/turn
```

---

### **PHASE 4: Telephony Integration** (Day 7-8)

#### Step 4.1: Implement Twilio Integration (Basic)
**Goal**: Enable phone call interface

**Tasks**:
- [ ] Create `src/integrations/twilio_client.py`
- [ ] Set up Twilio webhook endpoint (Flask/FastAPI)
- [ ] Implement `/voice` endpoint to handle incoming calls
- [ ] Use Twilio `<Gather>` for speech input
- [ ] Use Twilio `<Say>` for TTS output (or play audio)
- [ ] Connect Twilio webhook to Dialogue Manager
- [ ] Handle call lifecycle (start, turns, end)

**Validation**: Make test calls to the system

**Files to Create**:
- `src/integrations/twilio_client.py`
- `src/cli/voice_server.py` (Flask/FastAPI app)

---

### **PHASE 5: Testing & Refinement** (Day 9-10)

#### Step 5.1: End-to-End Integration Tests
**Goal**: Validate complete user journeys

**Tasks**:
- [ ] Write integration tests for all 3 main use cases:
  - Appointment scheduling (new)
  - Appointment management (reschedule/cancel)
  - Medical information query
- [ ] Test multi-intent conversations (e.g., ask about lab results then schedule follow-up)
- [ ] Test error scenarios (unclear speech, unavailable slots, unrecognized patient)
- [ ] Test authentication flow
- [ ] Test graceful fallbacks

**Validation**: All use cases pass E2E tests

**Files to Create**:
- `tests/test_workflows/test_appointment_scheduling.py`
- `tests/test_workflows/test_appointment_management.py`
- `tests/test_workflows/test_info_query.py`

---

#### Step 5.2: PHI Protection Validation
**Goal**: Ensure patient privacy in all operations

**Tasks**:
- [ ] Implement `src/utils/phi_protection.py`
- [ ] Sanitize all logs (names, DOB, test results)
- [ ] Verify authentication before releasing sensitive info
- [ ] Test that unauthenticated callers get no PHI
- [ ] Add compliance notes to documentation

**Validation**: Review logs to ensure no PHI leakage

**Files to Create**:
- `src/utils/phi_protection.py`
- `tests/test_utils/test_phi_protection.py`

---

#### Step 5.3: Prompt Engineering & Response Quality
**Goal**: Refine LLM prompts for natural, accurate responses

**Tasks**:
- [ ] Optimize NLU prompts for intent classification accuracy
- [ ] Improve response generation prompts for friendliness and clarity
- [ ] Add few-shot examples where needed
- [ ] Test edge cases (ambiguous requests, unclear dates)
- [ ] Adjust tone and personality (friendly, professional, empathetic)

**Validation**: Test with diverse utterances, measure intent accuracy

---

### **PHASE 6: Demo Preparation** (Day 11-12)

#### Step 6.1: Demo Scenarios & Script
**Goal**: Prepare compelling demo

**Tasks**:
- [ ] Create demo script with 3 scenarios:
  1. Patient books new appointment
  2. Patient reschedules existing appointment
  3. Patient asks about lab results and books follow-up
- [ ] Populate mock data to support demo scenarios
- [ ] Practice demo flow
- [ ] Prepare fallback/backup plans

**Validation**: Rehearse demo multiple times

---

#### Step 6.2: Documentation & Presentation
**Goal**: Complete documentation and demo materials

**Tasks**:
- [ ] Update README.md with demo instructions
- [ ] Document architecture in presentation format
- [ ] Create demo video (optional)
- [ ] Prepare Q&A responses for judges
- [ ] Document future improvements

**Validation**: Documentation is clear and complete

---

## Configuration

### GCP Setup
```bash
# Set GCP project
export GOOGLE_CLOUD_PROJECT=affable-zodiac-458801-b0

# Authenticate
gcloud auth application-default login

# Enable APIs
gcloud services enable speech.googleapis.com
gcloud services enable texttospeech.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Environment Variables (`.env`)
```
GOOGLE_CLOUD_PROJECT=affable-zodiac-458801-b0
GOOGLE_API_KEY=<your-key>
TWILIO_ACCOUNT_SID=<optional>
TWILIO_AUTH_TOKEN=<optional>
```

## Development Commands

### Setup
```bash
cd /Users/dheeraj/Documents/Workspace/EMRFlow
source .venv/bin/activate
pip install -r requirements.txt
```

### Running Tests
```bash
# All tests
pytest tests/ -v

# Specific agent
pytest tests/test_agents/test_nlu_agent.py -v

# With coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Running Voice Workflow
```bash
# CLI mode (text simulation)
python -m src.cli.run_workflow run --mode text

# Voice mode (requires mic/speaker)
python -m src.cli.run_workflow run --mode voice

# Twilio server
python -m src.cli.voice_server
```

### Testing Individual Components
```bash
# Test ASR with audio file
python -m src.agents.asr_agent --audio sample.wav

# Test NLU with text
python -m src.agents.nlu_agent --text "I need to schedule an appointment"

# Test scheduling
python -m src.agents.scheduling_agent --test
```

## Important Design Principles

### Healthcare-Specific
- ✅ **PHI Protection**: Sanitize all logs, verify authentication
- ✅ **Patient Safety**: Never provide medical diagnosis, redirect to humans when appropriate
- ✅ **Compliance**: Design with HIPAA in mind (even for mock data)
- ✅ **Audit Trail**: Log all interactions for review
- ✅ **Graceful Fallback**: Always offer human assistance option

### Multi-Agent Architecture
- ✅ **Specialization**: Each agent has single responsibility
- ✅ **Explicit Orchestration**: Dialogue Manager controls flow
- ✅ **Clean Interfaces**: Agents communicate via defined APIs
- ✅ **State Management**: Conversation state tracks context
- ✅ **Error Isolation**: Agent failures don't crash system

### Observability & Logging (REQUIRED)
**Every conversation MUST be logged as a structured execution trace.** This is critical for:
- Debugging failures during development
- Demonstrating system behavior at hackathon
- Evaluating conversation quality
- Ensuring PHI protection compliance

**What to Log Per Conversation:**
1. **Call/Session ID**: Unique identifier for this conversation
2. **Turns**: For each turn, log:
   - Timestamp
   - User utterance (ASR output, PHI-sanitized)
   - NLU intent + entities extracted
   - Chosen backend agent (Scheduling/Records/Knowledge)
   - Agent action/result (e.g., "booked appointment A-123" or "returned 3 lab results")
   - Final response to user (TTS input, PHI-sanitized)
   - Latency (ms for this turn)
3. **Errors**: Any exceptions, warnings, or fallbacks triggered
4. **Metadata**: Patient ID (if authenticated), call duration, outcome (success/failure)

**Storage Format**: JSONL (JSON Lines) - one conversation per file
- Location: `runs/<session_id>.jsonl`
- Each line = one turn or event
- Example:
  ```json
  {"session_id": "sess_123", "timestamp": "2025-12-01T10:00:00Z", "event": "call_start"}
  {"session_id": "sess_123", "turn": 1, "utterance": "[REDACTED]", "intent": "ScheduleAppointment", "entities": {"date": "2025-12-10"}, "agent": "SchedulingAgent", "result": "booked_A-501", "latency_ms": 1234}
  {"session_id": "sess_123", "turn": 2, ...}
  {"session_id": "sess_123", "event": "call_end", "duration_s": 120, "outcome": "success"}
  ```

**PHI Sanitization**: Before logging, apply `_protect_phi()` to:
- Patient names → "[NAME]"
- DOB → "[DOB]"
- Specific test values → "[LAB_VALUE]"
- Phone numbers, addresses → "[CONTACT]"

**Usage**:
- During development: Inspect logs to debug conversation flow
- At hackathon: Show judges a sample conversation trace
- For evaluation: Parse logs to compute metrics (success rate, avg latency)

The `run_storage.py` module handles this. Every agent should call `run_storage.log_turn()` after each action.

### Conversation Design
- ✅ **Natural Tone**: Friendly, professional, empathetic
- ✅ **Confirmation**: Repeat critical info (dates, times)
- ✅ **Clarification**: Ask follow-ups when uncertain
- ✅ **Context Switching**: Handle topic changes gracefully
- ✅ **Multi-turn Dialogues**: Complete complex tasks in one call

## Key Decisions & Patterns from CodeFlow

### Applied Patterns
- **Model Abstraction**: `ModelClient` keeps agents provider-agnostic
- **Base Agent**: All agents extend `BaseAgent` with consistent interface
- **Workflow Orchestration**: `WorkflowEngine` manages sequential steps
- **Run Metadata**: All conversations logged for improvement
- **Configuration**: YAML-based config with env vars for secrets

### EMRFlow Enhancements
- **Conversation State**: Track dialogue context across turns
- **Multi-turn Handling**: Support complex conversations
- **Voice I/O**: ASR and TTS integration
- **Real-time Processing**: Low-latency requirements
- **Authentication Flow**: Verify patient before releasing PHI

## Handoff to OpenAI Codex

For specific implementation tasks, you can delegate to OpenAI Codex:
- Code generation for specific agents
- Prompt template creation
- Test case generation
- Data structure design

**When handing off**, provide:
1. Clear specification (input/output, behavior)
2. Reference to base classes (`BaseAgent`, etc.)
3. Example test cases
4. Expected validation criteria

## Progress Tracking

As we build each phase:
1. ✅ Mark completed tasks
2. 📝 Document blockers or issues
3. 🧪 Validate before moving to next step
4. 💾 Commit working code frequently

---

## 🎯 CURRENT STATUS (Updated: December 1, 2025)

### ✅ Completed Phases

**Day 1: Foundation & Auth Bug Fix** ✅
- Fixed critical auth bug (python-dateutil dependency)
- Implemented robust date parsing with multiple format support
- Created 6 comprehensive auth flow tests (all passing)
- Added detailed auth logging throughout the pipeline

**Day 2: Golden Flows** ✅
- E2E test for new appointment booking (PASSING)
- E2E test for appointment rescheduling (PASSING)
- E2E test for lab results query (PASSING)
- All 10/10 workflow tests passing

**Day 3: Trace Viewer** ✅
- Implemented `scripts/view_trace.py` for conversation log visualization
- Rich library integration with beautiful terminal formatting
- Support for viewing individual sessions or listing all conversations

**Day 4: Wow Flow - Lab Results + Proactive Follow-up** ✅
- Enhanced `ResponseGenerator` with `generate_info_response()` method
- Added `generate_proactive_followup()` for natural follow-up suggestions
- Integrated with Dialogue Manager InfoQuery routing
- Uses Gemini 2.5 Flash for natural language generation
- Keyword detection for follow-up triggers (elevated, recommend, etc.)

**Day 5: Evaluation Harness with Metrics** ✅
- Expanded test scenarios from 8 to 13 (5 new scenarios)
- Implemented `EvalMetrics` dataclass with success_rate and avg_latency
- Created `run_eval_with_metrics()` function for detailed metrics collection
- Implemented `print_eval_report()` with rich formatting (+ plain text fallback)
- Created `scripts/run_eval_demo.py` for demo purposes
- **All 13 scenarios passing (100% success rate)**

### 📊 Test Coverage
- **10/10 workflow tests passing** (6 auth + 3 golden + 1 voice)
- **13/13 evaluation scenarios passing** (100% success rate)
- **0 blockers or failures**

### 🚀 System Status
- Multi-agent architecture fully operational
- Dialogue Manager routing all 6 intent types correctly
- Voice pipeline working (Twilio → Flask → ASR → NLU → DM → Response → TTS)
- Gemini 2.5 Flash integrated for NLU and response generation
- Conversation logging with PHI protection operational
- Mock data layer complete (patients, schedules, FAQs)

### 🎬 Ready for Demo
The system is **100% ready for hackathon demo** with:
1. ✅ 3 golden flows fully functional (booking, reschedule, lab query)
2. ✅ Wow factor feature (proactive follow-up suggestion)
3. ✅ Comprehensive evaluation metrics (100% pass rate)
4. ✅ Conversation trace viewer for debugging/demo
5. ✅ Clean architecture with 7 specialized agents
6. ✅ All tests passing

### 📝 Remaining Optional Enhancements
- Demo script documentation (for presentation)
- Rich library installation for colorized eval reports
- Practice live Twilio call demos

---

## Next Steps

**CURRENT FOCUS**: Demo preparation and documentation

The core system is complete and validated. Focus is now on:
1. Creating demo script documentation
2. Practicing live demo flows
3. Preparing presentation materials

## Questions & Clarifications

Before starting implementation, confirm:
- [ ] GCP credentials configured?
- [ ] Twilio account available (or using web UI)?
- [ ] Voice samples for ASR testing?
- [ ] Demo timeline and deadline?

---

**Ready to build!** Start with Phase 1, Step 1.1. We'll validate each step before proceeding.
