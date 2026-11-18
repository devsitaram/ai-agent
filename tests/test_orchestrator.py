"""Tests for the Orchestrator."""

from unittest.mock import MagicMock, patch

import pytest
from core.orchestrator import Orchestrator
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, ProjectState


class MockAgent:
    """Mock agent for testing."""
    
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.description = f"Mock {name} agent"
        self.should_fail = should_fail
        self.console = MagicMock()
    
    def run(self, project_state: ProjectState) -> ProjectState:
        result = AgentResult(
            status=AgentStatus.FAILED if self.should_fail else AgentStatus.COMPLETED,
            output=f"{self.name} completed",
            artifacts=[],
        )
        if self.should_fail:
            result.error = f"{self.name} failed"
        project_state.set_agent_result(self.name, result)
        return project_state


class TestOrchestrator:
    """Test Orchestrator class."""

    def test_initialization(self):
        orchestrator = Orchestrator()
        assert orchestrator.agents == {}
        assert orchestrator.agent_order == []

    def test_register_agent(self):
        orchestrator = Orchestrator()
        agent = MockAgent("test-agent")
        
        orchestrator.register_agent(agent)
        
        assert "test-agent" in orchestrator.agents
        assert "test-agent" in orchestrator.agent_order

    def test_register_multiple_agents(self):
        orchestrator = Orchestrator()
        
        agent1 = MockAgent("agent-1")
        agent2 = MockAgent("agent-2")
        agent3 = MockAgent("agent-3")
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)
        
        assert len(orchestrator.agents) == 3
        assert orchestrator.agent_order == ["agent-1", "agent-2", "agent-3"]

    def test_register_agent_with_order(self):
        orchestrator = Orchestrator()
        
        agent1 = MockAgent("first")
        agent2 = MockAgent("second")
        agent3 = MockAgent("third")
        
        orchestrator.register_agent(agent1, order=0)
        orchestrator.register_agent(agent2, order=2)
        orchestrator.register_agent(agent3, order=1)
        
        # Should be: first, third, second
        assert orchestrator.agent_order[0] == "first"
        assert orchestrator.agent_order[1] == "third"
        assert orchestrator.agent_order[2] == "second"

    @patch('core.orchestrator.ProjectManager')
    def test_run_pipeline_success(self, mock_pm_class):
        # Setup
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        
        orchestrator = Orchestrator(project_manager=mock_pm)
        
        agent1 = MockAgent("agent-1")
        agent2 = MockAgent("agent-2")
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        
        # Create initial project state
        mock_pm.create_project.return_value = ProjectState(
            user_input="Test project",
            project_name="Test",
            project_path="/tmp/test",
        )
        
        # Run pipeline
        project = orchestrator.run_pipeline("Test project", "Test")
        
        assert project.status == "completed"
        assert project.get_agent_result("agent-1").status == AgentStatus.COMPLETED
        assert project.get_agent_result("agent-2").status == AgentStatus.COMPLETED

    @patch('core.orchestrator.ProjectManager')
    def test_run_pipeline_agent_failure(self, mock_pm_class):
        # Setup
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        
        orchestrator = Orchestrator(project_manager=mock_pm)
        
        agent1 = MockAgent("agent-1")
        agent2 = MockAgent("agent-2", should_fail=True)
        agent3 = MockAgent("agent-3")
        
        orchestrator.register_agent(agent1)
        orchestrator.register_agent(agent2)
        orchestrator.register_agent(agent3)
        
        mock_pm.create_project.return_value = ProjectState(
            user_input="Test project",
            project_name="Test",
            project_path="/tmp/test",
        )
        
        # Run pipeline - should stop at agent-2
        project = orchestrator.run_pipeline("Test project", "Test")
        
        assert project.status == "failed"
        assert project.get_agent_result("agent-1").status == AgentStatus.COMPLETED
        assert project.get_agent_result("agent-2").status == AgentStatus.FAILED
        assert project.get_agent_result("agent-3").status == AgentStatus.PENDING

    @patch('core.orchestrator.ProjectManager')
    def test_run_single_agent(self, mock_pm_class):
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        
        orchestrator = Orchestrator(project_manager=mock_pm)
        agent = MockAgent("test-agent")
        orchestrator.register_agent(agent)
        
        project = ProjectState(user_input="Test", project_path="/tmp/test")
        
        result = orchestrator.run_single_agent(project, "test-agent")
        
        assert result.get_agent_result("test-agent").status == AgentStatus.COMPLETED

    @patch('core.orchestrator.ProjectManager')
    def test_run_single_agent_not_found(self, mock_pm_class):
        mock_pm = MagicMock()
        mock_pm_class.return_value = mock_pm
        
        orchestrator = Orchestrator(project_manager=mock_pm)
        project = ProjectState(user_input="Test")
        
        # Should not raise an error
        result = orchestrator.run_single_agent(project, "nonexistent")
        assert result == project

    def test_qa_loop_handling(self):
        """Test that QA loop is triggered when bugs are found."""
        orchestrator = Orchestrator()
        
        # Create a dev agent that always fixes bugs
        dev_agent = MockAgent("development")
        qa_agent = MockAgent("qa")
        
        orchestrator.register_agent(dev_agent)
        orchestrator.register_agent(qa_agent)
        
        # We'd need more complex setup for full QA loop testing
        # This tests the basic structure
        assert "development" in orchestrator.agents
        assert "qa" in orchestrator.agents
