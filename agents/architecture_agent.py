"""Agent 2: Architecture & Design Agent - Designs the technical architecture."""

from __future__ import annotations

from typing import Optional

from core.base_agent import BaseAgent
from core.llm_interface import LLMInterface
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, ProjectState, ProjectStatus


class ArchitectureAgent(BaseAgent):
    """Designs complete technical architecture based on requirements."""

    def __init__(
        self,
        llm_interface: Optional[LLMInterface] = None,
        project_manager: Optional[ProjectManager] = None,
    ):
        super().__init__(
            name="architecture",
            description="Designing system architecture and technical specifications",
        )
        self.llm = llm_interface or LLMInterface()
        self.project_manager = project_manager or ProjectManager()

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that requirements exist."""
        req_result = project_state.get_agent_result("requirement")
        if req_result.status != AgentStatus.COMPLETED:
            raise ValueError("Requirements not completed. Run requirement agent first.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project and generate architecture.
        
        Args:
            project_state: Current project state with requirements
            
        Returns:
            Updated project state with architecture
        """
        # Read requirements
        requirements = self.project_manager.read_file(project_state, "REQUIREMENTS.md")
        if not requirements:
            requirements = project_state.get_agent_result("requirement").output

        user_input = project_state.user_input

        # Generate architecture using LLM
        self.console.print("[dim]Designing architecture...[/dim]")
        try:
            architecture_content = self.llm.design_architecture(requirements, user_input)
        except Exception as e:
            self.console.print(f"[yellow]Warning: LLM call failed for architecture design: {e}[/yellow]")
            self.console.print("[yellow]Using fallback to generate default architecture.[/yellow]")
            architecture_content = ""

        # Fallback if LLM returns empty
        if not architecture_content.strip():
            architecture_content = self._generate_default_architecture(project_state)

        # Determine tech stack from architecture
        self._detect_tech_stack(project_state, architecture_content)

        # Write ARCHITECTURE.md
        arch_path = self.project_manager.write_file(
            project_state, "ARCHITECTURE.md", architecture_content
        )

        # Update agent result
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED,
            output=f"Architecture designed with {len(architecture_content)} characters",
            artifacts=[arch_path],
        )
        project_state.set_agent_result(self.name, agent_result)
        project_state.status = ProjectStatus.ARCHITECTURE_DESIGN

        self.console.print(f"[green]✓ Architecture saved to:[/green] {arch_path}")
        self._display_tech_stack(project_state.tech_stack)

        return project_state

    def _detect_tech_stack(self, project_state: ProjectState, architecture_content: str) -> None:
        """Extract technology stack from user input and architecture content.
        
        Args:
            project_state: Project state to update with tech stack
            architecture_content: Architecture document text
        """
        tech_stack = {}
        tech_markers = {
            "language": ["kotlin", "python", "javascript", "typescript", "java", "go", "rust", "ruby", "swift", "c#", "csharp", "php", "dart"],
            "backend": ["fastapi", "django", "flask", "express", "spring", "rails", "gin", "ktor", "actix"],
            "frontend": ["jetpack compose", "compose", "react", "vue", "angular", "svelte", "next.js", "nuxt", "swiftui"],
            "mobile": ["android", "ios", "flutter", "react native", "kotlin", "swift", "compose"],
            "database": ["postgresql", "mysql", "sqlite", "mongodb", "redis", "cassandra", "room"],
            "orm": ["sqlalchemy", "prisma", "typeorm", "django orm", "sequelize", "room"],
            "architecture": ["mvvm", "mvp", "mvc", "clean architecture", "clean arch", "viper", "tdd"],
            "di": ["dagger", "hilt", "koin", "spring", "guice"],
        }
        
        # Pass 1: Check user input for explicit tech choices
        user_input_lower = project_state.user_input.lower()
        for category, keywords in tech_markers.items():
            for keyword in keywords:
                if keyword in user_input_lower:
                    # Avoid 'compose' being both mobile and frontend if 'jetpack compose' is present
                    if keyword == 'compose' and 'jetpack compose' in user_input_lower:
                        continue
                    tech_stack[category] = keyword
                    break
        
        # Pass 2: Check architecture content for implicit choices
        content_lower = architecture_content.lower()
        for category, keywords in tech_markers.items():
            if category in tech_stack:  # Don't overwrite user's choice
                continue
            for keyword in keywords:
                if keyword in content_lower:
                    tech_stack[category] = keyword
                    break

        if not tech_stack:
            tech_stack = {
                "language": "python",
                "backend": "fastapi",
                "database": "sqlite",
                "orm": "sqlalchemy",
            }

        # Refine language based on other cues
        if "jetpack compose" in tech_stack.get("frontend", "") and "language" not in tech_stack:
            tech_stack["language"] = "kotlin"
        if "swiftui" in tech_stack.get("frontend", "") and "language" not in tech_stack:
            tech_stack["language"] = "swift"

        project_state.tech_stack = tech_stack

    def _display_tech_stack(self, tech_stack: dict) -> None:
        """Display detected technology stack."""
        if tech_stack:
            self.console.print("[bold cyan]Technology Stack:[/bold cyan]")
            for category, tech in tech_stack.items():
                self.console.print(f"  [dim]{category}:[/dim] [white]{tech}[/white]")

    def _generate_default_architecture(self, project_state: ProjectState) -> str:
        """Generate default architecture when LLM is unavailable.
        
        Args:
            project_state: Current project state
            
        Returns:
            Basic architecture markdown
        """
        tech = project_state.tech_stack or {
            "language": "python",
            "backend": "fastapi",
            "database": "sqlite",
        }

        return f"""# Architecture Design

## Technology Stack
- **Language**: {tech.get('language', 'python')}
- **Backend Framework**: {tech.get('backend', 'fastapi')}
- **Database**: {tech.get('database', 'sqlite')}
- **ORM**: {tech.get('orm', 'sqlalchemy')}

## Project Structure
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── config.py        # Configuration
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── routes/          # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── items.py
│   ├── services/        # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── item_service.py
│   └── templates/       # HTML templates (if applicable)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_items.py
├── requirements.txt
└── README.md
```

## Database Schema

### Users Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, Auto-increment |
| username | String(50) | UNIQUE, NOT NULL |
| email | String(100) | UNIQUE, NOT NULL |
| password_hash | String(255) | NOT NULL |
| created_at | DateTime | NOT NULL, DEFAULT NOW() |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() |

### Items Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, Auto-increment |
| user_id | Integer | FK -> users.id, NOT NULL |
| title | String(200) | NOT NULL |
| description | Text | NULLABLE |
| created_at | DateTime | NOT NULL, DEFAULT NOW() |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile

### Items CRUD
- `GET /api/items` - List all items (paginated)
- `POST /api/items` - Create new item
- `GET /api/items/{{id}}` - Get item by ID
- `PUT /api/items/{{id}}` - Update item
- `DELETE /api/items/{{id}}` - Delete item

## Authentication Flow
1. User registers with username, email, password
2. User logs in with credentials
3. Server returns JWT access token
4. Client includes token in Authorization header
5. Server validates token for protected routes
"""
