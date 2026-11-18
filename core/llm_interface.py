"""LLM provider abstraction layer for the AI Development Agent System.

Supports multiple providers: openai, anthropic, ollama, and a mock provider
for testing without API keys.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat conversation to the LLM.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text response
        """
        pass


class MockProvider(LLMProvider):
    """Mock provider for testing without API keys.
    
    Returns template-based responses.
    """

    def __init__(self):
        # Ordered by specificity - more specific keywords first to avoid false matches
        self.responses = [
            ("architecture design", self._mock_architecture),
            ("development agent", self._mock_development),
            ("qa agent", self._mock_qa_report),
            ("documentation agent", self._mock_documentation),
            ("requirements analysis", self._mock_requirements),
            ("requirement", self._mock_requirements),
            ("architecture", self._mock_architecture),
            ("development", self._mock_development),
            ("qa", self._mock_qa_report),
            ("documentation", self._mock_documentation),
        ]

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate mock response based on prompt content."""
        prompt_lower = prompt.lower()
        for key, handler in self.responses:
            if key in prompt_lower:
                return handler(prompt)
        return self._mock_generic(prompt)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Handle chat by extracting last user message."""
        last_msg = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                last_msg = msg["content"]
                break
        return self.generate(last_msg, **kwargs)

    def _mock_requirements(self, prompt: str) -> str:
        return """# Project Requirements

## Overview
A software project based on the user's description.

## Features
1. Core functionality as described
2. User authentication and authorization
3. Data management with CRUD operations
4. API endpoints for external integration
5. Responsive user interface

## Technical Requirements
- RESTful API design
- Database persistence
- Input validation and sanitization
- Error handling and logging
- Unit test coverage

## User Stories
- As a user, I can register and login
- As a user, I can perform core operations
- As an admin, I can manage users and data

## Milestones
1. Project setup and architecture
2. Core feature implementation
3. Testing and QA
4. Documentation and deployment
"""

    def _mock_architecture(self, prompt: str) -> str:
        return """# Architecture Design

## Technology Stack
- **Backend**: Python with FastAPI
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML/CSS/JS with Jinja2 templates
- **Testing**: pytest

## Project Structure
```
project/
├── app/
│   ├── main.py
│   ├── models.py
│   ├── routes/
│   ├── services/
│   └── templates/
├── tests/
├── requirements.txt
└── README.md
```

## Database Schema
- Users table (id, username, email, password_hash, created_at)
- Items table (id, user_id, title, description, created_at, updated_at)

## API Endpoints
- POST /api/auth/register
- POST /api/auth/login
- GET /api/items
- POST /api/items
- GET /api/items/{id}
- PUT /api/items/{id}
- DELETE /api/items/{id}
"""

    def _mock_development(self, prompt: str) -> str:
        return """# Development Summary

## Files Created
1. app/main.py - Application entry point and configuration
2. app/models.py - Database models
3. app/routes/auth.py - Authentication routes
4. app/routes/items.py - CRUD routes for items
5. app/services/auth_service.py - Authentication logic
6. app/services/item_service.py - Item management logic
7. tests/test_auth.py - Authentication tests
8. tests/test_items.py - CRUD tests
9. requirements.txt - Project dependencies
10. README.md - Project documentation

## Implementation Details
- FastAPI application with SQLAlchemy ORM
- JWT-based authentication
- Full CRUD operations with validation
- SQLite database for development
- pytest test suite with 95%+ coverage
"""

    def _mock_qa_report(self, prompt: str) -> str:
        return """# QA Report

## Summary
- **Tests Passed**: 24/25
- **Tests Failed**: 1
- **Security Issues**: 0
- **Performance**: Good

## Failed Tests
1. **test_delete_nonexistent_item** - Returns 404 instead of 400
   - Severity: Low
   - File: tests/test_items.py:120

## Performance
- Startup time: 0.8s
- Memory usage: 45MB
- API response time: <100ms average

## Recommendations
- Fix the HTTP status code for deleting non-existent items
- Add rate limiting for production deployment
"""

    def _mock_documentation(self, prompt: str) -> str:
        return """# Documentation Generated

## Files
1. README.md - Complete project README
2. API.md - API documentation
3. DEPLOYMENT.md - Deployment guide
4. CHANGELOG.md - Version history

## README Includes
- Project overview and features
- Installation and setup instructions
- Configuration guide
- API usage examples
- Testing instructions

## API Documentation
- All endpoints documented with request/response examples
- Authentication flow explained
- Error codes documented

## Deployment Guide
- Local development setup
- Production deployment steps
- Environment variables configuration
"""

    def _mock_generic(self, prompt: str) -> str:
        return f"""# Generated Output

Based on your request, here is the generated content.

## Summary
This is a mock response for testing purposes.

The prompt was: {prompt[:100]}...
"""


