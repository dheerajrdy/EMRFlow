# CodeFlow Learnings Applied to EMRFlow

This document captures key learnings from the CodeFlow project and how they've been applied to EMRFlow.

## Architecture Patterns Reused

### 1. Model Abstraction Layer

**CodeFlow Pattern**:
- `ModelClient` interface keeps agents provider-agnostic
- Implementations for different LLM providers (Google, OpenAI, etc.)
- Standardized `ModelResponse` object

**Applied to EMRFlow**:
```python
# src/models/model_client.py
class ModelClient(ABC):
    @abstractmethod
    async def generate(self, prompt, ...): pass

    @abstractmethod
    async def generate_structured(self, prompt, schema, ...): pass
```

**Why**: Healthcare workflows may need to switch between models or use multiple models. The abstraction makes this seamless.

### 2. Base Agent Pattern

**CodeFlow Pattern**:
- All agents inherit from `BaseAgent`
- Standardized `execute()` method returning `AgentResult`
- Built-in retry logic, error handling, validation

**Applied to EMRFlow**:
```python
# src/agents/base_agent.py
class BaseAgent(ABC):
    async def execute(self, input_data: Dict) -> AgentResult:
        pass
```

**Enhancements for Healthcare**:
- Added `_protect_phi()` method for PHI sanitization
- Enhanced error handling for compliance
- Metadata tracking for audit trails

### 3. Workflow Orchestration

**CodeFlow Pattern**:
- Sequential workflow with explicit steps
- `WorkflowContext` passed through pipeline
- Conditional branching with `ConditionalStep`
- Retry logic per step

**Applied to EMRFlow**:
```python
# src/orchestration/workflow_engine.py
class WorkflowEngine:
    async def execute(self, context: WorkflowContext): pass

# src/orchestration/workflow_context.py
class WorkflowContext:
    workflow_id: str
    input_data: Dict
    step_results: Dict
    status: WorkflowStatus
```

**Why**: Healthcare workflows have strict requirements for:
- Audit trails (all steps must be logged)
- Error recovery (patient safety)
- Sequential processing (data dependencies)

### 4. Run Metadata & Learning

**CodeFlow Pattern**:
- All workflow runs stored in `runs/` directory
- JSONL format for simple storage
- Ability to list, view, and analyze runs
- Used for prompt iteration and improvement

**Applied to EMRFlow**:
```python
# src/storage/run_storage.py
class RunStorage(ABC):
    async def save_run(self, context: WorkflowContext): pass
    async def get_run(self, workflow_id: str): pass
    async def list_runs(self, ...): pass
```

**Healthcare Additions**:
- PHI protection in stored runs
- Compliance-focused metadata
- Audit trail completeness

## Key Improvements Over CodeFlow

### 1. Healthcare-Specific Considerations

**PHI Protection**:
- Built into base agent (`_protect_phi()`)
- Configurable in storage layer
- Never log PHI unless explicitly encrypted

**Compliance**:
- Audit trail for all operations
- Timestamps on all actions
- Error tracking for incident response

**Safety**:
- Human-in-loop for critical decisions
- Dry-run mode for testing
- Graceful degradation on errors

### 2. Enhanced Error Handling

**CodeFlow**: Basic retry with exponential backoff

**EMRFlow**:
- Configurable retry per step
- Healthcare-specific error categorization
- Never fail silently (patient safety)
- Complete error context for debugging

### 3. Storage Flexibility

**CodeFlow**: JSONL only

**EMRFlow**:
- Abstract `RunStorage` interface
- JSONL for development
- Easy upgrade to SQLite/PostgreSQL for production
- Designed for HIPAA-compliant storage options

## Workflow Comparison

### CodeFlow Workflow
```
FetchTicket → AnalyzeRepo → Design → Code → Test → Review → PR → Notes
```

**Pattern**: Software development automation
- Jira ticket as input
- GitHub PR as output
- Agents: Design, Coding, Review, Notes

### EMRFlow Workflow (Template)
```
[Input] → [Healthcare-specific steps] → [Output]
```

**Pattern**: Healthcare workflow automation
- Healthcare data as input (patient records, requests, etc.)
- Healthcare output (updated records, reports, actions)
- Agents: TBD based on use case

**Same Principles**:
- Sequential steps with retry logic
- Conditional branching where needed
- Metadata/notes agent for learning
- All runs tracked for improvement

## Configuration Pattern

### CodeFlow
```yaml
jira:
  base_url: "..."
  api_token_env: "JIRA_API_TOKEN"

github:
  org: "..."
  token_env: "GITHUB_TOKEN"

model:
  provider: "google"
  model_name: "gemini-pro"
```

