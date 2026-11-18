# AI Software Development Agent System - Architecture

## 1. Technology Stack

### Core Language
- **Python 3.11+** - Primary implementation language
- **Type hints** throughout for type safety

### Key Libraries
- **openai** or **anthropic** - AI/LLM interaction (configurable)
- **rich** - Beautiful console output and progress display
- **pydantic** - Data validation and settings management
- **pyyaml** - Configuration file parsing
- **pathlib** - Modern file system operations
- **jinja2** - Template engine for code generation
- **pytest** - Test framework for QA agent
- **httpx** - HTTP client for API testing
- **json** - Configuration and data interchange

### Storage
- **File System** - Project files stored in organized directory structure
- **JSON/YAML** - Agent configuration and state files

## 2. Project Structure

```
ai-dev-agent/
├── main.py                          # Entry point
├── config.yaml                      # System configuration
├── schema.py                        # Pydantic models
├── requirements.txt                 # Dependencies
├── .env.example                     # Environment variables template
├── README.md                        # This file
├── ARCHITECTURE.md                  # Architecture document
├── REQUIREMENTS.md                  # Requirements document
│
├── core/
│   ├── __init__.py
│   ├── base_agent.py                # Abstract base agent class
│   ├── orchestrator.py              # Pipeline orchestration engine
│   ├── project_manager.py           # Project state management
│   └── llm_interface.py             # LLM provider abstraction
│
├── agents/
│   ├── __init__.py
│   ├── requirement_agent.py         # Agent 1: Requirement analysis
│   ├── architecture_agent.py        # Agent 2: Architecture design
│   ├── development_agent.py         # Agent 3: Code development
│   ├── qa_agent.py                  # Agent 4: Quality assurance
│   ├── documentation_agent.py       # Agent 5: Documentation
│   └── runner_agent.py              # Agent 6: Run/Deploy (optional)
│
├── templates/
│   ├── project_template.py          # Base project template
│   ├── python_backend/              # Python backend templates
│   │   ├── main.py.j2
│   │   ├── requirements.txt.j2
│   │   └── ...
│   ├── nodejs_backend/              # Node.js backend templates
│   │   └── ...
│   ├── web_frontend/                # Web frontend templates
│   │   └── ...
│   └── full_stack/                  # Full stack templates
│       └── ...
│
├── output/                          # Generated projects output
│   └── .gitkeep
│
└── tests/
    ├── __init__.py
    ├── test_base_agent.py
    ├── test_orchestrator.py
    ├── test_requirement_agent.py
    └── ...
```

## 3. Core Architecture

### Agent Pipeline Flow

```
                    ┌─────────────────┐
                    │   User Input    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Orchestrator   │
                    │  (Pipeline Mgr) │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
     ┌────────▼────────┐     │              │
     │  Project State  │     │              │
     │  (JSON Storage) │     │              │
     └─────────────────┘     │              │
                             │              │
                     ┌───────▼────────┐     │
                     │  Agent 1:      │     │
                     │  Requirement   │     │
                     └───────┬────────┘     │
                             │              │
                     ┌───────▼────────┐     │
                     │  Agent 2:      │     │
                     │  Architecture  │     │
                     └───────┬────────┘     │
                             │              │
                     ┌───────▼────────┐     │
                     │  Agent 3:      │     │
                     │  Development   │     │
                     └───────┬────────┘     │
                             │              │
                     ┌───────▼────────┐     │
               ┌─────│  Agent 4: QA   │     │
               │     └───────┬────────┘     │
               │             │              │
               │    ┌────────▼──────┐       │
               │    │   Tests Pass? │       │
               │    └───┬───────┬───┘       │
               │  No    │       │ Yes       │
               │    ┌───┘       └────┐      │
               │    │                │      │
               │    ▼                │      │
               │ (Back to Agent 3)   │      │
               │                     │     n│
               │             ┌───────▼───┐  │
               │             │  Agent 5: │  │
               │             │ Document. │  │
               │             └──────┬────┘  │
               │                    │       │
               │             ┌──────▼─────┐ │
               │             │  Agent 6:  │ │
               │             │  Runner    │ │
               │             └──────┬─────┘ │
               │                    │       │
               │             ┌──────▼───────▼┐
               │             │  Project      │
               │             │  Completed!   │
               │             └───────────────┘
```

### Agent Communication
- Agents communicate through **shared project state** (JSON files)
- Each agent reads previous agent's output and writes its own
- The orchestrator manages the sequence and handles failures

### State Management
- `project_state.json` contains all project metadata
- Each agent appends its results to the state
- The orchestrator can resume from any failed step

## 4. Database Design (for project state)

### Project State Schema
```json
{
  "project_id": "uuid",
  "project_name": "string",
  "created_at": "timestamp",
  "status": "string",
  "user_input": "string",
  "requirement_agent": {
    "status": "completed|failed|pending",
    "output": "REQUIREMENTS.md content",
    "artifacts": ["REQUIREMENTS.md"]
  },
  "architecture_agent": {
    "status": "completed|failed|pending",
    "output": "ARCHITECTURE.md content",
    "artifacts": ["ARCHITECTURE.md"]
  },
  "development_agent": {
    "status": "completed|failed|pending",
    "output": "Source code summary",
    "artifacts": ["source files..."]
  },
  "qa_agent": {
    "status": "completed|failed|pending",
    "output": "QA_REPORT.md content",
    "bugs_found": 0,
    "bugs_fixed": 0,
    "qa_loop_count": 0
  },
  "documentation_agent": {
    "status": "completed|failed|pending",
    "output": "Documentation summary",
    "artifacts": ["README.md", "API.md", ...]
  },
  "runner_agent": {
    "status": "completed|skipped|failed",
    "output": "Deployment info"
  }
}
```

## 5. API Design (System Internal API)

### Orchestrator API

| Method | Description |
|--------|-------------|
| `run_pipeline(user_input)` | Run the full agent pipeline |
| `run_agent(agent_name)` | Run a specific agent |
| `get_project_status(project_id)` | Get current project status |
| `resume_agent(agent_name)` | Resume from a failed agent |
| `run_qa_loop()` | Execute the QA feedback loop |

### Agent Interface

```python
class BaseAgent(ABC):
    @abstractmethod
    def process(self, project_state: dict) -> dict:
        """Process the project and return updated state"""
        pass
    
    @abstractmethod
    def validate(self, project_state: dict) -> bool:
        """Validate preconditions before processing"""
        pass
    
    def get_artifact_paths(self) -> list[str]:
        """Return paths of generated artifacts"""
        pass
```

## 6. UI Design

### Console UI (Phase 1)
- Rich-formatted terminal output
- Progress bars for each agent
- Color-coded status indicators
- Collapsible sections for detailed logs

### Web UI (Phase 2 - Future)
- Dashboard showing pipeline status
- File viewer for generated code
- Test results visualization
- Project configuration interface

## 7. Security

- Generated projects are stored in isolated directories
- No execution of generated code on the host system without user consent
- API keys stored in environment variables
- Input sanitization for all user-provided content
