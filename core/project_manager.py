"""Project state management and persistence."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from schema import ProjectState, ProjectStatus


class ProjectManager:
    """Manages project state persistence and file operations."""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_project(self, user_input: str, project_name: str = "") -> ProjectState:
        """Create a new project with initial state.
        
        Args:
            user_input: The user's project description
            project_name: Optional project name
            
        Returns:
            New ProjectState instance
        """
        if not project_name:
            # Generate name from first few words of input
            words = user_input.strip().split()[:5]
            project_name = " ".join(words).title()
            # Clean filename
            project_name = "".join(c for c in project_name if c.isalnum() or c in " -_")
            project_name = project_name[:50]

        project = ProjectState(
            project_name=project_name or "Untitled Project",
            user_input=user_input,
            status=ProjectStatus.CREATED,
        )

        # Create project directory using project name (sanitized)
        safe_name = "".join(c for c in project.project_name if c.isalnum() or c in " -_").strip().replace(" ", "_")
        if not safe_name:
            safe_name = project.project_id
        project_dir = self.output_dir / f"{safe_name}_{project.project_id[:8]}"
        project_dir.mkdir(parents=True, exist_ok=True)
        project.project_path = str(project_dir)

        # Save initial state
        self.save_state(project)

        return project

    def save_state(self, project: ProjectState) -> None:
        """Save project state to JSON file.
        
        Args:
            project: Project state to save
        """
        if project.project_path:
            state_path = Path(project.project_path) / "project_state.json"
            with open(state_path, "w") as f:
                json.dump(project.to_dict(), f, indent=2, default=str)

    def load_state(self, project_id: str) -> Optional[ProjectState]:
        """Load project state from JSON file.
        
        Args:
            project_id: The project ID
            
        Returns:
            ProjectState if found, None otherwise
        """
        # Search all project directories for matching project_id
        if self.output_dir.exists():
            for project_dir in self.output_dir.iterdir():
                if project_dir.is_dir():
                    state_path = project_dir / "project_state.json"
                    if state_path.exists():
                        with open(state_path) as f:
                            data = json.load(f)
                            if data.get("project_id") == project_id:
                                return ProjectState.from_dict(data)
        return None

    def list_projects(self) -> list[Dict[str, Any]]:
        """List all projects with basic info.
        
        Returns:
            List of project summaries
        """
        projects = []
        if self.output_dir.exists():
            for project_dir in self.output_dir.iterdir():
                if project_dir.is_dir():
                    state_path = project_dir / "project_state.json"
                    if state_path.exists():
                        with open(state_path) as f:
                            data = json.load(f)
                            projects.append(
                                {
                                    "id": data.get("project_id", ""),
                                    "name": data.get("project_name", ""),
                                    "status": data.get("status", ""),
                                    "created": data.get("created_at", ""),
                                }
                            )
        return sorted(projects, key=lambda p: p.get("created", ""), reverse=True)

    def write_file(self, project: ProjectState, relative_path: str, content: str) -> str:
        """Write a file to the project directory.
        
        Args:
            project: Project state
            relative_path: Path relative to project directory
            content: File content
            
        Returns:
            Absolute path to the written file
        """
        if not project.project_path:
            raise ValueError("Project has no path set")

        file_path = Path(project.project_path) / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            f.write(content)

        return str(file_path)

    def read_file(self, project: ProjectState, relative_path: str) -> Optional[str]:
        """Read a file from the project directory.
        
        Args:
            project: Project state
            relative_path: Path relative to project directory
            
        Returns:
            File content if exists, None otherwise
        """
        if not project.project_path:
            return None

        file_path = Path(project.project_path) / relative_path
        if file_path.exists():
            with open(file_path) as f:
                return f.read()

        return None

    def get_project_path(self, project: ProjectState) -> Path:
        """Get the project directory path.
        
        Args:
            project: Project state
            
        Returns:
            Path object for project directory
        """
        return Path(project.project_path) if project.project_path else self.output_dir
