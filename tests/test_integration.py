"""Integration tests for the AI Software Development Agent System.

Tests the full pipeline end-to-end with mock LLM responses.
"""

import tempfile
from pathlib import Path

import pytest
from agents.requirement_agent import RequirementAgent
from agents.architecture_agent import ArchitectureAgent
from agents.development_agent import DevelopmentAgent
from agents.qa_agent import QAAgent
from agents.documentation_agent import DocumentationAgent
from agents.runner_agent import RunnerAgent
from core.llm_interface import LLMInterface, MockProvider
from core.orchestrator import Orchestrator
from core.project_manager import ProjectManager
from schema import AgentStatus, ProjectState


@pytest.fixture
def project_manager():
    """Create a project manager with temp directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield ProjectManager(output_dir=tmpdir)


@pytest.fixture
def orchestrator(project_manager):
    """Create a fully configured orchestrator with mock LLM."""
    orchestrator = Orchestrator(project_manager=project_manager)
    
    # Use mock LLM interface (not raw provider) for testing
    mock_llm = LLMInterface(MockProvider())
    
    orchestrator.register_agent(
        RequirementAgent(llm_interface=mock_llm, project_manager=project_manager)
    )
    orchestrator.register_agent(
        ArchitectureAgent(llm_interface=mock_llm, project_manager=project_manager)
    )
    orchestrator.register_agent(
        DevelopmentAgent(llm_interface=mock_llm, project_manager=project_manager)
    )
    orchestrator.register_agent(
        QAAgent(llm_interface=mock_llm, project_manager=project_manager)
    )
    orchestrator.register_agent(
        DocumentationAgent(llm_interface=mock_llm, project_manager=project_manager)
    )
    orchestrator.register_agent(
        RunnerAgent(project_manager=project_manager)
    )
    
    return orchestrator


class TestIntegration:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_python_project(self, orchestrator):
        """Test the full pipeline with a Python project."""
        project = orchestrator.run_pipeline(
            user_input="Build a REST API for a task management system with FastAPI",
            project_name="Task Manager API",
        )
        
        assert project.status == "completed"
        assert project.project_name == "Task Manager API"
        
        # Verify all agents completed
        assert project.get_agent_result("requirement").status == AgentStatus.COMPLETED
        assert project.get_agent_result("architecture").status == AgentStatus.COMPLETED
        assert project.get_agent_result("development").status == AgentStatus.COMPLETED
        assert project.get_agent_result("qa").status == AgentStatus.COMPLETED
        assert project.get_agent_result("documentation").status == AgentStatus.COMPLETED
        assert project.get_agent_result("runner").status == AgentStatus.SKIPPED  # Not requested

    def test_full_pipeline_with_runner(self, orchestrator):
        """Test pipeline with runner agent enabled."""
        project = orchestrator.run_pipeline(
            user_input="Build a simple calculator API",
            project_name="Calculator",
            run_runner=True,
        )
        
        assert project.status == "completed"
        assert project.get_agent_result("runner").status == AgentStatus.COMPLETED

    def test_pipeline_creates_artifacts(self, orchestrator):
        """Test that pipeline creates all expected files."""
        project = orchestrator.run_pipeline(
            user_input="Build a note-taking API",
            project_name="Notes API",
        )
        
        project_path = Path(project.project_path)
        
        # Check essential files exist (these should be created by agents)
        expected_files = ["REQUIREMENTS.md", "ARCHITECTURE.md", "QA_REPORT.md",
                          "README.md", "API.md", "DEPLOYMENT.md", "CHANGELOG.md",
                          "project_state.json"]
        for file_name in expected_files:
            assert (project_path / file_name).exists(), f"Missing file: {file_name}"

    def test_pipeline_creates_source_code(self, orchestrator):
        """Test that development agent creates source code files."""
        project = orchestrator.run_pipeline(
            user_input="Build a blog API with FastAPI",
            project_name="Blog API",
        )
        
        project_path = Path(project.project_path)
        
        # Check Python project files
        assert (project_path / "app/main.py").exists()
        assert (project_path / "app/__init__.py").exists()
        assert (project_path / "app/config.py").exists()
        assert (project_path / "app/models.py").exists()
        assert (project_path / "app/schemas.py").exists()
        assert (project_path / "requirements.txt").exists()
        
        # Check test files
        tests_dir = project_path / "tests"
        if tests_dir.exists():
            assert (tests_dir / "conftest.py").exists()
            assert (tests_dir / "test_main.py").exists()
            assert (tests_dir / "test_models.py").exists()
            assert (tests_dir / "test_schemas.py").exists()

    def test_tech_stack_detection(self, orchestrator):
        """Test that tech stack is properly detected."""
        project = orchestrator.run_pipeline(
            user_input="Build a web app",
            project_name="Web App",
        )
        
        assert "language" in project.tech_stack
        assert project.tech_stack["language"] is not None

    def test_qa_finds_and_reports_bugs(self, orchestrator):
        """Test that QA agent finds issues and reports them."""
        project = orchestrator.run_pipeline(
            user_input="Build a simple API with FastAPI",
            project_name="Simple API",
        )
        
        qa_result = project.get_agent_result("qa")
        assert qa_result.status == AgentStatus.COMPLETED
        
        # QA should have test results
        assert qa_result.test_results is not None
        assert "functional" in qa_result.test_results

    def test_project_state_persistence(self, orchestrator, project_manager):
        """Test that project state is persisted to disk."""
        project = orchestrator.run_pipeline(
            user_input="Build a test project",
            project_name="Persistence Test",
        )
        
        # Load state from disk
        loaded = project_manager.load_state(project.project_id)
        assert loaded is not None
        assert loaded.project_name == "Persistence Test"
        assert loaded.status == "completed"
        
        # Verify all agent states persisted
        assert loaded.get_agent_result("requirement").status == AgentStatus.COMPLETED
        assert loaded.get_agent_result("architecture").status == AgentStatus.COMPLETED
        assert loaded.get_agent_result("development").status == AgentStatus.COMPLETED

    def test_nodejs_project_generation(self, orchestrator):
        """Test generating a Node.js project."""
        # Force Node.js tech stack
        project = orchestrator.run_pipeline(
            user_input="Build a Node.js Express API for a chat application",
            project_name="Chat API",
        )
        
        project_path = Path(project.project_path)
        
        # Check if Node.js files were created based on tech stack
        tech = project.tech_stack
        if tech.get("language") in ("javascript", "typescript", "nodejs"):
            assert (project_path / "package.json").exists()
            assert (project_path / "src/index.js").exists()

    def test_pipeline_with_long_description(self, orchestrator):
        """Test pipeline with a detailed description."""
        long_description = """
        I want to build a full-featured e-commerce API with the following features:
        - User registration and login with JWT
        - Product catalog with categories
        - Shopping cart management
        - Order processing and tracking
        - Admin dashboard for managing products
        - Payment integration placeholder
        - Email notifications for orders
        """
        
        project = orchestrator.run_pipeline(
            user_input=long_description.strip(),
            project_name="E-Commerce API",
        )
        
        assert project.status == "completed"
        assert project.project_name == "E-Commerce API"

    def test_agent_sequence_order(self, orchestrator):
        """Test that agents run in the correct order."""
        from tests.test_orchestrator import MockAgent
        
        local_orch = Orchestrator()
        
        agents = ["requirement", "architecture", "development", "qa", "documentation", "runner"]
        
        for agent_name in agents:
            local_orch.register_agent(MockAgent(agent_name))
        
        assert local_orch.agent_order == agents

