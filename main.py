#!/usr/bin/env python3
"""
AI Software Development Agent System
An autonomous multi-agent platform that builds software projects from 
initial requirements to final deployment.

Usage:
    python main.py "Build a todo list app with FastAPI"
    python main.py --name "Todo App" "Build a todo list app with FastAPI"
    python main.py --run "Build a web scraper API"
    python main.py --list-projects
    python main.py --resume <project_id> --agent requirement
"""

from __future__ import annotations

import argparse
import sys
from typing import Dict, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from agents.requirement_agent import RequirementAgent
from agents.architecture_agent import ArchitectureAgent
from agents.development_agent import DevelopmentAgent
from agents.qa_agent import QAAgent
from agents.documentation_agent import DocumentationAgent
from agents.runner_agent import RunnerAgent
from core.orchestrator import Orchestrator
from core.project_manager import ProjectManager

console = Console()


def create_orchestrator() -> Orchestrator:
    """Create and configure the orchestrator with all agents.
    
    Returns:
        Configured Orchestrator instance
    """
    project_manager = ProjectManager()
    orchestrator = Orchestrator(project_manager)

    # Register agents in order
    orchestrator.register_agent(RequirementAgent(project_manager=project_manager))
    orchestrator.register_agent(ArchitectureAgent(project_manager=project_manager))
    orchestrator.register_agent(DevelopmentAgent(project_manager=project_manager))
    orchestrator.register_agent(QAAgent(project_manager=project_manager))
    orchestrator.register_agent(DocumentationAgent(project_manager=project_manager))
    orchestrator.register_agent(RunnerAgent(project_manager=project_manager))

    return orchestrator


def list_projects() -> None:
    """List all previously generated projects."""
    project_manager = ProjectManager()
    projects = project_manager.list_projects()

    if not projects:
        console.print("[yellow]No projects found yet.[/yellow]")
        return

    console.print(Panel("[bold cyan]Previous Projects[/bold cyan]", border_style="cyan"))
    for i, proj in enumerate(projects, 1):
        status_color = {
            "completed": "green",
            "failed": "red",
            "created": "yellow",
        }.get(proj.get("status", ""), "white")
        
        console.print(
            f"{i}. [bold]{proj.get('name', 'Unknown')}[/bold] "
            f"[dim](ID: {proj.get('id', '')[:8]}...)[/dim] "
            f"[{status_color}]{proj.get('status', 'unknown')}[/{status_color}]"
        )


def resume_project(project_id: str, agent_name: Optional[str] = None) -> None:
    """Resume a project from a specific agent.
    
    Args:
        project_id: Project ID to resume
        agent_name: Agent to resume from (optional)
    """
    project_manager = ProjectManager()
    project = project_manager.load_state(project_id)

    if not project:
        console.print(f"[bold red]Project with ID '{project_id}' not found.[/bold red]")
        return

    orchestrator = create_orchestrator()

    if agent_name:
        console.print(f"[cyan]Resuming project from {agent_name} agent...[/cyan]")
        orchestrator.run_single_agent(project, agent_name)
    else:
        console.print("[cyan]Resuming full pipeline...[/cyan]")
        # Continue from the last failed/pending agent
        agent_order = orchestrator.agent_order
        for agent_name in agent_order:
            agent_result = project.get_agent_result(agent_name)
            if agent_result.status in ("failed", "pending"):
                console.print(f"[cyan]Running {agent_name} agent...[/cyan]")
                orchestrator.run_single_agent(project, agent_name)


def interactive_mode() -> None:
    """Run the system in interactive mode with step-by-step prompts."""
    console.print(
        Panel.fit(
            "[bold yellow]🤖 AI Software Development Agent System[/bold yellow]\n\n"
            "[cyan]Welcome! I'll help you build a complete software project.[/cyan]\n"
            "[dim]Describe your project idea and I'll handle the rest.[/dim]",
            border_style="yellow",
        )
    )

    # Get project description
    console.print("\n[bold]Describe your project idea:[/bold]")
    console.print("[dim](What do you want to build? Be as specific as you'd like)[/dim]")
    user_input = Prompt.ask("\n[cyan]You[/cyan]")

    if not user_input.strip():
        console.print("[red]Please provide a project description.[/red]")
        return

    # Get optional project name
    project_name = Prompt.ask(
        "\n[cyan]Project name[/cyan]",
        default="",
    )

    # Ask about running the application
    run_app = Prompt.ask(
        "\n[cyan]Run the application after generation?[/cyan]",
        choices=["y", "n"],
        default="n",
    )

    # Create orchestrator and run pipeline
    orchestrator = create_orchestrator()

    console.print("\n[bold green]Starting pipeline...[/bold green]")
    project = orchestrator.run_pipeline(
        user_input=user_input,
        project_name=project_name,
        run_runner=run_app.lower() == "y",
    )

    # Show final instructions
    if project.status == "completed":
        console.print(
            Panel(
                "[bold green]✅ Project Generated Successfully![/bold green]\n\n"
                f"[bold]Project Location:[/bold] {project.project_path}\n\n"
                "[bold]Next Steps:[/bold]\n"
                "1. Navigate to the project directory\n"
                "2. Install dependencies: pip install -r requirements.txt\n"
                "3. Run the app: python -m app.main\n"
                "4. Open http://localhost:8000 in your browser\n"
                "5. View API docs at http://localhost:8000/docs",
                border_style="green",
                title="Success",
            )
        )
    else:
        console.print(
            Panel(
                f"[bold red]❌ Pipeline completed with status: {project.status}[/bold red]\n"
                "Check the output above for details.",
                border_style="red",
                title="Issues Detected",
            )
        )


def main():
    """Main entry point for the AI Software Development Agent System."""
    parser = argparse.ArgumentParser(
        description="AI Software Development Agent System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "Build a todo list app with FastAPI"
  python main.py --name "Todo App" "Build a todo list API"
  python main.py --list-projects
  python main.py --resume <project-id> --agent development
  python main.py --interactive
        """,
    )

    parser.add_argument(
        "description",
        nargs="?",
        help="Project description (omit for interactive mode)",
    )
    parser.add_argument(
        "--name",
        "-n",
        help="Project name",
        default="",
    )
    parser.add_argument(
        "--run",
        "-r",
        action="store_true",
        help="Run the runner/deployment agent after generation",
    )
    parser.add_argument(
        "--list-projects",
        "-l",
        action="store_true",
        help="List all generated projects",
    )
    parser.add_argument(
        "--resume",
        help="Resume a project by ID",
    )
    parser.add_argument(
        "--agent",
        "-a",
        help="Resume from a specific agent (used with --resume)",
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Run in interactive mode",
    )

    args = parser.parse_args()

    # Handle different modes
    if args.list_projects:
        list_projects()
        return

    if args.resume:
        resume_project(args.resume, args.agent)
        return

    if args.interactive or not args.description:
        interactive_mode()
        return

    # Direct mode with description
    orchestrator = create_orchestrator()
    
    console.print(
        Panel(
            f"[bold cyan]🤖 AI Development Agent[/bold cyan]\n"
            f"[dim]Building project:[/dim] {args.description[:100]}{'...' if len(args.description) > 100 else ''}",
            border_style="cyan",
        )
    )

    project = orchestrator.run_pipeline(
        user_input=args.description,
        project_name=args.name,
        run_runner=args.run,
    )

    # Final output
    if project.status == "completed":
        console.print(f"\n[bold green]✅ Project generated at: {project.project_path}[/bold green]")
    else:
        console.print(f"\n[bold red]❌ Pipeline failed with status: {project.status}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
