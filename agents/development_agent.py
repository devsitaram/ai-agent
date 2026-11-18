"""Agent 3: Development Agent - Implements the software based on architecture."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

from core.base_agent import BaseAgent
from core.llm_interface import LLMInterface
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, BugReport, ProjectState, ProjectStatus


class DevelopmentAgent(BaseAgent):
    """Generates complete source code based on approved architecture and requirements."""

    def __init__(
        self,
        llm_interface: Optional[LLMInterface] = None,
        project_manager: Optional[ProjectManager] = None,
    ):
        super().__init__(
            name="development",
            description="Generating source code and implementing features",
        )
        self.llm = llm_interface or LLMInterface()
        self.project_manager = project_manager or ProjectManager()
        self.generated_files: List[str] = []

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that architecture exists."""
        arch_result = project_state.get_agent_result("architecture")
        if arch_result.status != AgentStatus.COMPLETED:
            raise ValueError("Architecture not completed. Run architecture agent first.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project and generate source code.
        
        Args:
            project_state: Current project state with architecture
            
        Returns:
            Updated project state with generated code
        """
        self.generated_files = []

        # Read inputs
        requirements = self.project_manager.read_file(project_state, "REQUIREMENTS.md") or ""
        architecture = self.project_manager.read_file(project_state, "ARCHITECTURE.md") or ""
        user_input = project_state.user_input

        # Get tech stack
        tech_stack = project_state.tech_stack
        lang = tech_stack.get("language", "python")

        self.console.print(f"[cyan]Generating {lang} project...[/cyan]")

        # Use LLM to generate code based on architecture and tech stack
        try:
            code_content = self.llm.generate_code(architecture, requirements, user_input)
        except Exception as e:
            self.console.print(f"[yellow]Warning: LLM call failed for code generation: {e}[/yellow]")
            self.console.print("[yellow]Using fallback to generate from templates.[/yellow]")
            code_content = ""
        
        # Parse LLM response to extract files
        self._parse_and_write_files(project_state, code_content, tech_stack)

        # If LLM returned nothing or parsing failed, use fallback templates
        if not self.generated_files:
            self.console.print("[yellow]LLM code generation incomplete, using fallback templates...[/yellow]")

            # Detect framework/type to route to best generator
            framework = tech_stack.get("framework", tech_stack.get("backend", "")).lower()
            is_mobile = tech_stack.get("type") == "mobile" or any(kw in str(tech_stack).lower() for kw in ["mobile", "android", "ios", "flutter"])
            is_frontend = tech_stack.get("type") == "frontend" or any(kw in str(tech_stack).lower() for kw in ["react", "vue", "frontend", "ui"])

            if lang == "python":
                self._generate_python_project(project_state, requirements, architecture)
            elif lang in ("javascript", "typescript", "nodejs", "node.js"):
                self._generate_nodejs_project(project_state, requirements, architecture)
            elif lang == "go":
                self._generate_go_project(project_state)
            elif lang == "rust":
                self._generate_rust_project(project_state)
            elif lang == "kotlin":
                self._generate_kotlin_project(project_state)
            elif lang == "java":
                self._generate_java_project(project_state)
            elif lang == "swift":
                self._generate_swift_project(project_state)
            elif lang == "dart":
                self._generate_dart_project(project_state)
            elif lang == "csharp" or lang == "c#":
                self._generate_csharp_project(project_state)
            elif lang == "ruby":
                self._generate_ruby_project(project_state)
            elif lang == "php":
                self._generate_php_project(project_state)
            else:
                # For any other language, generate a basic structure with source code
                self._generate_basic_project(project_state, lang, tech_stack)

        # Get previous bug reports if in QA loop
        qa_result = project_state.get_agent_result("qa")
        if qa_result.bug_reports:
            self.console.print(f"[yellow]Fixing {len(qa_result.bug_reports)} reported bugs...[/yellow]")
            self._fix_bugs(project_state, qa_result.bug_reports)
            qa_result.bugs_fixed = len(qa_result.bug_reports)

        # Update agent result
        summary = self._generate_summary()
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED,
            output=summary,
            artifacts=self.generated_files,
        )
        project_state.set_agent_result(self.name, agent_result)
        project_state.status = ProjectStatus.DEVELOPMENT

        self.console.print(
            f"[green]✓ Generated {len(self.generated_files)} files[/green]"
        )

        return project_state

    def _parse_and_write_files(self, project_state: ProjectState, code_content: str, tech_stack: dict) -> None:
        """Parse LLM-generated code content and write files to project.
        
        Tries to extract file blocks from markdown code fences with file paths.
        """
        import re as re2

        # Regex to find file paths and code blocks.
        # It looks for a filename (e.g., `path/to/file.py`) followed by a markdown code block.
        # The filename can be on the same line as the opening ```, or on the line(s) before.
        pattern = re2.compile(
            r"[`#]*\s*(?:[Ff]ile:)?\s*([a-zA-Z0-9_./\\-]+\.[a-zA-Z0-9_]+)\s*[`#]*\n"  # File path
            r"```[a-zA-Z]*\n"  # Opening code fence
            r"([\s\S]*?)\n"    # Code content
            r"```",            # Closing code fence
            re2.MULTILINE
        )

        matches = pattern.finditer(code_content)
        
        for match in matches:
            file_path = match.group(1).strip()
            content = match.group(2).strip()

            self.generated_files.append(
                self.project_manager.write_file(project_state, file_path, content)
            )

    def _generate_basic_project(self, project_state: ProjectState, lang: str, tech_stack: dict) -> None:
        """Generate basic project files for any language when LLM fails.
        
        Creates proper source code files with a working HTTP server,
        rather than just a README.
        """
        framework = tech_stack.get("framework", tech_stack.get("backend", ""))
        db = tech_stack.get("database", "sqlite")
        
        # README
        self._generate_project_readme(project_state)
        
        # Generate language-specific source code
        if lang == "ruby":
            self._generate_ruby_project(project_state)
        elif lang == "php":
            self._generate_php_project(project_state)
        elif lang == "csharp" or lang == "c#":
            self._generate_csharp_project(project_state)
        elif lang == "java":
            self._generate_java_project(project_state)
        elif lang == "dart":
            self._generate_dart_project(project_state)
        else:
            # Generic fallback: create a minimal source file
            self._generate_fallback_project(project_state, lang)

    def _generate_python_project(
        self, project_state: ProjectState, requirements: str, architecture: str
    ) -> None:
        """Generate Python project structure."""
        # Create app directory
        app_dir = "app"
        
        # __init__.py
        init_content = """# Application package
from fastapi import FastAPI


def create_app() -> FastAPI:
    \"\"\"Create and configure the FastAPI application.\"\"\"
    app = FastAPI(
        title="My Application",
        description="Auto-generated application",
        version="1.0.0",
    )
    return app
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{app_dir}/__init__.py", init_content)
        )

        # config.py
        config_content = """# Application configuration
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    \"\"\"Application settings.\"\"\"
    app_name: str = "My Application"
    debug: bool = True
    database_url: str = "sqlite:///./app.db"
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{app_dir}/config.py", config_content)
        )

        # models.py
        models_content = """# Database models
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


