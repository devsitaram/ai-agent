"""Agent 5: Documentation Agent - Generates complete project documentation."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from core.base_agent import BaseAgent
from core.llm_interface import LLMInterface
from core.project_manager import ProjectManager
from schema import AgentResult, AgentStatus, ProjectState, ProjectStatus


class DocumentationAgent(BaseAgent):
    """Generates comprehensive project documentation."""

    def __init__(
        self,
        llm_interface: Optional[LLMInterface] = None,
        project_manager: Optional[ProjectManager] = None,
    ):
        super().__init__(
            name="documentation",
            description="Generating project documentation and guides",
        )
        self.llm = llm_interface or LLMInterface()
        self.project_manager = project_manager or ProjectManager()

    def validate(self, project_state: ProjectState) -> bool:
        """Validate that QA is completed."""
        qa_result = project_state.get_agent_result("qa")
        if qa_result.status != AgentStatus.COMPLETED:
            raise ValueError("QA not completed. Run QA agent first.")
        return True

    def process(self, project_state: ProjectState) -> ProjectState:
        """Process the project and generate documentation.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state with documentation
        """
        generated_docs = []

        # Gather project information
        requirements = self.project_manager.read_file(project_state, "REQUIREMENTS.md") or ""
        architecture = self.project_manager.read_file(project_state, "ARCHITECTURE.md") or ""
        qa_report = self.project_manager.read_file(project_state, "QA_REPORT.md") or ""
        readme = self.project_manager.read_file(project_state, "README.md") or ""

        project_info = {
            "name": project_state.project_name,
            "description": project_state.user_input[:200] + "...",
            "tech_stack": project_state.tech_stack,
            "created_at": project_state.created_at,
        }

        # Generate API documentation
        self.console.print("[cyan]Generating API documentation...[/cyan]")
        api_docs = self._generate_api_docs(project_state, architecture)
        api_path = self.project_manager.write_file(project_state, "API.md", api_docs)
        generated_docs.append(api_path)

        # Generate/Update comprehensive README
        self.console.print("[cyan]Generating comprehensive README...[/cyan]")
        full_readme = self._generate_comprehensive_readme(project_state, project_info, requirements)
        readme_path = self.project_manager.write_file(project_state, "README.md", full_readme)
        generated_docs.append(readme_path)

        # Generate deployment guide
        self.console.print("[cyan]Generating deployment guide...[/cyan]")
        deploy_docs = self._generate_deployment_guide(project_state, project_info)
        deploy_path = self.project_manager.write_file(project_state, "DEPLOYMENT.md", deploy_docs)
        generated_docs.append(deploy_path)

        # Generate changelog
        self.console.print("[cyan]Generating changelog...[/cyan]")
        changelog = self._generate_changelog(project_state)
        changelog_path = self.project_manager.write_file(project_state, "CHANGELOG.md", changelog)
        generated_docs.append(changelog_path)

        # Generate user guide
        self.console.print("[cyan]Generating user guide...[/cyan]")
        user_guide = self._generate_user_guide(project_state, architecture)
        userguide_path = self.project_manager.write_file(project_state, "USER_GUIDE.md", user_guide)
        generated_docs.append(userguide_path)

        # Update agent result
        agent_result = AgentResult(
            status=AgentStatus.COMPLETED,
            output=f"Generated {len(generated_docs)} documentation files",
            artifacts=generated_docs,
        )
        project_state.set_agent_result(self.name, agent_result)
        project_state.status = ProjectStatus.DOCUMENTATION

        self.console.print(
            f"[green]✓ Generated {len(generated_docs)} documentation files[/green]"
        )
        for doc in generated_docs:
            doc_name = doc.split("/")[-1]
            self.console.print(f"  [dim]• {doc_name}[/dim]")

        return project_state

    def _generate_api_docs(self, project_state: ProjectState, architecture: str) -> str:
        """Generate API documentation.
        
        Args:
            project_state: Current project state
            architecture: Architecture document
            
        Returns:
            API documentation markdown
        """
        tech = project_state.tech_stack
        lang = tech.get("language", "python")
        backend = tech.get("backend", "fastapi")

        return f"""# API Documentation

## Overview
API documentation for {project_state.project_name}.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

### Register
Creates a new user account.

```http
POST /api/auth/register
Content-Type: application/json

{{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
}}
```

**Response**: `201 Created`
```json
{{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2024-01-01T00:00:00Z"
}}
```

### Login
Authenticates a user and returns a JWT token.

```http
POST /api/auth/login
Content-Type: application/json

{{
    "username": "johndoe",
    "password": "securepassword123"
}}
```

**Response**: `200 OK`
```json
{{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}}
```

### Get Current User
Returns the authenticated user's profile.

```http
GET /api/auth/me
Authorization: Bearer {{token}}
```

**Response**: `200 OK`
```json
{{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
}}
```

## Items

