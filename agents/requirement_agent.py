"""Agent 1: Requirement Agent - Analyzes user input and generates requirements."""

from __future__ import annotations

from typing import Optional

from core.base_agent import BaseAgent
from core.llm_interface import LLMInterface
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, ProjectState, ProjectStatus


class RequirementAgent(BaseAgent):
    """Analyzes user requirements and generates a comprehensive requirements specification."""

    def __init__(
        self,
        llm_interface: Optional[LLMInterface] = None,
        project_manager: Optional[ProjectManager] = None,
    ):
        super().__init__(
            name="requirement",
            description="Analyzing requirements and generating specification",
        )
        self.llm = llm_interface or LLMInterface()
        self.project_manager = project_manager or ProjectManager()

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that user input exists."""
        if not project_state.user_input:
            raise ValueError("No user input provided. Cannot analyze requirements.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project and generate requirements.
        
        Args:
            project_state: Current project state with user input
            
        Returns:
            Updated project state with requirements
        """
        user_input = project_state.user_input

        # Display analysis info
        self.console.print(f"[cyan]Analyzing:[/cyan] {user_input[:100]}...")

        # Generate requirements using LLM
        self.console.print("[dim]Generating requirements specification...[/dim]")
        try:
            requirements_content = self.llm.analyze_requirements(user_input)
        except Exception as e:
            self.console.print(f"[yellow]Warning: LLM call failed for requirements generation: {e}[/yellow]")
            self.console.print("[yellow]Using fallback to generate default requirements.[/yellow]")
            requirements_content = ""

        # Fallback content if LLM returns empty
        if not requirements_content.strip():
            requirements_content = self._generate_default_requirements(user_input)

        # Write REQUIREMENTS.md
        req_path = self.project_manager.write_file(
            project_state, "REQUIREMENTS.md", requirements_content
        )

        # Extract project name from user input if not set
        if project_state.project_name == "Untitled Project":
            words = user_input.strip().split()[:5]
            name = " ".join(words).title()
            project_state.project_name = "".join(
                c for c in name if c.isalnum() or c in " -_"
            )[:50]

        # Update agent result
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED,
            output=f"Requirements generated with {len(requirements_content)} characters",
            artifacts=[req_path],
        )
        project_state.set_agent_result(self.name, agent_result)
        project_state.status = ProjectStatus.REQUIREMENT_ANALYSIS

        self.console.print(f"[green]✓ Requirements saved to:[/green] {req_path}")

        return project_state

    def _generate_default_requirements(self, user_input: str) -> str:
        """Generate default requirements when LLM is unavailable.
        
        Args:
            user_input: The user's project description
            
        Returns:
            Basic requirements markdown
        """
        return f"""# Requirements Specification

## Project Overview
{user_input}

## Core Features
1. User authentication and authorization
2. Data management with CRUD operations
3. API endpoints for external access
4. Responsive user interface
5. Data persistence and storage

## Technical Requirements
- RESTful API architecture
- Relational database for data storage
- Input validation and sanitization
- Comprehensive error handling
- Unit and integration testing

## User Stories
- As a user, I can register an account and log in
- As a user, I can create, read, update, and delete data
- As a user, I can search and filter information
- As an administrator, I can manage user accounts
- As a developer, I can integrate with the API

## Development Milestones
1. **Phase 1**: Project setup, database design, authentication
2. **Phase 2**: Core CRUD operations and API endpoints
3. **Phase 3**: UI/UX implementation
4. **Phase 4**: Testing and quality assurance
5. **Phase 5**: Documentation and deployment
"""
