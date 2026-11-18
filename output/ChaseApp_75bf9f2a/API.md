# API Documentation

## Overview
API documentation for ChaseApp.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

### Register
Creates a new user account.

```http
POST /api/auth/register
Content-Type: application/json

{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "securepassword123"
}
```

**Response**: `201 Created`
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### Login
Authenticates a user and returns a JWT token.

```http
POST /api/auth/login
Content-Type: application/json

{
    "username": "johndoe",
    "password": "securepassword123"
}
```

**Response**: `200 OK`
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
}
```

### Get Current User
Returns the authenticated user's profile.

```http
GET /api/auth/me
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
}
```

## Items

### List Items
Retrieves a paginated list of items.

```http
GET /api/items?page=1&page_size=10
Authorization: Bearer {token}
```

**Response**: `200 OK`
```json
{
    "items": [
        {
            "id": 1,
            "title": "Sample Item",
            "description": "This is a sample item",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ],
    "total": 1,
    "page": 1,
    "page_size": 10
}
```

### Create Item
Creates a new item.

```http
POST /api/items
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "New Item",
    "description": "Item description"
}
```

**Response**: `201 Created`
```json
{
    "id": 2,
    "user_id": 1,
    "title": "New Item",
    "description": "Item description",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Item
Retrieves a specific item by ID.

```http
GET /api/items/{id}
Authorization: Bearer {token}
```

### Update Item
Updates an existing item.

```http
PUT /api/items/{id}
Content-Type: application/json
Authorization: Bearer {token}

{
    "title": "Updated Title",
    "description": "Updated description"
}
```

### Delete Item
Deletes an item.

```http
DELETE /api/items/{id}
Authorization: Bearer {token}
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
