"""Pipeline orchestration engine that manages agent execution flow."""

from __future__ import annotations

from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.base_agent import BaseAgent
from core.project_manager import ProjectManager
from schema import AgentStatus, ProjectState, ProjectStatus

console = Console()


class Orchestrator:
    """Orchestrates the agent pipeline execution."""

    def __init__(self, project_manager: Optional[ProjectManager] = None):
        self.project_manager = project_manager or ProjectManager()
        self.agents: Dict[str, BaseAgent] = {}
        self.agent_order: list[str] = []

    def register_agent(self, agent: BaseAgent, order: int = 0) -> None:
        """Register an agent with the orchestrator.
        
        Args:
            agent: The agent instance to register
            order: Execution order (lower = earlier)
        """
        self.agents[agent.name] = agent
        if order == 0:
            # Auto-assign order based on registration sequence
            self.agent_order.append(agent.name)
        else:
            if order <= len(self.agent_order):
                self.agent_order.insert(order, agent.name)
            else:
                self.agent_order.append(agent.name)

    def run_pipeline(
        self,
        user_input: str,
        project_name: str = "",
        run_runner: bool = False,
    ) -> ProjectState:
        """Run the full agent pipeline.
        
        Args:
            user_input: User's project description
            project_name: Optional project name
            run_runner: Whether to run the runner agent
            
        Returns:
            Final project state
        """
        # Create project
        project = self.project_manager.create_project(user_input, project_name)
        project.status = ProjectStatus.REQUIREMENT_ANALYSIS

        self._display_pipeline_start(project)

        # Run agents in order
        for agent_name in self.agent_order:
            if agent_name == "runner" and not run_runner:
                console.print(
                    f"[dim]Skipping {agent_name} agent (not requested)[/dim]"
                )
                agent_result = project.get_agent_result(agent_name)
                agent_result.status = AgentStatus.SKIPPED
                continue

            if agent_name in self.agents:
                agent = self.agents[agent_name]
                project = agent.run(project)
                self.project_manager.save_state(project)

                # Check if agent failed
                agent_result = project.get_agent_result(agent_name)
                if agent_result.status == AgentStatus.FAILED:
                    project.status = ProjectStatus.FAILED
                    self.project_manager.save_state(project)
                    self._display_pipeline_failed(project, agent_name)
                    return project

                # Handle QA loop
                if agent_name == "qa" and agent_result.status == AgentStatus.COMPLETED:
                    project = self._handle_qa_loop(project)

                # Update project status
                self._update_project_status(project, agent_name)

        project.status = ProjectStatus.COMPLETED
        self.project_manager.save_state(project)
        self._display_pipeline_complete(project)

        return project

    def run_single_agent(self, project: ProjectState, agent_name: str) -> ProjectState:
        """Run a single agent on an existing project.
        
        Args:
            project: Current project state
            agent_name: Name of the agent to run
            
        Returns:
            Updated project state
        """
        if agent_name not in self.agents:
            console.print(f"[bold red]Agent '{agent_name}' not found[/bold red]")
            return project

        agent = self.agents[agent_name]
        project = agent.run(project)
        self.project_manager.save_state(project)

        return project

    def _handle_qa_loop(self, project: ProjectState) -> ProjectState:
        """Handle the QA feedback loop where bugs are sent back to development.
        
        Args:
            project: Current project state
            
        Returns:
            Updated project state after QA loop
        """
        qa_result = project.get_agent_result("qa")
        max_loops = 5

        loop_count = 0
        while (qa_result.bugs_found > qa_result.bugs_fixed 
               and loop_count < max_loops):
            loop_count += 1
            qa_result.qa_loop_count = loop_count
            project.status = ProjectStatus.QA_LOOP

            console.print(
                Panel(
                    f"[bold yellow]🔄 QA LOOP #{loop_count}[/bold yellow]\n"
                    f"Bugs found: {qa_result.bugs_found} | "
                    f"Bugs fixed: {qa_result.bugs_fixed}\n"
                    f"Sending issues back to Development Agent...",
                    border_style="yellow",
                )
            )

            # Run development agent again to fix bugs
            if "development" in self.agents:
                project = self.agents["development"].run(project)
                self.project_manager.save_state(project)

            # Run QA again to verify fixes
            if "qa" in self.agents:
                project = self.agents["qa"].run(project)
                self.project_manager.save_state(project)

            qa_result = project.get_agent_result("qa")

        if qa_result.bugs_found <= qa_result.bugs_fixed:
            console.print("[bold green]✓ All bugs resolved![/bold green]")
        else:
            console.print(
                f"[bold yellow]⚠ Max QA loops reached. "
                f"{qa_result.bugs_found - qa_result.bugs_fixed} bugs remaining.[/bold yellow]"
            )

        return project

    def _update_project_status(self, project: ProjectState, agent_name: str) -> None:
        """Update project status based on completed agent.
        
        Args:
            project: Project state
            agent_name: Name of completed agent
        """
        status_map = {
            "requirement": ProjectStatus.REQUIREMENT_ANALYSIS,
            "architecture": ProjectStatus.ARCHITECTURE_DESIGN,
            "development": ProjectStatus.DEVELOPMENT,
            "qa": ProjectStatus.QA_TESTING,
            "documentation": ProjectStatus.DOCUMENTATION,
            "runner": ProjectStatus.RUNNER,
        }
        if agent_name in status_map:
            project.status = status_map[agent_name]

    def _display_pipeline_start(self, project: ProjectState) -> None:
        """Display pipeline start banner."""
        console.print()
        console.print(
            Panel(
                "[bold green]🚀 AI Software Development Agent System[/bold green]\n\n"
                f"[bold]Project:[/bold] {project.project_name}\n"
                f"[bold]ID:[/bold] {project.project_id}\n"
                f"[bold]Pipeline Agents:[/bold] {', '.join(self.agent_order)}",
                border_style="green",
                title="Pipeline Started",
            )
        )

    def _display_pipeline_complete(self, project: ProjectState) -> None:
        """Display pipeline completion banner."""
        console.print()
        console.print(
            Panel(
                "[bold green]✅ PIPELINE COMPLETED SUCCESSFULLY![/bold green]\n\n"
                f"[bold]Project:[/bold] {project.project_name}\n"
                f"[bold]Location:[/bold] {project.project_path}",
                border_style="green",
                title="Project Complete",
            )
        )
        self._display_project_summary(project)

    def _display_pipeline_failed(self, project: ProjectState, agent_name: str) -> None:
        """Display pipeline failure message."""
        console.print(
            Panel(
                f"[bold red]❌ Pipeline failed at {agent_name} agent[/bold red]\n"
                f"Check the logs above for details.",
                border_style="red",
                title="Pipeline Failed",
            )
        )

    def _display_project_summary(self, project: ProjectState) -> None:
        """Display a summary table of the completed project."""
        table = Table(title="Project Summary", border_style="cyan")
        table.add_column("Agent", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        agents_info = [
            ("Requirement", project.get_agent_result("requirement")),
            ("Architecture", project.get_agent_result("architecture")),
            ("Development", project.get_agent_result("development")),
            ("QA", project.get_agent_result("qa")),
            ("Documentation", project.get_agent_result("documentation")),
            ("Runner", project.get_agent_result("runner")),
        ]

        for name, result in agents_info:
            status_str = {
                AgentStatus.COMPLETED: "[green]✓ Passed[/green]",
                AgentStatus.FAILED: "[red]✗ Failed[/red]",
                AgentStatus.RUNNING: "[yellow]⟳ Running[/yellow]",
                AgentStatus.PENDING: "[dim]◌ Pending[/dim]",
                AgentStatus.SKIPPED: "[dim]— Skipped[/dim]",
            }.get(result.status, "[dim]Unknown[/dim]")

            details = result.output[:50] + "..." if len(result.output) > 50 else result.output
            if name == "QA" and result.qa_loop_count > 0:
                details += f" ({result.qa_loop_count} loops)"

            table.add_row(name, status_str, details)

        console.print(table)
