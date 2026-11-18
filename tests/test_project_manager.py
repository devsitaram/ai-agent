"""Tests for ProjectManager."""

import json
import os
import tempfile
from pathlib import Path

import pytest
from core.project_manager import ProjectManager
from schema import ProjectState


@pytest.fixture
def temp_output_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestProjectManager:
    """Test ProjectManager class."""

    def test_initialization(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        assert pm.output_dir == Path(temp_output_dir)
        assert pm.output_dir.exists()

    def test_create_project(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Build a calculator app", "Calculator App")
        
        assert project.project_name == "Calculator App"
        assert project.user_input == "Build a calculator app"
        assert project.project_id is not None
        assert project.project_path is not None
        
        # Check project directory was created
        project_dir = Path(project.project_path)
        assert project_dir.exists()
        
        # Check state file was saved
        state_file = project_dir / "project_state.json"
        assert state_file.exists()
        
        # Verify state file contents
        with open(state_file) as f:
            data = json.load(f)
            assert data["project_name"] == "Calculator App"
            assert data["user_input"] == "Build a calculator app"

    def test_create_project_without_name(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Build a simple API")
        
        # Should auto-generate a name
        assert project.project_name != "Untitled Project"
        assert "Build" in project.project_name

    def test_save_and_load_state(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Test save/load", "Test")
        
        # Modify and save
        project.project_name = "Updated Name"
        pm.save_state(project)
        
        # Load from file
        loaded = pm.load_state(project.project_id)
        assert loaded is not None
        assert loaded.project_name == "Updated Name"
        assert loaded.user_input == "Test save/load"

    def test_load_nonexistent_project(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        loaded = pm.load_state("nonexistent-id")
        assert loaded is None

    def test_list_projects(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        
        # Create multiple projects
        pm.create_project("Project 1", "Alpha")
        pm.create_project("Project 2", "Beta")
        
        projects = pm.list_projects()
        assert len(projects) == 2
        
        # Check project data
        names = [p["name"] for p in projects]
        assert "Alpha" in names
        assert "Beta" in names

    def test_write_and_read_file(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("File test", "FileTest")
        
        # Write a file
        path = pm.write_file(project, "test/test.txt", "Hello World")
        assert Path(path).exists()
        
        # Read it back
        content = pm.read_file(project, "test/test.txt")
        assert content == "Hello World"
        
        # Try non-existent file
        content = pm.read_file(project, "nonexistent.txt")
        assert content is None

    def test_write_file_creates_directories(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Dir test", "DirTest")
        
        # Write file in nested directory structure
        path = pm.write_file(project, "a/b/c/deep.txt", "Nested file")
        assert Path(path).exists()
        
        # Verify content
        content = pm.read_file(project, "a/b/c/deep.txt")
        assert content == "Nested file"

    def test_get_project_path(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Path test", "PathTest")
        
        path = pm.get_project_path(project)
        assert path.exists()
        # Path should contain project name and partial project_id
        assert "PathTest" in str(path)
        assert project.project_id[:8] in str(path)

    def test_project_state_persistence(self, temp_output_dir):
        pm = ProjectManager(output_dir=temp_output_dir)
        project = pm.create_project("Persistence test", "Persist")
        
        # Simulate updating agent results
        from schema import AgentResult, AgentStatus
        project.set_agent_result(
            "requirement",
            AgentResult(status=AgentStatus.COMPLETED, output="Done")
        )
        pm.save_state(project)
        
        # Reload and verify
        loaded = pm.load_state(project.project_id)
        assert loaded is not None
        
        req_result = loaded.get_agent_result("requirement")
        assert req_result.status == AgentStatus.COMPLETED
        assert req_result.output == "Done"