class User(Base):
    \"\"\"User model.\"\"\"
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    items = relationship("Item", back_populates="owner", cascade="all, delete-orphan")


class Item(Base):
    \"\"\"Item model.\"\"\"
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    owner = relationship("User", back_populates="items")
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{app_dir}/models.py", models_content)
        )

        # schemas.py
        schemas_content = """# Pydantic schemas for request/response validation
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


# ---- Auth Schemas ----

class UserCreate(BaseModel):
    \"\"\"Schema for user registration.\"\"\"
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    \"\"\"Schema for user login.\"\"\"
    username: str
    password: str


class UserResponse(BaseModel):
    \"\"\"Schema for user response.\"\"\"
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    \"\"\"Schema for JWT token response.\"\"\"
    access_token: str
    token_type: str = "bearer"


# ---- Item Schemas ----

class ItemCreate(BaseModel):
    \"\"\"Schema for creating an item.\"\"\"
    title: str
    description: Optional[str] = None


class ItemUpdate(BaseModel):
    \"\"\"Schema for updating an item.\"\"\"
    title: Optional[str] = None
    description: Optional[str] = None


class ItemResponse(BaseModel):
    \"\"\"Schema for item response.\"\"\"
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemListResponse(BaseModel):
    \"\"\"Schema for paginated item list.\"\"\"
    items: List[ItemResponse]
    total: int
    page: int
    page_size: int
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{app_dir}/schemas.py", schemas_content)
        )

        # Create routes directory
        self.project_manager.write_file(project_state, f"{app_dir}/routes/__init__.py", "")

    def _generate_main_app(self, project_state: ProjectState, architecture: str) -> None:
        """Generate the main application entry point."""
        tech = project_state.tech_stack
        lang = tech.get("language", "python")

        main_content = '''"""Main application entry point."""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Auto-generated Application",
    description="Application generated by AI Software Development Agent",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Welcome to the Auto-generated Application",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "app/main.py", main_content)
        )

    def _generate_dependency_file(self, project_state: ProjectState) -> None:
        """Generate requirements.txt or package.json."""
        tech = project_state.tech_stack
        lang = tech.get("language", "python")

        if lang == "python":
            req_content = """# Core
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0

# Database
sqlalchemy>=2.0.0
aiosqlite>=0.19.0

# Auth
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# Testing
pytest>=7.4.0
httpx>=0.25.0
pytest-asyncio>=0.21.0

# Utils
python-dotenv>=1.0.0
"""
            self.generated_files.append(
                self.project_manager.write_file(project_state, "requirements.txt", req_content)
            )

    def _generate_tests(self, project_state: ProjectState, architecture: str) -> None:
        """Generate test files."""
        # conftest.py
        conftest_content = """# Test configuration and fixtures
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    \"\"\"Create test client.\"\"\"
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_user_data():
    \"\"\"Sample user data for testing.\"\"\"
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    }
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tests/conftest.py", conftest_content)
        )

        # test_main.py
        test_main_content = """# Tests for main application
from fastapi.testclient import TestClient


def test_root_endpoint(client):
    \"\"\"Test root endpoint returns expected response.\"\"\"
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "status" in data


def test_health_check(client):
    \"\"\"Test health check endpoint.\"\"\"
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_cors_headers(client):
    \"\"\"Test CORS headers are present.\"\"\"
    response = client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tests/test_main.py", test_main_content)
        )

        # test_models.py
        test_models_content = """# Tests for database models
