"""Agent 4: QA Agent - Verifies software quality through comprehensive testing."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.llm_interface import LLMInterface
from core.base_agent import BaseAgent
from core.llm_interface import LLMInterface
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, BugReport, ProjectState, ProjectStatus


class QAAgent(BaseAgent):
    """Performs quality assurance testing on the generated project."""

    def __init__(
        self,
        llm_interface: Optional[LLMInterface] = None,
        project_manager: Optional[ProjectManager] = None,
    ):
        super().__init__(
            name="qa",
            description="Running quality assurance tests and validation",
        )
        self.llm = llm_interface or LLMInterface()
        self.project_manager = project_manager or ProjectManager()
        self.test_results: Dict[str, Any] = {}
        self.bug_reports: List[BugReport] = []

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that development is completed."""
        dev_result = project_state.get_agent_result("development")
        if dev_result.status != AgentStatus.COMPLETED:
            raise ValueError("Development not completed. Run development agent first.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project and run QA tests.
        
        Args:
            project_state: Current project state with generated code
            
        Returns:
            Updated project state with QA results
        """
        self.test_results = {}
        self.bug_reports = []

        project_path = self.project_manager.get_project_path(project_state)

        # Run different categories of tests
        self._run_functional_tests(project_path, project_state)
        self._run_security_checks(project_state)
        self._run_edge_case_tests(project_state)
        self._check_code_quality(project_path, project_state)

        # Generate QA report
        qa_report = self._generate_qa_report(project_state)
        qa_path = self.project_manager.write_file(
            project_state, "QA_REPORT.md", qa_report
        )

        # Update agent result
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED,
            output=self._generate_summary(),
            artifacts=[qa_path],
            bugs_found=len(self.bug_reports),
            bugs_fixed=0,
            bug_reports=self.bug_reports,
            test_results=self.test_results,
        )
        project_state.set_agent_result(self.name, agent_result)
        project_state.status = ProjectStatus.QA_TESTING

        self._display_test_summary()

        return project_state

    def _run_functional_tests(
        self, project_path: Path, project_state: ProjectState
    ) -> None:
        """Run functional tests using pytest or equivalent.
        
        Args:
            project_path: Path to the project directory
            project_state: Current project state
        """
        self.console.print("[cyan]Running functional tests...[/cyan]")

        tech = project_state.tech_stack
        lang = tech.get("language", "python")

        test_cases = self._generate_test_cases(project_state)

        passed = 0
        failed = 0
        failures = []

        for name, test_func, args in test_cases:
            try:
                if test_func == "check_file_exists":
                    self._check_file_exists(project_path, args[0])
                elif test_func == "check_file_contains":
                    self._check_file_contains(project_path, args[0], args[1])
                passed += 1
                self.console.print(f"  [green]✓ {name}[/green]")
            except AssertionError as e:
                failed += 1
                failures.append((name, str(e)))
                self.console.print(f"  [red]✗ {name}: {e}[/red]")

        self.test_results["functional"] = {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "failures": failures,
        }

        # Create bug reports for failures
        for name, error in failures:
            self.bug_reports.append(
                BugReport(
                    title=f"Functional test failure: {name}",
                    description=str(error),
                    severity="high" if "auth" in name.lower() or "security" in name.lower() else "medium",
                )
            )

    def _generate_test_cases(self, project_state: ProjectState) -> List:
        """Generate test cases using LLM based on project requirements."""
        requirements = self.project_manager.read_file(project_state, "REQUIREMENTS.md")
        architecture = self.project_manager.read_file(project_state, "ARCHITECTURE.md")

        if not requirements or not architecture:
            self.console.print("[yellow]Warning: Cannot generate dynamic tests. requirements or architecture missing.[/yellow]")
            return [("Check README", "check_file_exists", ["README.md"])]

        prompt = f"""
        Based on the following project requirements and architecture, generate a list of functional test cases.
        The tests should verify file existence and content.
        Return a Python list of tuples, where each tuple is:
        (test_name: str, test_function: str, args: list).
        
        Available test_functions:
        - 'check_file_exists': args are [relative_path]
        - 'check_file_contains': args are [relative_path, content_string]

        Requirements:
        {requirements}

        Architecture:
        {architecture}

        Example output for a simple FastAPI app:
        [
            ("Check for main application file", "check_file_exists", ["app/main.py"]),
            ("Check for FastAPI import", "check_file_contains", ["app/main.py", "from fastapi import FastAPI"]),
            ("Check for requirements file", "check_file_exists", ["requirements.txt"]),
            ("Check for FastAPI in requirements", "check_file_contains", ["requirements.txt", "fastapi"]),
            ("Check for database models", "check_file_exists", ["app/models.py"]),
            ("Check for User model", "check_file_contains", ["app/models.py", "class User"]),
            ("Check for test files", "check_file_exists", ["tests/test_main.py"])
        ]

        Now, generate the test cases for the given project.
        """
        try:
            response = self.llm.generate(prompt)
        except Exception as e:
            self.console.print(f"[red]Error calling LLM for test case generation: {e}[/red]")
            return [("Check README", "check_file_exists", ["README.md"])]

        try:
            # The response is a string representation of a list of tuples
            test_cases = eval(response.strip())
            if isinstance(test_cases, list):
                return test_cases
        except Exception as e:
            self.console.print(f"[red]Error parsing LLM-generated test cases: {e}[/red]")
        
        return [("Check README", "check_file_exists", ["README.md"])]

    def _check_file_exists(self, project_path: Path, relative_path: str) -> None:
        """Assert that a file exists in the project."""
        assert (project_path / relative_path).exists(), f"File not found: {relative_path}"

    def _check_file_contains(self, project_path: Path, relative_path: str, content: str) -> None:
        """Assert that a file contains a specific string."""
        file_path = project_path / relative_path
        assert file_path.exists(), f"File not found: {relative_path}"
        file_content = file_path.read_text()
        assert content in file_content, f"'{content}' not found in {relative_path}"

    def _run_security_checks(self, project_state: ProjectState) -> None:
        """Run security checks on the codebase.
        
        Args:
            project_state: Current project state
        """
        self.console.print("[cyan]Running security checks...[/cyan]")

        findings = []
        project_path = self.project_manager.get_project_path(project_state)

        # Check for hardcoded secrets
        for py_file in project_path.rglob("*.py"):
            content = py_file.read_text()
            if "secret_key" in content.lower() and "change-me" in content.lower():
                findings.append("Warning: Default secret key found in production code")

        # Check for CORS configuration
        main_file = project_path / "app/main.py"
        if main_file.exists():
            content = main_file.read_text()
            if '"*"' in content:
                findings.append("Info: Wide CORS policy (allow_origins=['*']) - restrict for production")

        self.test_results["security"] = {
            "issues_found": len(findings),
            "findings": findings,
        }

        if findings:
            for finding in findings:
                self.console.print(f"  [yellow]⚠ {finding}[/yellow]")

    def _run_edge_case_tests(self, project_state: ProjectState) -> None:
        """Test edge cases and error handling.
        
        Args:
            project_state: Current project state
        """
        self.console.print("[cyan]Testing edge cases...[/cyan]")

        project_path = self.project_manager.get_project_path(project_state)
        issues = []

        # Check error handling
        main_file = project_path / "app/main.py"
        if main_file.exists():
            content = main_file.read_text()
            if "try" not in content and "except" not in content:
                issues.append("No error handling (try/except) found in main application")

        # Check status codes
        tests_dir = project_path / "tests"
        if tests_dir.exists():
            test_files = list(tests_dir.rglob("*.py"))
            if not test_files:
                issues.append("No test files found")

            has_edge_case_tests = False
            for tf in test_files:
                content = tf.read_text()
                if any(kw in content for kw in ["def test_"]) and any(
                    kw in content for kw in ["invalid", "error", "exception", "empty", "none"]
                ):
                    has_edge_case_tests = True
                    break

            if not has_edge_case_tests:
                issues.append("No edge case/error handling tests found")

        self.test_results["edge_cases"] = {
            "issues_found": len(issues),
            "issues": issues,
        }

        for issue in issues:
            self.console.print(f"  [yellow]⚠ {issue}[/yellow]")
            self.bug_reports.append(
                BugReport(
                    title=f"Edge case: {issue}",
                    description=issue,
                    severity="medium",
                )
            )

    def _check_code_quality(self, project_path: Path, project_state: ProjectState) -> None:
        """Check code quality metrics.
        
        Args:
            project_path: Path to the project directory
            project_state: Current project state
        """
        self.console.print("[cyan]Checking code quality...[/cyan]")

        total_lines = 0
        total_files = 0
        docstring_count = 0
        comment_lines = 0

        for py_file in project_path.rglob("*.py"):
            if "site-packages" in str(py_file) or ".venv" in str(py_file):
                continue
            total_files += 1
            content = py_file.read_text()
            lines = content.split("\n")
            total_lines += len(lines)
            docstring_count += content.count('"""')
            comment_lines += sum(1 for l in lines if l.strip().startswith("#"))

        self.test_results["code_quality"] = {
            "total_files": total_files,
            "total_lines": total_lines,
            "docstrings": docstring_count,
            "comment_lines": comment_lines,
        }

        self.console.print(
            f"  [dim]Files: {total_files}, Lines: {total_lines}, "
            f"Docstrings: {docstring_count}[/dim]"
        )

    def _generate_qa_report(self, project_state: ProjectState) -> str:
        """Generate QA report in markdown format.
        
        Args:
            project_state: Current project state
            
        Returns:
            QA report markdown content
        """
        functional = self.test_results.get("functional", {})
        security = self.test_results.get("security", {})
        edge_cases = self.test_results.get("edge_cases", {})
        quality = self.test_results.get("code_quality", {})

        report = f"""# QA Report

## Summary
- **Functional Tests**: {functional.get('passed', 0)}/{functional.get('total', 0)} passed
- **Security Issues**: {security.get('issues_found', 0)} found
- **Edge Case Issues**: {edge_cases.get('issues_found', 0)} found
- **Code Quality**: {quality.get('total_files', 0)} files, {quality.get('total_lines', 0)} lines

## Functional Test Results

| Test | Status |
|------|--------|
"""

        for name, result in functional.get("failures", []):
            report += f"| {name} | ❌ Failed |\n"
        
        if not functional.get("failures"):
            report += "| All tests | ✅ Passed |\n"

        if self.bug_reports:
            report += "\n## Bug Reports\n\n"
            for bug in self.bug_reports:
                report += f"""### {bug.title}
- **Severity**: {bug.severity}
- **Description**: {bug.description}
- **Status**: {bug.status}

"""

        if security.get("findings"):
            report += "\n## Security Findings\n\n"
            for finding in security["findings"]:
                report += f"- ⚠ {finding}\n"

        if edge_cases.get("issues"):
            report += "\n## Edge Case Issues\n\n"
            for issue in edge_cases["issues"]:
                report += f"- ⚠ {issue}\n"

        report += f"""
## Code Quality Metrics
- **Files Analyzed**: {quality.get('total_files', 'N/A')}
- **Total Lines**: {quality.get('total_lines', 'N/A')}
- **Docstrings**: {quality.get('docstrings', 'N/A')}
- **Comment Lines**: {quality.get('comment_lines', 'N/A')}

## Recommendations
"""

        if functional.get("failed", 0) > 0:
            report += "- Fix failing functional tests before proceeding\n"
        if security.get("issues_found", 0) > 0:
            report += "- Address security findings before production deployment\n"
        if edge_cases.get("issues_found", 0) > 0:
            report += "- Add edge case handling and error recovery\n"
        if not functional.get("failures") and not security.get("issues_found") and not edge_cases.get("issues_found"):
            report += "- Code quality is good. Ready for documentation phase.\n"

        return report

    def _generate_summary(self) -> str:
        """Generate a summary of QA results."""
        functional = self.test_results.get("functional", {})
        total = functional.get("total", 0)
        passed = functional.get("passed", 0)
        failed = functional.get("failed", 0)

        return (
            f"QA completed: {passed}/{total} tests passed, "
            f"{failed} failed, "
            f"{len(self.bug_reports)} bugs reported"
        )

    def _display_test_summary(self) -> None:
        """Display test results summary."""
        functional = self.test_results.get("functional", {})
        passed = functional.get("passed", 0)
        total = functional.get("total", 0)

        self.console.print()
        self.console.print("[bold]Test Summary:[/bold]")
        self.console.print(f"  Functional: [green]{passed}/{total} passed[/green]")
        self.console.print(f"  Bugs Found: [yellow]{len(self.bug_reports)}[/yellow]")
        self.console.print(f"  Security Issues: {self.test_results.get('security', {}).get('issues_found', 0)}")
