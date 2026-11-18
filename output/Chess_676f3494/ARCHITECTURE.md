# Architecture Design

## Technology Stack
- **Language**: python
- **Backend Framework**: fastapi
- **Database**: sqlite
- **ORM**: sqlalchemy

## Project Structure
```
project/
├── app/
│   ├── __init__.py
│   ├── main.py          # Application entry point
│   ├── config.py        # Configuration
│   ├── models.py        # Database models
│   ├── schemas.py       # Pydantic schemas
│   ├── routes/          # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── items.py
│   ├── services/        # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   └── item_service.py
│   └── templates/       # HTML templates (if applicable)
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   └── test_items.py
├── requirements.txt
└── README.md
```

## Database Schema

### Users Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, Auto-increment |
| username | String(50) | UNIQUE, NOT NULL |
| email | String(100) | UNIQUE, NOT NULL |
| password_hash | String(255) | NOT NULL |
| created_at | DateTime | NOT NULL, DEFAULT NOW() |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() |

### Items Table
| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, Auto-increment |
| user_id | Integer | FK -> users.id, NOT NULL |
| title | String(200) | NOT NULL |
| description | Text | NULLABLE |
| created_at | DateTime | NOT NULL, DEFAULT NOW() |
| updated_at | DateTime | NOT NULL, DEFAULT NOW() |

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user profile

### Items CRUD
- `GET /api/items` - List all items (paginated)
- `POST /api/items` - Create new item
- `GET /api/items/{id}` - Get item by ID
- `PUT /api/items/{id}` - Update item
- `DELETE /api/items/{id}` - Delete item

## Authentication Flow
1. User registers with username, email, password
2. User logs in with credentials
3. Server returns JWT access token
4. Client includes token in Authorization header
5. Server validates token for protected routes