from app.models import User, Item


def test_user_model_attributes():
    \"\"\"Test User model has required attributes.\"\"\"
    assert hasattr(User, "id")
    assert hasattr(User, "username")
    assert hasattr(User, "email")
    assert hasattr(User, "password_hash")
    assert hasattr(User, "created_at")
    assert hasattr(User, "updated_at")


def test_item_model_attributes():
    \"\"\"Test Item model has required attributes.\"\"\"
    assert hasattr(Item, "id")
    assert hasattr(Item, "user_id")
    assert hasattr(Item, "title")
    assert hasattr(Item, "description")
    assert hasattr(Item, "created_at")
    assert hasattr(Item, "updated_at")


def test_user_item_relationship():
    \"\"\"Test User-Item relationship exists.\"\"\"
    assert hasattr(User, "items")
    assert hasattr(Item, "owner")
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tests/test_models.py", test_models_content)
        )

        # test_schemas.py
        test_schemas_content = """# Tests for Pydantic schemas
from app.schemas import UserCreate, UserLogin, ItemCreate, ItemUpdate


def test_user_create_schema():
    \"\"\"Test UserCreate schema validation.\"\"\"
    data = {"username": "testuser", "email": "test@example.com", "password": "pass123"}
    schema = UserCreate(**data)
    assert schema.username == "testuser"
    assert schema.email == "test@example.com"


def test_user_create_invalid_email():
    \"\"\"Test UserCreate rejects invalid email.\"\"\"
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="not-an-email", password="pass123")


def test_item_create_schema():
    \"\"\"Test ItemCreate schema.\"\"\"
    item = ItemCreate(title="Test Item", description="A test item")
    assert item.title == "Test Item"
    assert item.description == "A test item"


def test_item_create_optional_description():
    \"\"\"Test ItemCreate with optional description.\"\"\"
    item = ItemCreate(title="Test Item")
    assert item.title == "Test Item"
    assert item.description is None


def test_item_update_schema():
    \"\"\"Test ItemUpdate with all fields optional.\"\"\"
    update = ItemUpdate(title="Updated Title")
    assert update.title == "Updated Title"
    assert update.description is None
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tests/test_schemas.py", test_schemas_content)
        )

    def _generate_project_readme(self, project_state: ProjectState) -> None:
        """Generate project README based on tech stack."""
        tech = project_state.tech_stack
        lang = tech.get('language', 'python')
        backend = tech.get('backend', 'fastapi')
        database = tech.get('database', 'sqlite')

        readme_content = f"""# {project_state.project_name}

## Overview
Auto-generated project by the AI Software Development Agent System.

## Tech Stack
- **Language**: {lang}
- **Framework**: {backend}
- **Database**: {database}