### EMRFlow
```yaml
healthcare:
  # Integration configs (EMR, FHIR, etc.)
  phi_protection:
    enabled: true
    anonymize_logs: true

model:
  provider: "google"
  model_name: "gemini-1.5-pro"

workflow:
  max_retries: 2
  timeout_seconds: 300
```

**Same Pattern**: YAML-based config with environment variables for secrets

## Testing Approach

### CodeFlow
- Pytest for all tests
- Mock model clients for unit tests
- Integration tests with real APIs (optional)
- Evaluation set of "training" tickets

### EMRFlow (Same + Healthcare)
- Same pytest approach
- Mock model clients
- **Added**: Mock healthcare data (synthetic patients)
- **Added**: Compliance testing (PHI protection, audit trails)
- **Added**: Safety testing (error scenarios, fail-safes)

## CLI Pattern

Both use Click for CLI with similar commands:

```bash
# CodeFlow
python -m src.cli.run_workflow --ticket JIRA-123
python -m src.cli.run_workflow --list-runs

# EMRFlow
python -m src.cli.run_workflow run
python -m src.cli.run_workflow list-runs
python -m src.cli.run_workflow stats
```

**Same Benefits**:
- User-friendly CLI
- Dry-run mode
- Run inspection
- Statistics

## Code Organization

Both follow clean architecture:

```
src/
├── agents/          # Business logic (agents)
├── orchestration/   # Workflow control
├── integrations/    # External services
├── models/          # LLM abstraction
├── storage/         # Persistence
└── cli/             # User interface
```

**Principle**: Separation of concerns, testability, maintainability

## Development Workflow

### CodeFlow Process
1. Define agents for software dev workflow
2. Implement workflow steps
3. Test with example tickets
4. Iterate on prompts using run metadata
5. Evaluate with training set

### EMRFlow Process (Same Approach)
1. **Define healthcare use case** ← START HERE
2. Design agents for healthcare workflow
3. Implement workflow steps
4. Test with synthetic healthcare data
5. Iterate on prompts using run metadata
6. Evaluate with test cases
7. Add compliance validation

## What to Build Next

Based on CodeFlow learnings, here's the recommended order:

### Phase 1: Define & Design (Day 1-2)
- [ ] Define specific healthcare use case
- [ ] Design agent roles and responsibilities
- [ ] Map workflow steps
- [ ] Identify external integrations needed
- [ ] Create design document (like CodeFlow's design.md)

### Phase 2: Core Implementation (Day 3-4)
- [ ] Implement first agent (following BaseAgent pattern)
- [ ] Create workflow steps
- [ ] Implement model client (Google Cloud integration)
- [ ] Basic end-to-end workflow

### Phase 3: Integrations (Day 5)
- [ ] External healthcare system integrations
- [ ] Data transformation/validation
- [ ] Error handling and retry logic

### Phase 4: Compliance & Safety (Day 6)
- [ ] PHI protection implementation
- [ ] Audit logging
- [ ] Human-in-loop checkpoints
- [ ] Compliance testing

### Phase 5: Iteration (Ongoing)
- [ ] Run workflows, collect metadata
- [ ] Iterate on agent prompts
- [ ] Improve error handling
- [ ] Add monitoring/alerting

## Key Takeaways from CodeFlow

### What Worked Well
✅ Simple, sequential workflows (don't over-engineer)
✅ Model abstraction (easy to switch providers)
✅ Run metadata for learning (critical for improvement)
✅ CLI-first approach (fast iteration)
✅ Explicit orchestration (predictable, debuggable)

### What to Watch Out For
⚠️ Don't skip the design phase (define use case first)
⚠️ Start simple, add complexity as needed
⚠️ PHI protection must be built-in from day 1
⚠️ Test with synthetic data before real data
⚠️ Compliance is not optional in healthcare

## Resources

- **CodeFlow Project**: `/Users/dheeraj/Documents/Workspace/codeflow`
- **CodeFlow Design Doc**: `codeflow/docs/design/design.md`
- **Multi-Agent Patterns**: CodeFlow reference materials

## Questions to Answer Before Building

Before implementing EMRFlow agents, define:

1. **Use Case**: What healthcare workflow are we automating?
2. **Input**: What data triggers the workflow?
3. **Output**: What does the workflow produce?
4. **Agents**: What specialized roles do we need?
5. **Steps**: What's the sequence of operations?
6. **Integrations**: What external systems do we connect to?
7. **Compliance**: What are the HIPAA/PHI requirements?
8. **Safety**: What are the failure modes and safeguards?

**Next Step**: Define your healthcare use case, and we'll build the agents!
