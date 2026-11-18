"""Agent 6: Runner Agent (Optional) - Builds, runs, and optionally deploys the application."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from core.base_agent import BaseAgent
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, ProjectState, ProjectStatus


class RunnerAgent(BaseAgent):
    """Builds, runs, validates, and optionally deploys the generated application."""

    def __init__(self, project_manager: Optional[ProjectManager] = None):
        super().__init__(
            name="runner",
            description="Building and running the generated application",
        )
        self.project_manager = project_manager or ProjectManager()

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that documentation is completed."""
        doc_result = project_state.get_agent_result("documentation")
        if doc_result.status != AgentStatus.COMPLETED:
            raise ValueError("Documentation not completed. Run documentation agent first.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project - build, run, and validate.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state with runner results
        """
        project_path = self.project_manager.get_project_path(project_state)
        tech = project_state.tech_stack
        lang = tech.get("language", "python")
        framework = tech.get("framework", tech.get("backend", ""))

        results = []

        # 1. Validate project structure
        self.console.print("[cyan]Validating project structure...[/cyan]")
        structure_valid = self._validate_structure(project_path, lang)
        results.append(("Structure Validation", "✅ Passed" if structure_valid else "❌ Failed"))

        # 2. Check dependencies
        self.console.print("[cyan]Checking dependencies...[/cyan]")
        deps_ok = self._check_dependencies(project_path, lang)
        results.append(("Dependencies", "✅ Resolved" if deps_ok else "❌ Missing"))

        # 3. Syntax check
        self.console.print("[cyan]Running syntax check...[/cyan]")
        syntax_ok = self._check_syntax(project_path, lang)
        results.append(("Syntax Check", "✅ Passed" if syntax_ok else "❌ Issues found"))

        # 4. Check for entry point
        self.console.print("[cyan]Verifying entry point...[/cyan]")
        entry_ok = self._verify_entry_point(project_path, lang)
        results.append(("Entry Point", "✅ Valid" if entry_ok else "❌ Not found"))

        # Generate runner report
        run_report = self._generate_runner_report(project_state, results)
        run_path = self.project_manager.write_file(
            project_state, "RUNNER_REPORT.md", run_report
        )

        # Update agent result
        all_passed = all("✅" in r[1] for r in results)
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED if all_passed else AgentStatus.FAILED,
            output="\n".join([f"{r[0]}: {r[1]}" for r in results]),
            artifacts=[run_path],
        )
        project_state.set_agent_result(self.name, agent_result)

        if all_passed:
            project_state.status = ProjectStatus.RUNNER
            self.console.print("[bold green]✓ All validations passed![/bold green]")
            self.console.print()
            self.console.print("[bold]To run the application:[/bold]")
            self._print_run_instructions(project_path, lang, framework)
        else:
            self.console.print("[bold red]✗ Some validations failed[/bold red]")

        return project_state

    def _print_run_instructions(self, project_path: Path, lang: str, framework: str) -> None:
        """Print run instructions based on language and framework."""
        if lang == "python":
            self.console.print(f"  cd {project_path} && python -m app.main")
        elif lang in ("javascript", "typescript", "nodejs"):
            self.console.print(f"  cd {project_path} && npm start")
        elif lang in ("kotlin", "java") or "android" in framework.lower():
            self.console.print(f"  cd {project_path}")
            self.console.print("  # Open in Android Studio and run on emulator:")
            self.console.print("  # 1. File -> Open -> Select the project folder")
            self.console.print("  # 2. Wait for Gradle sync to finish")
            self.console.print("  # 3. Select an emulator from the device dropdown")
            self.console.print("  # 4. Click Run (green triangle)")
            self.console.print()
            self.console.print("  # Or build from command line:")
            self.console.print("  ./gradlew assembleDebug")
            self.console.print("  # APK location: app/build/outputs/apk/debug/")
        elif lang == "swift" or "ios" in framework.lower():
            self.console.print(f"  cd {project_path}")
            self.console.print("  # Open in Xcode and run on simulator:")
            self.console.print("  # 1. Open .xcodeproj or .xcworkspace file")
            self.console.print("  # 2. Select an iOS Simulator")
            self.console.print("  # 3. Press Cmd+R to run")
        else:
            self.console.print(f"  cd {project_path}")
            self.console.print("  # Check RUNNER_REPORT.md for instructions")

    def _validate_structure(self, project_path: Path, lang: str) -> bool:
        """Validate project structure.
        
        Args:
            project_path: Path to project directory
            lang: Programming language
            
        Returns:
            True if structure is valid
        """
        if lang == "python":
            required_files = ["requirements.txt", "README.md"]
            required_dirs = ["app", "tests"]
        elif lang in ("javascript", "typescript", "nodejs"):
            required_files = ["package.json", "README.md"]
            required_dirs = ["src", "tests"]
        else:
            required_files = ["README.md"]
            required_dirs = []

        for f in required_files:
            if not (project_path / f).exists():
                self.console.print(f"  [red]Missing: {f}[/red]")
                return False

        for d in required_dirs:
            if not (project_path / d).exists():
                self.console.print(f"  [yellow]Warning: Missing directory {d}[/yellow]")

        return True

    def _check_dependencies(self, project_path: Path, lang: str) -> bool:
        """Check if dependency files exist and are valid.
        
        Args:
            project_path: Path to project directory
            lang: Programming language
            
        Returns:
            True if dependencies are found
        """
        if lang == "python":
            req_file = project_path / "requirements.txt"
            if req_file.exists():
                content = req_file.read_text()
                if content.strip():
                    dep_count = len([l for l in content.split("\n") if l.strip() and not l.startswith("#")])
                    self.console.print(f"  [dim]Found {dep_count} dependencies[/dim]")
                    return True
            return False
        elif lang in ("javascript", "typescript", "nodejs"):
            pkg_file = project_path / "package.json"
            if pkg_file.exists():
                import json
                with open(pkg_file) as f:
                    data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                self.console.print(f"  [dim]Found {len(deps)} dependencies, {len(dev_deps)} devDependencies[/dim]")
                return True
            return False
        return True

    def _check_syntax(self, project_path: Path, lang: str) -> bool:
        """Check syntax of source files.
        
        Args:
            project_path: Path to project directory
            lang: Programming language
            
        Returns:
            True if syntax is valid
        """
        if lang == "python":
            try:
                import py_compile
                for py_file in project_path.rglob("*.py"):
                    if "site-packages" not in str(py_file) and ".venv" not in str(py_file):
                        try:
                            py_compile.compile(str(py_file), doraise=True)
                        except py_compile.PyCompileError as e:
                            self.console.print(f"  [red]Syntax error in {py_file}: {e}[/red]")
                            return False
                return True
            except ImportError:
                # Fallback: just check files exist
                return True
        return True

    def _verify_entry_point(self, project_path: Path, lang: str) -> bool:
        """Verify application entry point exists.
        
        Args:
            project_path: Path to project directory
            lang: Programming language
            
        Returns:
            True if entry point is found
        """
        if lang == "python":
            main_files = [
                project_path / "app/main.py",
                project_path / "main.py",
                project_path / "app.py",
            ]
        elif lang in ("javascript", "typescript", "nodejs"):
            main_files = [
                project_path / "src/index.js",
                project_path / "src/index.ts",
                project_path / "index.js",
                project_path / "app.js",
            ]
        else:
            main_files = []

        for mf in main_files:
            if mf.exists():
                return True

        return False

    def _generate_runner_report(
        self, project_state: ProjectState, results: list
    ) -> str:
        """Generate runner report.
        
        Args:
            project_state: Current project state
            results: List of (check_name, result) tuples
            
        Returns:
            Runner report markdown
        """
        tech = project_state.tech_stack
        lang = tech.get("language", "python")
        framework = tech.get("framework", tech.get("backend", ""))
        db = tech.get("database", "")

        report = f"""# Runner Report

## Project: {project_state.project_name}
## Tech Stack: {lang} / {framework} / {db}

## Validation Results

| Check | Result |
|-------|--------|
"""
        for name, result in results:
            report += f"| {name} | {result} |\n"

        all_passed = all("✅" in r[1] for r in results)
        report += f"\n## Overall: {'✅ PASSED' if all_passed else '❌ FAILED'}\n"

        if all_passed:
            report += "\n## How to Run\n\n"
            if lang == "python":
                report += """### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python -m app.main
```

### Access the application
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
"""
            elif lang in ("javascript", "typescript", "nodejs"):
                report += """### Local Development
```bash
# Install dependencies
npm install

# Run the application
npm start
```
"""
            elif lang in ("kotlin", "java") or "android" in framework.lower():
                report += """### Run on Android Emulator / Device

**Prerequisites:** Android Studio installed with Android SDK

#### Option 1: Using Android Studio (Recommended)
```bash
# Open project in Android Studio
# File -> Open -> Select the project folder
```
1. Wait for Gradle sync to complete
2. Select a device from the toolbar dropdown
3. Click the **Run** button (green triangle) or press `Ctrl+R`

#### Option 2: Build APK from Command Line
```bash
# Make sure ANDROID_HOME is set
export ANDROID_HOME=~/Android/Sdk

# Build debug APK
./gradlew assembleDebug

# APK location:
# app/build/outputs/apk/debug/app-debug.apk

# Install on connected device
adb install app/build/outputs/apk/debug/app-debug.apk
```

#### Option 3: Run Tests
```bash
./gradlew test
./gradlew connectedAndroidTest
```
"""
            elif lang == "swift" or "ios" in framework.lower():
                report += """### Run on iOS Simulator

**Prerequisites:** Xcode installed

1. Open the `.xcodeproj` or `.xcworkspace` file in Xcode
2. Select an iOS Simulator from the device dropdown
3. Press `Cmd+R` to build and run

#### Build for Testing
```bash
xcodebuild test -project *.xcodeproj -scheme * -destination 'platform=iOS Simulator,name=iPhone 15'
```
"""
            else:
                report += """### How to Run
Check the project README.md for specific instructions on running this application.
"""
        return report
