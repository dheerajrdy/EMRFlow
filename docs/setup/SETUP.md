# EMRFlow Setup Guide

## What's Been Created

EMRFlow is now scaffolded with a solid foundation based on **CodeFlow learnings**. Here's what you have:

### Project Structure
```
EMRFlow/
├── src/
│   ├── agents/              # Agent implementations
│   │   └── base_agent.py   # Base agent abstraction ✅
│   ├── orchestration/       # Workflow orchestration
│   │   ├── workflow_context.py    # Shared context ✅
│   │   └── workflow_engine.py     # Workflow runner ✅
│   ├── models/              # LLM abstraction
│   │   └── model_client.py        # Model client interface ✅
│   ├── storage/             # Run metadata storage
│   │   └── run_storage.py         # JSONL storage ✅
│   ├── integrations/        # External service integrations
│   └── cli/                 # CLI interface
│       └── run_workflow.py        # CLI commands ✅
├── tests/                   # Test suite
│   └── test_base_components.py    # Basic tests ✅
├── docs/design/             # Design documentation
├── runs/                    # Workflow run logs
├── config/                  # Configuration
│   └── config.template.yaml       # Config template ✅
├── .venv/                   # Virtual environment ✅
├── README.md                # Project overview ✅
├── CLAUDE.md                # Claude Code instructions ✅
├── .gitignore              # Git ignore rules ✅
└── requirements.txt         # Python dependencies ✅
```

### Core Components Built

#### 1. **Model Abstraction** (`src/models/model_client.py`)
- Provider-agnostic LLM interface
- Google Cloud (Gemini) implementation stub
- Structured output support
- Ready to implement actual API calls

#### 2. **Base Agent** (`src/agents/base_agent.py`)
- Standardized agent interface
- AgentResult for consistent outputs
- PHI protection helpers
- Retry logic with backoff
- Error handling patterns

#### 3. **Workflow System** (`src/orchestration/`)
- `WorkflowContext`: Shared state across steps
- `WorkflowEngine`: Sequential orchestration with retry logic
- `WorkflowStep`: Base class for workflow steps
- Conditional execution support
- Timeout handling

#### 4. **Storage** (`src/storage/run_storage.py`)
- JSONL-based run metadata storage
- Run retrieval and listing
- Statistics aggregation
- Ready for SQLite upgrade if needed

#### 5. **CLI** (`src/cli/run_workflow.py`)
- Command-line interface with Click
- Run workflows, list runs, show run details
- Statistics command
- Dry-run mode support

#### 6. **Testing** (`tests/`)
- Pytest setup
- Mock implementations for testing
- Basic component tests

### Key Patterns from CodeFlow Applied

✅ **Role-specialized agents** - BaseAgent provides clear interface
✅ **Explicit orchestration** - WorkflowEngine controls flow
✅ **Model abstraction** - ModelClient keeps agents provider-agnostic
✅ **Observability** - Run storage tracks everything
✅ **Healthcare-specific** - PHI protection built-in

## Next Steps

### 1. Activate Environment & Install Dependencies

```bash
cd /Users/dheeraj/Documents/Workspace/EMRFlow

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Project

```bash
# Copy config template
cp config/config.template.yaml config/config.yaml

# Edit config with your settings
# Set up environment variables for GCP credentials
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

### 3. Define Healthcare Use Case

Now you need to:
1. **Define the specific healthcare workflow** you want to automate
2. **Design the agents** needed for your use case
3. **Map out workflow steps**
4. **Identify external integrations** (EMR systems, FHIR servers, etc.)

### 4. Implement First Agent

Example - create a new agent in `src/agents/`:

```python
from src.agents.base_agent import BaseAgent, AgentResult
from typing import Dict, Any

class HealthcareAgent(BaseAgent):
    """Agent for specific healthcare task."""

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        # Validate input
        self._validate_input(input_data)

        # Use model client
        response = await self.model.generate(
            prompt=f"Healthcare task: {input_data}",
            system_prompt="You are a healthcare workflow assistant..."
        )

        # Return result
        return self._create_success_result(
            output={"result": response.content}
        )
```

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### 6. Start Development

```bash
# Run CLI (once workflow is implemented)
python -m src.cli.run_workflow run --help

# List runs
python -m src.cli.run_workflow list-runs

# Show statistics
python -m src.cli.run_workflow stats
```

## Healthcare Use Case Template

To help define your use case, consider:

### Use Case: [Name]
**Goal**: What healthcare workflow are you automating?

**Inputs**: What data/triggers start the workflow?
- Patient data?
- Medical records?
- External events?

**Agents Needed**:
1. **[Agent 1]**: Responsibility
2. **[Agent 2]**: Responsibility
3. **[Agent 3]**: Responsibility

**Workflow Steps**:
```
Step1 → Step2 → Step3 → ...
```

**External Integrations**:
- EMR system?
- FHIR server?
- Billing system?
- Notification service?

**Outputs**: What does the workflow produce?
- Updated records?
- Reports?
- Notifications?

**Compliance Requirements**:
- HIPAA considerations?
- Audit trail needs?
- PHI handling rules?

## Development Workflow

1. **Define use case** (see template above)
2. **Create agents** in `src/agents/`
3. **Define workflow steps** in `src/orchestration/`
4. **Build integrations** in `src/integrations/`
5. **Wire up CLI** in `src/cli/run_workflow.py`
6. **Test** with dry-run mode
7. **Iterate** based on run metadata

## Resources

- **CodeFlow**: `/Users/dheeraj/Documents/Workspace/codeflow` - Reference implementation
- **CLAUDE.md**: Development guidelines and architecture patterns
- **Config Template**: `config/config.template.yaml` - Configuration options

## Support

For questions about:
- **Architecture**: See CLAUDE.md and CodeFlow project
- **Multi-agent patterns**: CodeFlow docs/design/design.md
- **Healthcare compliance**: Build into agent implementations

## Ready to Build!

The foundation is solid. Now define your healthcare use case and start building agents!

What healthcare workflow do you want to automate?