### List Items
Retrieves a paginated list of items.

```http
GET /api/items?page=1&page_size=10
Authorization: Bearer {{token}}
```

**Response**: `200 OK`
```json
{{
    "items": [
        {{
            "id": 1,
            "title": "Sample Item",
            "description": "This is a sample item",
            "created_at": "2024-01-01T00:00:00Z"
        }}
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
}}
```

### Create Item
Creates a new item.

```http
POST /api/items
Content-Type: application/json
Authorization: Bearer {{token}}

{{
    "title": "New Item",
    "description": "Item description"
}}
```

**Response**: `201 Created`
```json
{{
    "id": 2,
    "user_id": 1,
    "title": "New Item",
    "description": "Item description",
    "created_at": "2024-01-01T00:00:00Z"
}}
```

### Get Item
Retrieves a specific item by ID.

```http
GET /api/items/{{id}}
Authorization: Bearer {{token}}
```

### Update Item
Updates an existing item.

```http
PUT /api/items/{{id}}
Content-Type: application/json
Authorization: Bearer {{token}}

{{
    "title": "Updated Title",
    "description": "Updated description"
}}
```

### Delete Item
Deletes an item.

```http
DELETE /api/items/{{id}}
Authorization: Bearer {{token}}
```

**Response**: `204 No Content`

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (successful delete) |
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Missing or invalid token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 422 | Unprocessable Entity - Validation error |
| 500 | Internal Server Error |

## Rate Limiting
- 100 requests per minute per user
- 1000 requests per hour per user
"""

    def _generate_comprehensive_readme(
        self, project_state: ProjectState, project_info: dict, requirements: str
    ) -> str:
        """Generate comprehensive README.
        
        Args:
            project_state: Current project state
            project_info: Project information
            requirements: Requirements document
            
        Returns:
            Comprehensive README markdown
        """
        tech = project_state.tech_stack
        lang = tech.get("language", "python")
        backend = tech.get("backend", "fastapi")
        database = tech.get("database", "sqlite")

        return f"""# {project_state.project_name}

> Auto-generated by the AI Software Development Agent System

{project_state.user_input[:200]}

## ✨ Features

- User authentication (register, login, JWT tokens)
- Full CRUD operations
- RESTful API design
- Database persistence with {database}
- Input validation and sanitization
- Comprehensive error handling
- Unit tests with pytest
- Interactive API documentation (Swagger UI)

## 🛠 Tech Stack

| Category | Technology |
|----------|------------|
| **Language** | {lang} |
| **Backend** | {backend} |
| **Database** | {database} |
| **ORM** | {tech.get('orm', 'N/A')} |
| **Auth** | JWT (python-jose) |
| **Testing** | pytest |

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd {project_state.project_name.lower().replace(' ', '-')}

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
# (Auto-created on first run)

# Start the development server
python -m app.main
```

The server will start at `http://localhost:8000`.

## 📖 Usage

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Quick Start

1. **Register a user**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \\
     -H "Content-Type: application/json" \\
     -d '{{"username": "demo", "email": "demo@example.com", "password": "demo123"}}'
   ```

2. **Login to get token**
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \\
     -H "Content-Type: application/json" \\
     -d '{{"username": "demo", "password": "demo123"}}'
   ```

3. **Use the token for authenticated requests**
   ```bash
   curl http://localhost:8000/api/items \\
     -H "Authorization: Bearer YOUR_TOKEN_HERE"
   ```

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app -v

# Run specific test file
pytest tests/test_main.py -v
```

## 📁 Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── models.py            # SQLAlchemy database models
│   ├── schemas.py           # Pydantic validation schemas
│   └── routes/              # API route handlers
│       └── __init__.py
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_main.py         # Main application tests
│   ├── test_models.py       # Database model tests
│   └── test_schemas.py      # Schema validation tests
├── requirements.txt
├── README.md
├── API.md
├── DEPLOYMENT.md
├── CHANGELOG.md
└── QA_REPORT.md
```

## 🔒 Security