class LLMInterface:
    """Main interface for LLM interactions across all agents."""

    def __init__(self, provider: Optional[LLMProvider] = None):
        """Initialize the LLM interface.
        
        Args:
            provider: LLM provider instance. If None, uses MockProvider.
        """
        # Auto-load .env file if it exists
        self._load_env_file()
        self.provider = provider or self._create_provider()

    def _load_env_file(self) -> None:
        """Load environment variables from .env file if it exists."""
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip("'\"")
                        os.environ.setdefault(key, value)

    def _create_provider(self) -> LLMProvider:
        """Create LLM provider based on environment configuration."""
        provider_type = os.environ.get("LLM_PROVIDER", "mock").lower()
        
        if provider_type == "mock":
            return MockProvider()
        elif provider_type == "openai":
            from .providers.openai_provider import OpenAIProvider
            return OpenAIProvider()
        elif provider_type == "deepseek":
            from .providers.openai_provider import OpenAIProvider
            return OpenAIProvider(
                base_url="https://api.deepseek.com/v1",
                model=os.environ.get("OPENAI_MODEL", "deepseek-chat"),
            )
        elif provider_type == "anthropic":
            from .providers.anthropic_provider import AnthropicProvider
            return AnthropicProvider()
        elif provider_type == "ollama":
            from .providers.ollama_provider import OllamaProvider
            return OllamaProvider()
        else:
            print(f"Unknown provider '{provider_type}', using mock")
            return MockProvider()

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from the LLM.
        
        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        return self.provider.generate(prompt, **kwargs)

    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send a chat conversation to the LLM.
        
        Args:
            messages: List of message dicts
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        return self.provider.chat(messages, **kwargs)

    def analyze_requirements(self, user_input: str) -> str:
        """Analyze user input to generate requirements.
        
        Args:
            user_input: User's project description
            
        Returns:
            Generated requirements document
        """
        prompt = f"""You are a Requirements Analysis Agent. Analyze the following project idea and generate a complete requirements specification.

User's Project Idea:
{user_input}

Generate a comprehensive requirements document including:
1. Project Overview
2. Core Features
3. User Stories
4. Technical Requirements
5. Development Milestones

Output in markdown format."""
        return self.generate(prompt)

    def design_architecture(self, requirements: str, user_input: str) -> str:
        """Design architecture based on requirements.
        
        Args:
            requirements: The requirements document
            user_input: Original user input
            
        Returns:
            Generated architecture document
        """
        prompt = f"""You are an Architecture Design Agent. Based on the following requirements, design a complete technical architecture.

User's Original Request:
{user_input}

Requirements:
{requirements}

Generate an architecture document including:
1. Technology Stack (appropriate for the project type)
2. Project Structure
3. Database Schema
4. API Design
5. UI Design

Output in markdown format."""
        return self.generate(prompt)

    def generate_code(self, architecture: str, requirements: str, user_input: str) -> str:
        """Generate code based on architecture.
        
        Args:
            architecture: Architecture document
            requirements: Requirements document
            user_input: Original user input
            
        Returns:
            Generated code summary and file list
        """
        prompt = f"""You are a Development Agent. Based on the following architecture, generate complete source code for the project.

User's Request:
{user_input}

Architecture:
{architecture}

Requirements:
{requirements}

Generate the complete project with:
1. All source files with full implementation
2. Unit tests
3. Configuration files
4. Build/package files

List each file and its complete contents."""
        return self.generate(prompt)

    def run_qa(self, code_summary: str, requirements: str) -> str:
        """Run QA analysis on generated code.
        
        Args:
            code_summary: Summary of generated code
            requirements: Requirements document
            
        Returns:
            QA report
        """
        prompt = f"""You are a QA Agent. Analyze the following project and generate a QA report.

Code:
{code_summary}

Requirements:
{requirements}

Generate a QA report including:
1. Test results summary
2. Failed tests and bugs
3. Security findings
4. Performance metrics
5. Recommendations

Output in markdown format."""
        return self.generate(prompt)

    def generate_documentation(self, project_info: str) -> str:
        """Generate project documentation.
        
        Args:
            project_info: Project information summary
            
        Returns:
            Generated documentation
        """
        prompt = f"""You are a Documentation Agent. Generate complete documentation for the following project.

Project Info:
{project_info}

Generate:
1. README.md - Project overview, setup, and usage
2. API.md - API documentation
3. DEPLOYMENT.md - Deployment instructions
4. CHANGELOG.md - Version history

Output in markdown format."""
        return self.generate(prompt)
