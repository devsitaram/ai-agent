"""Tests for schema models."""

import pytest
from schema import (
    AgentResult,
    AgentStatus,
    BugReport,
    ProjectState,
    ProjectStatus,
)


class TestAgentStatus:
    """Test AgentStatus enum."""

    def test_values(self):
        assert AgentStatus.PENDING == "pending"
        assert AgentStatus.RUNNING == "running"
        assert AgentStatus.COMPLETED == "completed"
        assert AgentStatus.FAILED == "failed"
        assert AgentStatus.SKIPPED == "skipped"


class TestProjectStatus:
    """Test ProjectStatus enum."""

    def test_values(self):
        assert ProjectStatus.CREATED == "created"
        assert ProjectStatus.COMPLETED == "completed"
        assert ProjectStatus.FAILED == "failed"
        assert ProjectStatus.QA_LOOP == "qa_loop"


class TestBugReport:
    """Test BugReport model."""

    def test_create_bug_report(self):
        bug = BugReport(
            title="Test bug",
            description="This is a test bug",
            severity="high",
        )
        assert bug.title == "Test bug"
        assert bug.description == "This is a test bug"
        assert bug.severity == "high"
        assert bug.status == "open"
        assert bug.id is not None

    def test_default_values(self):
        bug = BugReport(title="Minimal bug", description="Minimal")
        assert bug.severity == "medium"
        assert bug.status == "open"
        assert bug.file_path is None
        assert bug.line_number is None


class TestAgentResult:
    """Test AgentResult model."""

    def test_default_values(self):
        result = AgentResult()
        assert result.status == AgentStatus.PENDING
        assert result.output == ""
        assert result.artifacts == []
        assert result.error is None
        assert result.bugs_found == 0
        assert result.bugs_fixed == 0
        assert result.qa_loop_count == 0
        assert result.bug_reports == []
        assert result.test_results == {}

    def test_with_bugs(self):
        bugs = [
            BugReport(title="Bug 1", description="First bug"),
            BugReport(title="Bug 2", description="Second bug"),
        ]
        result = AgentResult(
            status=AgentStatus.COMPLETED,
            output="Found 2 bugs",
            bugs_found=2,
            bug_reports=bugs,
        )
        assert result.status == AgentStatus.COMPLETED
        assert result.bugs_found == 2
        assert len(result.bug_reports) == 2


class TestProjectState:
    """Test ProjectState model."""

    def test_default_values(self):
        project = ProjectState()
        assert project.project_id is not None
        assert project.project_name == "Untitled Project"
        assert project.status == ProjectStatus.CREATED
        assert project.user_input == ""
        assert project.tech_stack == {}

    def test_with_user_input(self):
        project = ProjectState(
            user_input="Build a todo app",
            project_name="Todo App",
        )
        assert project.user_input == "Build a todo app"
        assert project.project_name == "Todo App"

    def test_agent_result_access(self):
        project = ProjectState()
        
        # Test get_agent_result
        req_result = project.get_agent_result("requirement")
        assert req_result.status == AgentStatus.PENDING
        
        # Test set_agent_result
        new_result = AgentResult(status=AgentStatus.COMPLETED, output="Done")
        project.set_agent_result("requirement", new_result)
        
        req_result = project.get_agent_result("requirement")
        assert req_result.status == AgentStatus.COMPLETED
        assert req_result.output == "Done"

    def test_to_dict_and_from_dict(self):
        project = ProjectState(
            user_input="Test project",
            project_name="Test",
        )
        
        # Convert to dict
        data = project.to_dict()
        assert data["project_name"] == "Test"
        assert data["user_input"] == "Test project"
        
        # Convert back from dict
        restored = ProjectState.from_dict(data)
        assert restored.project_name == project.project_name
        assert restored.user_input == project.user_input
        assert restored.project_id == project.project_id

    def test_agent_results_in_dict(self):
        project = ProjectState()
        project.set_agent_result(
            "requirement",
            AgentResult(status=AgentStatus.COMPLETED, output="Requirements done"),
        )
        
        data = project.to_dict()
        assert data["requirement_agent"]["status"] == "completed"
        assert data["requirement_agent"]["output"] == "Requirements done"
