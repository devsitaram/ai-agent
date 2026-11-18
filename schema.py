"""Pydantic models for the AI Software Development Agent System."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ProjectStatus(str, Enum):
    CREATED = "created"
    REQUIREMENT_ANALYSIS = "requirement_analysis"
    ARCHITECTURE_DESIGN = "architecture_design"
    DEVELOPMENT = "development"
    QA_TESTING = "qa_testing"
    QA_LOOP = "qa_loop"
    DOCUMENTATION = "documentation"
    RUNNER = "runner"
    COMPLETED = "completed"
    FAILED = "failed"


class BugReport(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    severity: str = "medium"  # critical, high, medium, low
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    status: str = "open"  # open, fixed, verified


class AgentResult(BaseModel):
    status: AgentStatus = AgentStatus.PENDING
    output: str = ""
    artifacts: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    bugs_found: int = 0
    bugs_fixed: int = 0
    qa_loop_count: int = 0
    bug_reports: List[BugReport] = Field(default_factory=list)
    test_results: Dict[str, Any] = Field(default_factory=dict)


class ProjectState(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    project_name: str = "Untitled Project"
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    user_input: str = ""
    status: ProjectStatus = ProjectStatus.CREATED
    tech_stack: Dict[str, str] = Field(default_factory=dict)
    project_path: Optional[str] = None
    agent_results: Dict[str, AgentResult] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = self.model_dump()
        # Flatten agent_results into top-level for backwards compatibility
        for agent_name, result in self.agent_results.items():
            data[f"{agent_name}_agent"] = result.model_dump() if hasattr(result, 'model_dump') else result
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectState":
        # Extract agent results from data
        agent_results = {}
        known_agents = ["requirement", "architecture", "development", "qa", "documentation", "runner"]
        for agent_name in known_agents:
            field_key = f"{agent_name}_agent"
            if field_key in data:
                result_data = data.pop(field_key, {})
                if isinstance(result_data, dict):
                    agent_results[agent_name] = AgentResult(**result_data)
                elif isinstance(result_data, AgentResult):
                    agent_results[agent_name] = result_data

        # Pop any remaining agent_results to avoid conflict
        data.pop("agent_results", None)

        state = cls.model_validate(data)
        state.agent_results = agent_results
        return state

    def get_agent_result(self, agent_name: str) -> AgentResult:
        """Get agent result by name (e.g., 'requirement', 'qa').
        
        If the agent result doesn't exist yet, creates and stores a new one.
        """
        if agent_name not in self.agent_results:
            self.agent_results[agent_name] = AgentResult()
        return self.agent_results[agent_name]

    def set_agent_result(self, agent_name: str, result: AgentResult) -> None:
        """Set agent result by name (e.g., 'requirement', 'qa')."""
        self.agent_results[agent_name] = result