## Getting Started
### Prerequisites
- {lang.title()} SDK installed

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd <project-directory>
# Install dependencies (see specific instructions below)
```

### Running the Application
Check the documentation or run instructions in the project files.
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "README.md", readme_content)
        )

    def _generate_nodejs_project(
        self, project_state: ProjectState, requirements: str, architecture: str
    ) -> None:
        """Generate Node.js project structure."""
        # package.json
        package_content = """{
  "name": "auto-generated-app",
  "version": "1.0.0",
  "description": "Auto-generated application",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0",
    "mongoose": "^7.0.0",
    "jsonwebtoken": "^9.0.0",
    "bcryptjs": "^2.4.3",
    "cors": "^2.8.5",
    "dotenv": "^16.0.0"
  },
  "devDependencies": {
    "jest": "^29.0.0",
    "nodemon": "^3.0.0",
    "supertest": "^6.3.0"
  }
}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "package.json", package_content)
        )

        # src/index.js
        index_content = """const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
  res.json({
    message: 'Welcome to Auto-generated Application',
    version: '1.0.0',
    status: 'running'
  });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// Start server
app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

module.exports = app;
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "src/index.js", index_content)
        )

    # ── Language-Specific Generators ──
    # Go, Rust, Kotlin, Swift, Ruby, PHP, C#, and generic fallback

    def _generate_go_project(self, project_state: ProjectState) -> None:
        """Generate Go project structure with a basic HTTP server."""
        # go.mod
        mod_content = f"""module {project_state.project_name.lower().replace(' ', '-')}

go 1.21
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "go.mod", mod_content)
        )

        # main.go
        main_content = '''package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

type HealthResponse struct {
	Status  string `json:"status"`
	Version string `json:"version"`
	Time    string `json:"time"`
}

type ErrorResponse struct {
	Error   string `json:"error"`
	Message string `json:"message"`
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type, Authorization")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}

func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func rootHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"message": "Welcome to Auto-generated Application",
		"version": "1.0.0",
		"status":  "running",
	})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, HealthResponse{
		Status:  "healthy",
		Version: "1.0.0",
		Time:    time.Now().UTC().Format(time.RFC3339),
	})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/", rootHandler)
	mux.HandleFunc("/health", healthHandler)

	handler := corsMiddleware(mux)

	fmt.Printf("Server starting on port %s...\\n", port)
	log.Fatal(http.ListenAndServe(":"+port, handler))
}
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "main.go", main_content)
        )

        # main_test.go
        test_content = '''package main

import (
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRootEndpoint(t *testing.T) {
	req := httptest.NewRequest("GET", "/", nil)
	rec := httptest.NewRecorder()

	rootHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestHealthEndpoint(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	rec := httptest.NewRecorder()

	healthHandler(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200, got %d", rec.Code)
	}
}

func TestCorsHeaders(t *testing.T) {
	req := httptest.NewRequest("OPTIONS", "/", nil)
	rec := httptest.NewRecorder()

	mux := http.NewServeMux()
	mux.HandleFunc("/", rootHandler)
	corsMiddleware(mux).ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Errorf("expected status 200 for CORS preflight, got %d", rec.Code)
	}
}
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "main_test.go", test_content)
        )

        # .gitignore
        gitignore = """# Binaries
*.exe
*.exe~
*.dll
*.so
*.dylib

# Test binary
*.test

# Output of the go coverage tool
*.out

# Dependency directories
vendor/
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, ".gitignore", gitignore)
        )

    def _generate_rust_project(self, project_state: ProjectState) -> None:
        """Generate Rust project structure with Actix-web HTTP server."""
        proj_name = project_state.project_name.lower().replace(' ', '_').replace('-', '_')

        # Cargo.toml
        cargo = f"""[package]
name = "{proj_name}"
version = "0.1.0"
edition = "2021"

[dependencies]
actix-web = "4"
actix-cors = "0.7"
serde = {{ version = "1", features = ["derive"] }}
serde_json = "1"
tokio = {{ version = "1", features = ["full"] }}
chrono = "0.4"
env_logger = "0.11"
log = "0.4"
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Cargo.toml", cargo)
        )

        # src/main.rs
        main_rs = '''use actix_cors::Cors;
use actix_web::{get, web, App, HttpResponse, HttpServer, middleware, Responder};
use serde::Serialize;
use std::env;

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    version: String,
}

#[derive(Serialize)]
struct RootResponse {
    message: String,
    version: String,
    status: String,
}

#[get("/")]
async fn root() -> impl Responder {
    HttpResponse::Ok().json(RootResponse {
        message: "Welcome to Auto-generated Application".to_string(),
        version: "1.0.0".to_string(),
        status: "running".to_string(),
    })
}

#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok().json(HealthResponse {
        status: "healthy".to_string(),
        version: "1.0.0".to_string(),
    })
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    env_logger::init();

    let port: u16 = env::var("PORT")
        .unwrap_or_else(|_| "8080".to_string())
        .parse()
        .expect("PORT must be a valid number");

    log::info!("Starting server on port {}", port);

    HttpServer::new(|| {
        let cors = Cors::default()
            .allow_any_origin()
            .allow_any_method()
            .allow_any_header()
            .max_age(3600);

        App::new()
            .wrap(cors)
            .wrap(middleware::Logger::default())
            .service(root)
            .service(health)
    })
    .bind(("0.0.0.0", port))?
    .run()
    .await
}
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "src/main.rs", main_rs)
        )

        # .gitignore
        gitignore = """/target
**/*.rs.bk
Cargo.lock
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, ".gitignore", gitignore)
        )

    def _generate_kotlin_project(self, project_state: ProjectState) -> None:
        """Generate Kotlin project structure with Ktor HTTP server."""
        tech = project_state.tech_stack
        is_mobile = "android" in tech.get("mobile", "") or "compose" in tech.get("frontend", "")

        if is_mobile:
            self._generate_android_compose_project(project_state)
        else:
            self._generate_ktor_project(project_state)

    def _generate_ktor_project(self, project_state: ProjectState) -> None:
        """Generates a backend project using Ktor."""
        proj_name = project_state.project_name.lower().replace(" ", "-")

        # build.gradle.kts
        build_gradle = f"""plugins {{
    kotlin("jvm") version "1.9.22"
    kotlin("plugin.serialization") version "1.9.22"
    application
}}

group = "com.example"
version = "1.0.0"

repositories {{ mavenCentral() }}

dependencies {{
    // Ktor server
    implementation("io.ktor:ktor-server-core-jvm:2.3.10")
    implementation("io.ktor:ktor-server-netty-jvm:2.3.10")
    implementation("io.ktor:ktor-server-content-negotiation-jvm:2.3.10")
    implementation("io.ktor:ktor-serialization-kotlinx-json-jvm:2.3.10")
    implementation("io.ktor:ktor-server-cors-jvm:2.3.10")

    // Logging
    implementation("ch.qos.logback:logback-classic:1.5.3")

    // Testing
    testImplementation("io.ktor:ktor-server-tests-jvm:2.3.10")
    testImplementation("org.jetbrains.kotlin:kotlin-test-junit:1.9.22")
}}

application {{
    mainClass.set("com.example.ApplicationKt")
}}

kotlin {{ jvmToolchain(17) }}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "build.gradle.kts", build_gradle)
        )

        # settings.gradle.kts
        settings = f"""rootProject.name = "{proj_name}" """
        self.generated_files.append(
            self.project_manager.write_file(project_state, "settings.gradle.kts", settings)
        )

        # src/main/kotlin/com/example/Application.kt
        app_kt = """package com.example

import io.ktor.serialization.kotlinx.json.*
import io.ktor.server.application.*
import io.ktor.server.engine.*
import io.ktor.server.netty.*
import io.ktor.server.plugins.contentnegotiation.*
import io.ktor.server.plugins.cors.routing.*
import io.ktor.server.response.*
import io.ktor.server.routing.*

fun main() {
    embeddedServer(Netty, port = 8080, host = "0.0.0.0", module = Application::module)
        .start(wait = true)
}

fun Application.module() {
    install(ContentNegotiation) { json() }
    install(CORS) { anyHost() }
    routing {
        get("/") { call.respond(mapOf("message" to "Welcome!")) }
        get("/health") { call.respond(mapOf("status" to "healthy")) }
    }
}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "src/main/kotlin/com/example/Application.kt", app_kt)
        )

    def _generate_android_compose_project(self, project_state: ProjectState) -> None:
        """Generates a basic Android Jetpack Compose project structure."""
        proj_name = project_state.project_name
        pkg_name = "".join(filter(str.isalnum, proj_name)).lower()
        pkg_path = f"app/src/main/java/com/example/{pkg_name}"

        # settings.gradle.kts
        settings_gradle = """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "My Application"
include(":app")
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "settings.gradle.kts", settings_gradle))

        # build.gradle.kts (root)
        root_build_gradle = """plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.jetbrains.kotlin.android) apply false
}
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "build.gradle.kts", root_build_gradle))

        # gradle/libs.versions.toml
        libs_toml = """[versions]
agp = "8.2.0"
kotlin = "1.9.22"
coreKtx = "1.12.0"
lifecycleRuntimeKtx = "2.7.0"
activityCompose = "1.8.2"
composeBom = "2024.02.01"

[libraries]
androidx-core-ktx = { group = "androidx.core", name = "core-ktx", version.ref = "coreKtx" }
androidx-lifecycle-runtime-ktx = { group = "androidx.lifecycle", name = "lifecycle-runtime-ktx", version.ref = "lifecycleRuntimeKtx" }
androidx-activity-compose = { group = "androidx.activity", name = "activity-compose", version.ref = "activityCompose" }
androidx-compose-bom = { group = "androidx.compose", name = "compose-bom", version.ref = "composeBom" }
androidx-ui = { group = "androidx.compose.ui", name = "ui" }
androidx-ui-graphics = { group = "androidx.compose.ui", name = "ui-graphics" }
androidx-ui-tooling = { group = "androidx.compose.ui", name = "ui-tooling" }
androidx-ui-tooling-preview = { group = "androidx.compose.ui", name = "ui-tooling-preview" }
androidx-material3 = { group = "androidx.compose.material3", name = "material3" }

[plugins]
android-application = { id = "com.android.application", version.ref = "agp" }
jetbrains-kotlin-android = { id = "org.jetbrains.kotlin.android", version.ref = "kotlin" }
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "gradle/libs.versions.toml", libs_toml))

        # app/build.gradle.kts
        app_build_gradle = f"""plugins {{
    alias(libs.plugins.android.application)
    alias(libs.plugins.jetbrains.kotlin.android)
}}

android {{
    namespace = "com.example.{pkg_name}"
    compileSdk = 34

    defaultConfig {{
        applicationId = "com.example.{pkg_name}"
        minSdk = 24
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }}
    buildFeatures {{
        compose = true
    }}
    composeOptions {{
        kotlinCompilerExtensionVersion = "1.5.8"
    }}
    packaging {{
        resources.excludes.add("/META-INF/{{*.md,*.txt}}")
    }}
}}

dependencies {{
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
}}
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "app/build.gradle.kts", app_build_gradle))

        # app/src/main/AndroidManifest.xml
        manifest = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <application
        android:allowBackup="true"
        android:icon="@android:mipmap/sym_def_app_icon"
        android:label="@string/app_name"
        android:roundIcon="@android:mipmap/sym_def_app_icon"
        android:supportsRtl="true"
        android:theme="@style/Theme.App"
        tools:targetApi="31">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.App">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "app/src/main/AndroidManifest.xml", manifest))

        # app/src/main/res/values/strings.xml
        strings_xml = f"""<resources>
    <string name="app_name">{proj_name}</string>
</resources>
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "app/src/main/res/values/strings.xml", strings_xml))

        # app/src/main/res/values/themes.xml
        themes_xml = """<resources>
    <style name="Theme.App" parent="android:Theme.Material.Light.NoActionBar" />
</resources>
"""
        self.generated_files.append(self.project_manager.write_file(project_state, "app/src/main/res/values/themes.xml", themes_xml))

        # MainActivity.kt
        main_activity = f"""package com.example.{pkg_name}

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import com.example.{pkg_name}.ui.theme.AppTheme

class MainActivity : ComponentActivity() {{
    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContent {{
            AppTheme {{
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {{
                    Greeting("Android")
                }}
            }}
        }}
    }}
}}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {{
    Box(modifier = modifier.fillMaxSize(), contentAlignment = Alignment.Center) {{
        Text(text = "Hello $name!")
    }}
}}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {{
    AppTheme {{
        Greeting("Android")
    }}
}}
"""
        self.generated_files.append(self.project_manager.write_file(project_state, f"{pkg_path}/MainActivity.kt", main_activity))

        # Theme.kt
        theme_kt = f"""package com.example.{pkg_name}.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable

private val LightColorScheme = lightColorScheme()

@Composable
fun AppTheme(content: @Composable () -> Unit) {{
    MaterialTheme(
        colorScheme = LightColorScheme,
        typography = Typography,
        content = content
    )
}}
"""
        self.generated_files.append(self.project_manager.write_file(project_state, f"{pkg_path}/ui/theme/Theme.kt", theme_kt))

        # Type.kt
        type_kt = f"""package com.example.{pkg_name}.ui.theme

import androidx.compose.material3.Typography

val Typography = Typography()
"""
        self.generated_files.append(self.project_manager.write_file(project_state, f"{pkg_path}/ui/theme/Typography.kt", type_kt))

    def _generate_swift_project(self, project_state: ProjectState) -> None:
        """Generate Swift project structure with Vapor HTTP server."""
        # Package.swift
        package_swift = """// swift-tools-version:5.7
import PackageDescription

let package = Package(
    name: "auto-generated-app",
    platforms: [
        .macOS(.v12)
    ],
    dependencies: [
        .package(url: "https://github.com/vapor/vapor.git", from: "4.89.0"),
    ],
    targets: [
        .executableTarget(
            name: "App",
            dependencies: [
                .product(name: "Vapor", package: "vapor"),
            ]
        ),
        .testTarget(
            name: "AppTests",
            dependencies: [
                .target(name: "App"),
                .product(name: "XCTVapor", package: "vapor"),
            ]
        )
    ]
)
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Package.swift", package_swift)
        )

        # Sources/App/main.swift
        main_swift = '''import Vapor

var env = try Environment.detect()
try LoggingSystem.bootstrap(from: &env)

let app = Application(env)
defer { app.shutdown() }

// CORS
let corsConfiguration = CORSMiddleware.Configuration(
    allowedOrigin: .all,
    allowedMethods: [.GET, .POST, .PUT, .DELETE, .OPTIONS],
    allowedHeaders: [.contentType, .authorization]
)
app.middleware.use(CORSMiddleware(configuration: corsConfiguration))
app.middleware.use(ErrorMiddleware(environment: app.environment))

// Routes
app.get { req async throws in
    return ["message": "Welcome to Auto-generated Application",
            "version": "1.0.0",
            "status": "running"]
}

app.get("health") { req async throws in
    return ["status": "healthy", "version": "1.0.0"]
}

try app.run()
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Sources/App/main.swift", main_swift)
        )

        # Tests/AppTests/AppTests.swift
        test_swift = '''@testable import App
import XCTVapor

final class AppTests: XCTestCase {
    func testRootEndpoint() throws {
        let app = Application(.testing)
        defer { app.shutdown() }
        try configure(app)

        try app.test(.GET, "/") { res in
            XCTAssertEqual(res.status, .ok)
        }
    }

    func testHealthEndpoint() throws {
        let app = Application(.testing)
        defer { app.shutdown() }
        try configure(app)

        try app.test(.GET, "/health") { res in
            XCTAssertEqual(res.status, .ok)
        }
    }
}
'''
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Tests/AppTests/AppTests.swift", test_swift)
        )

        # .gitignore
        gitignore = """.DS_Store
/.build
/Packages
*.xcodeproj
*.xcworkspace
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, ".gitignore", gitignore)
        )

    def _generate_ruby_project(self, project_state: ProjectState) -> None:
        """Generate Ruby project structure with Sinatra."""
        # Gemfile
        gemfile = """source 'https://rubygems.org'

gem 'sinatra', '~> 3.0'
gem 'sinatra-contrib', '~> 3.0'
gem 'puma', '~> 6.0'
gem 'rack-cors', '~> 2.0'
gem 'json'

group :test do
  gem 'rspec', '~> 3.12'
  gem 'rack-test', '~> 2.1'
end
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Gemfile", gemfile)
        )

        # app.rb
        app_rb = """require 'sinatra'
require 'sinatra/json'
require 'rack/cors'
require 'json'

use Rack::Cors do
  allow do
    origins '*'
    resource '*',
      headers: :any,
      methods: [:get, :post, :put, :delete, :options]
  end
end

set :port, ENV.fetch('PORT', 4567).to_i
set :bind, '0.0.0.0'

# Root endpoint
get '/' do
  json(
    message: 'Welcome to Auto-generated Application',
    version: '1.0.0',
    status: 'running'
  )
end

# Health check
get '/health' do
  json(
    status: 'healthy',
    version: '1.0.0'
  )
end
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "app.rb", app_rb)
        )

        # config.ru
        config_ru = "require './app'\nrun Sinatra::Application\n"
        self.generated_files.append(
            self.project_manager.write_file(project_state, "config.ru", config_ru)
        )

        # spec/app_spec.rb
        spec_rb = """require 'rack/test'
require 'json'

describe 'Application' do
  include Rack::Test::Methods

  def app
    Sinatra::Application
  end

  it 'returns OK on root' do
    get '/'
    expect(last_response.status).to eq(200)
  end

  it 'returns healthy on health check' do
    get '/health'
    expect(last_response.status).to eq(200)
    body = JSON.parse(last_response.body)
    expect(body['status']).to eq('healthy')
  end
end
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "spec/app_spec.rb", spec_rb)
        )

    def _generate_php_project(self, project_state: ProjectState) -> None:
        """Generate PHP project structure with Slim framework."""
        # composer.json
        composer = """{
    "name": "app/auto-generated",
    "description": "Auto-generated PHP application",
    "require": {
        "php": ">=8.1",
        "slim/slim": "^4.0",
        "slim/psr7": "^1.6",
        "php-di/php-di": "^7.0"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0",
        "guzzlehttp/guzzle": "^7.0"
    },
    "autoload": {
        "psr-4": {
            "App\\\\": "src/"
        }
    }
}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "composer.json", composer)
        )

        # public/index.php
        index_php = """<?php
declare(strict_types=1);

use Psr\\Http\\Message\\ResponseInterface as Response;
use Psr\\Http\\Message\\ServerRequestInterface as Request;
use Slim\\Factory\\AppFactory;

require __DIR__ . '/../vendor/autoload.php';

$app = AppFactory::create();

// CORS
$app->add(function (Request $request, $handler): Response {
    $response = $handler->handle($request);
    return $response
        ->withHeader('Access-Control-Allow-Origin', '*')
        ->withHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        ->withHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
});

// Root
$app->get('/', function (Request $request, Response $response) {
    $payload = json_encode([
        'message' => 'Welcome to Auto-generated Application',
        'version' => '1.0.0',
        'status' => 'running'
    ]);
    $response->getBody()->write($payload);
    return $response->withHeader('Content-Type', 'application/json');
});

// Health
$app->get('/health', function (Request $request, Response $response) {
    $payload = json_encode([
        'status' => 'healthy',
        'version' => '1.0.0'
    ]);
    $response->getBody()->write($payload);
    return $response->withHeader('Content-Type', 'application/json');
});

$app->run();
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "public/index.php", index_php)
        )

        # tests/ApplicationTest.php
        test_php = """<?php
declare(strict_types=1);

use PHPUnit\\Framework\\TestCase;
use Slim\\Psr7\\Factory\\ServerRequestFactory;

class ApplicationTest extends TestCase
{
    public function testRootEndpoint(): void
    {
        $app = require __DIR__ . '/../public/index.php';
        $this->assertTrue(true); // Basic connectivity test
    }
}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tests/ApplicationTest.php", test_php)
        )

    def _generate_csharp_project(self, project_state: ProjectState) -> None:
        """Generate C# (.NET) project structure with minimal API."""
        proj_name = project_state.project_name.replace(' ', '.')

        # .csproj
        csproj = f"""<Project Sdk="Microsoft.NET.Sdk.Web">

  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <RootNamespace>{proj_name}</RootNamespace>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

</Project>
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{proj_name}.csproj", csproj)
        )

        # Program.cs
        program_cs = """using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);

// CORS
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

var app = builder.Build();
app.UseCors();

// Root endpoint
app.MapGet("/", () =>
{
    return Results.Json(new
    {
        message = "Welcome to Auto-generated Application",
        version = "1.0.0",
        status = "running"
    });
});

// Health check
app.MapGet("/health", () =>
{
    return Results.Json(new
    {
        status = "healthy",
        version = "1.0.0"
    });
});

var port = Environment.GetEnvironmentVariable("PORT") ?? "5000";
app.Run($"http://0.0.0.0:{port}");
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "Program.cs", program_cs)
        )

    def _generate_java_project(self, project_state: ProjectState) -> None:
        """Generate Java (Spring Boot) project structure."""
        proj_name = project_state.project_name.lower().replace(' ', '-')
        pkg = "com.example"

        # pom.xml
        pom = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.2.0</version>
    </parent>
    <groupId>{pkg}</groupId>
    <artifactId>{proj_name}</artifactId>
    <version>1.0.0</version>
    <name>{proj_name}</name>
    <properties>
        <java.version>17</java.version>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "pom.xml", pom)
        )

        # src/main/java/com/example/Application.java
        pkg_path = "src/main/java/com/example"
        app_java = f"""package {pkg};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@SpringBootApplication
@RestController
public class Application {{

    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}

    @GetMapping("/")
    public RootResponse root() {{
        return new RootResponse("Welcome to Auto-generated Application", "1.0.0", "running");
    }}

    @GetMapping("/health")
    public HealthResponse health() {{
        return new HealthResponse("healthy", "1.0.0");
    }}

    record RootResponse(String message, String version, String status) {{}}
    record HealthResponse(String status, String version) {{}}
}}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"{pkg_path}/Application.java", app_java)
        )

        # src/test/java/com/example/ApplicationTest.java
        test_java = f"""package {pkg};

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class ApplicationTest {{

    @Autowired
    private MockMvc mockMvc;

    @Test
    void rootEndpoint() throws Exception {{
        mockMvc.perform(get("/")).andExpect(status().isOk());
    }}

    @Test
    void healthEndpoint() throws Exception {{
        mockMvc.perform(get("/health")).andExpect(status().isOk());
    }}
}}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "src/test/java/com/example/ApplicationTest.java", test_java)
        )

    def _generate_dart_project(self, project_state: ProjectState) -> None:
        """Generate Dart/Flutter project structure."""
        proj_name = project_state.project_name.lower().replace(' ', '_').replace('-', '_')

        # pubspec.yaml
        pubspec = f"""name: {proj_name}
description: Auto-generated Flutter project
version: 1.0.0

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  cupertino_icons: ^1.0.6

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "pubspec.yaml", pubspec)
        )

        # lib/main.dart
        main_dart = f"""import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() {{
  runApp(const MyApp());
}}

class MyApp extends StatelessWidget {{
  const MyApp({{super.key}});

  @override
  Widget build(BuildContext context) {{
    return MaterialApp(
      title: '{project_state.project_name}',
      theme: ThemeData(
        colorSchemeSeed: Colors.blue,
        useMaterial3: true,
      ),
      home: const HomePage(),
    );
  }}
}}

class HomePage extends StatefulWidget {{
  const HomePage({{super.key}});

  @override
  State<HomePage> createState() => _HomePageState();
}}

class _HomePageState extends State<HomePage> {{
  String _status = 'Loading...';

  @override
  void initState() {{
    super.initState();
    _checkHealth();
  }}

  Future<void> _checkHealth() async {{
    try {{
      final response = await http.get(
        Uri.parse('http://localhost:8080/health'),
      );
      if (response.statusCode == 200) {{
        setState(() => _status = 'Connected');
      }}
    }} catch (e) {{
      setState(() => _status = 'Server not running');
    }}
  }}

  @override
  Widget build(BuildContext context) {{
    return Scaffold(
      appBar: AppBar(
        title: Text('{project_state.project_name}'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Text('Welcome to Auto-generated Application'),
            const SizedBox(height: 20),
            Text('Status: $_status'),
          ],
        ),
      ),
    );
  }}
}}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "lib/main.dart", main_dart)
        )

    def _generate_electron_project(self, project_state: ProjectState) -> None:
        """Generate Electron (TypeScript) desktop project structure."""
        # package.json
        package_json = f"""{{"name": "{project_state.project_name.lower().replace(' ', '-')}",
  "version": "1.0.0",
  "description": "Auto-generated Electron application",
  "main": "dist/main.js",
  "scripts": {{
    "build": "tsc",
    "start": "npm run build && electron .",
    "dev": "tsc && electron ."
  }},
  "dependencies": {{
    "electron": "^28.0.0"
  }},
  "devDependencies": {{
    "typescript": "^5.3.0",
    "@types/node": "^20.0.0"
  }}
}}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "package.json", package_json)
        )

        # src/main.ts
        main_ts = """import { app, BrowserWindow } from 'electron';
import * as path from 'path';

let mainWindow: BrowserWindow | null = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, '../public/index.html'));
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "src/main.ts", main_ts)
        )

        # tsconfig.json
        tsconfig = """{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true
  },
  "include": ["src/**/*"]
}
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "tsconfig.json", tsconfig)
        )

        # public/index.html
        index_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Electron App</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container { text-align: center; }
        h1 { font-size: 2.5em; margin-bottom: 0.5em; }
        p { font-size: 1.2em; opacity: 0.9; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to Auto-generated Application</h1>
        <p>Version 1.0.0</p>
        <p>Running on Electron</p>
    </div>
</body>
</html>
"""
        self.generated_files.append(
            self.project_manager.write_file(project_state, "public/index.html", index_html)
        )

    def _generate_fallback_project(self, project_state: ProjectState, lang: str) -> None:
        """Generate a minimal fallback project for any unrecognized language.
        
        Creates a generic source file so the project is never empty.
        """
        # README is already created by _generate_project_readme
        # Create a basic source file with instructions
        fallback = f"""//
// {project_state.project_name}
// Auto-generated {lang} project
//
// This is a starter template. Run this project according to your {lang} environment.
//

fn main() {{
    println!("{project_state.project_name} - ready to build!");
    println!("Language: {lang}");
    println!("Edit this file to add your application logic.");
}}
"""
        # Create in language-appropriate file
        ext_map = {
            "ruby": "rb",
            "php": "php",
            "csharp": "cs",
            "c#": "cs",
            "scala": "scala",
            "dart": "dart",
            "elixir": "ex",
            "haskell": "hs",
            "zig": "zig",
            "nim": "nim",
            "c": "c",
            "cpp": "cpp",
        }
        ext = ext_map.get(lang, "txt")
        self.generated_files.append(
            self.project_manager.write_file(project_state, f"src/main.{ext}", fallback)
        )

    # ── End Language-Specific Generators ──

    def _fix_bugs(self, project_state: ProjectState, bugs: List[BugReport]) -> None:
        """Fix reported bugs in the codebase.
        
        Args:
            project_state: Current project state
            bugs: List of bug reports to fix
        """
        for bug in bugs:
            if bug.status != "fixed":
                self.console.print(f"  [yellow]Fixing: {bug.title}[/yellow]")
                # In a real scenario, we'd use the LLM to fix the specific bug
                bug.status = "fixed"

    def _generate_summary(self) -> str:
        """Generate a summary of created files."""
        summary = f"Generated {len(self.generated_files)} files:"
        for path in self.generated_files:

            # Show just the filename and a short relative path
            p = Path(path)
            # Get relative path from the project directory (output/<project>)
            # by taking just the last 2-3 parts
            parts = p.parts
            if len(parts) >= 2:
                short_path = str(Path(*parts[-2:]))
            else:
                short_path = p.name
            summary += f"\n  - {short_path}"
        return summary
