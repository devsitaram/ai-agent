"""Abstract base class for all agents in the pipeline."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from schema import AgentResult, AgentStatus, ProjectState

console = Console()


class BaseAgent(ABC):
    """Abstract base class that all agents must implement."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.console = console

    @abstractmethod
    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project state and return updated state.
        
        Args:
            project_state: Current state of the project
            
        Returns:
            Updated project state with agent results
        """
        pass

    def validate(self, project_state: ProjectState) -> bool:
        """Validate preconditions before processing.
        
        Override in subclass if needed.
        
        Args:
            project_state: Current state of the project
            
        Returns:
            True if validation passes
        """
        return True

    def run(self, project_state: ProjectState) -> ProjectState:
        """Run the agent with progress display and error handling.
        
        Args:
            project_state: Current state of the project
            
        Returns:
            Updated project state
        """
        agent_result = project_state.get_agent_result(self.name)
        agent_result.status = AgentStatus.RUNNING
        agent_result.started_at = datetime.now().isoformat()

        self._display_header()

        try:
            # Validate preconditions
            if not self.validate(project_state):
                raise ValueError(f"Precondition validation failed for {self.name} agent")

            # Process
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Running {self.name} agent...", total=None
                )
                project_state = self.process(project_state)
                progress.update(task, completed=True)

            # Mark as completed
            agent_result = project_state.get_agent_result(self.name)
            agent_result.status = AgentStatus.COMPLETED
            agent_result.completed_at = datetime.now().isoformat()

            self._display_success()

        except Exception as e:
            agent_result = project_state.get_agent_result(self.name)
            agent_result.status = AgentStatus.FAILED
            agent_result.error = str(e)
            agent_result.completed_at = datetime.now().isoformat()
            self._display_error(e)

        return project_state

    def _display_header(self):
        """Display agent start header."""
        self.console.print()
        self.console.print(
            Panel(
                f"[bold yellow]🚀 {self.name.upper()} AGENT[/bold yellow]\n"
                f"[dim]{self.description}[/dim]",
                border_style="yellow",
            )
        )

    def _display_success(self):
        """Display agent completion message."""
        self.console.print(
            f"[bold green]✓ {self.name} agent completed successfully![/bold green]"
        )

    def _display_error(self, error: Exception):
        """Display agent error message."""
        self.console.print(
            f"[bold red]✗ {self.name} agent failed: {error}[/bold red]"
        )

    def get_artifact_paths(self, project_state: ProjectState) -> list[str]:
        """Return paths of generated artifacts.
        
        Override in subclass if needed.
        
        Args:
            project_state: Current state of the project
            
        Returns:
            List of artifact file paths
        """
        return project_state.get_agent_result(self.name).artifacts