- Passwords hashed with bcrypt
- JWT tokens for authentication
- CORS configurable for production
- Input validation on all endpoints
- SQL injection protection via ORM

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Generated by [AI Software Development Agent System](https://github.com/ai-dev-agent)
"""

    def _generate_deployment_guide(
        self, project_state: ProjectState, project_info: dict
    ) -> str:
        """Generate deployment guide.
        
        Args:
            project_state: Current project state
            project_info: Project information
            
        Returns:
            Deployment guide markdown
        """
        return f"""# Deployment Guide

## Prerequisites

- Python 3.11+
- pip
- A server or cloud platform account

## Environment Variables

Create a `.env` file in the project root:

```env
# Application
DEBUG=false
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./app.db

# Optional: Use PostgreSQL in production
# DATABASE_URL=postgresql://user:password@localhost/dbname

# CORS
ALLOWED_ORIGINS=https://your-domain.com
```

## Local Deployment

### Using Uvicorn

```bash
# Install production dependencies
pip install -r requirements.txt

# Run with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Gunicorn (Linux)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn app.main:app --worker-class uvicorn.workers.UvicornWorker \\
  --bind 0.0.0.0:8000 --workers 4
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - SECRET_KEY=change-in-production
    volumes:
      - ./data:/app/data
```

### Build and Run

```bash
docker build -t myapp .
docker run -p 8000:8000 myapp
```

## Cloud Deployment

### Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Add `vercel.json`:
```json
{{
  "builds": [
    {{
      "src": "app/main.py",
      "use": "@vercel/python"
    }}
  ],
  "routes": [
    {{
      "src": "/(.*)",
      "dest": "app/main.py"
    }}
  ]
}}
```
3. Run `vercel --prod`

### Railway

1. Push code to GitHub
2. Create new project on [Railway](https://railway.app)
3. Connect your GitHub repository
4. Set environment variables
5. Railway auto-detects Python/FastAPI

### Render

1. Create a new Web Service on [Render](https://render.com)
2. Connect your repository
3. Set:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Monitoring

### Health Check
The application provides a health check endpoint at `/health`.

### Logging
Logs are output to stdout by default. Configure file logging in production:

```bash
uvicorn app.main:app --log-level info --log-config logging.conf
```

## Backup

### Database Backup
```bash
# SQLite
cp app.db app.db.backup

# PostgreSQL
pg_dump dbname > backup.sql
```

## Scaling

- Increase workers: `--workers 8`
- Use PostgreSQL for better concurrency
- Add caching with Redis
- Use a reverse proxy (nginx) for production
"""

    def _generate_changelog(self, project_state: ProjectState) -> str:
        """Generate changelog.
        
        Args:
            project_state: Current project state
            
        Returns:
            Changelog markdown
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return f"""# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - {today}

### Added
- Initial release of {project_state.project_name}
- User authentication system with JWT tokens
- Full CRUD API endpoints
- Database models with SQLAlchemy ORM
- Input validation with Pydantic schemas
- Comprehensive test suite
- Interactive API documentation (Swagger/ReDoc)
- CORS middleware configuration
- Health check endpoint
- Error handling middleware

### Technical Details
- **Framework**: FastAPI
- **Database**: SQLite (SQLAlchemy)
- **Auth**: JWT with bcrypt password hashing
- **Testing**: pytest with HTTPX TestClient

## [Unreleased]

### Planned Features
- Rate limiting
- Email notifications
- File upload support
- Search functionality
- API versioning
- Caching with Redis
- WebSocket support for real-time features
"""

    def _generate_user_guide(self, project_state: ProjectState, architecture: str) -> str:
        """Generate user guide.
        
        Args:
            project_state: Current project state
            architecture: Architecture document
            
        Returns:
            User guide markdown
        """
        return f"""# User Guide

## Introduction

Welcome to {project_state.project_name}! This guide will help you understand and use the application effectively.

## Getting Started

### Accessing the Application

1. **Start the server** (see [README.md](README.md) for installation)
2. Open your browser to `http://localhost:8000`
3. The API documentation is available at `http://localhost:8000/docs`

### Creating an Account

1. Send a POST request to `/api/auth/register` with:
   ```json
   {{
     "username": "yourusername",
     "email": "your@email.com",
     "password": "yourpassword"
   }}
   ```
2. You'll receive your user details in response

### Authentication

1. Login at `/api/auth/login` with your credentials
2. You'll receive a JWT token
3. Include this token in all subsequent requests:
   ```
   Authorization: Bearer YOUR_TOKEN
   ```

## Using the API

### Managing Items

Items are the core data objects in the application.

#### Creating an Item
```http
POST /api/items
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{{
    "title": "My First Item",
    "description": "This is my first item"
}}
```

#### Viewing Items
```http
GET /api/items
Authorization: Bearer YOUR_TOKEN
```

#### Updating an Item
```http
PUT /api/items/1
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{{
    "title": "Updated Title"
}}
```

#### Deleting an Item
```http
DELETE /api/items/1
Authorization: Bearer YOUR_TOKEN
```

## Troubleshooting

### Common Issues

| Problem | Solution |
|---------|----------|
| Cannot connect to server | Ensure the server is running on port 8000 |
| Authentication failed | Check your token is valid and not expired |
| 422 Validation Error | Check your request body matches the expected format |
| 404 Not Found | The resource ID may be incorrect |

### Getting Help

If you encounter issues:
1. Check the API documentation at `/docs`
2. Review the test files for usage examples
3. Check the server logs for error messages

## Best Practices

1. **Use environment variables** for configuration
2. **Keep your token secure** - never share it
3. **Validate data** before sending requests
4. **Handle errors** gracefully in your client code
5. **Use pagination** when listing items
"""
