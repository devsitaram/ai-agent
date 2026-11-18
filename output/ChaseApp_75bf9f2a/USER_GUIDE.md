# User Guide

## Introduction

Welcome to ChaseApp! This guide will help you understand and use the application effectively.

## Getting Started

### Accessing the Application

1. **Start the server** (see [README.md](README.md) for installation)
2. Open your browser to `http://localhost:8000`
3. The API documentation is available at `http://localhost:8000/docs`

### Creating an Account

1. Send a POST request to `/api/auth/register` with:
   ```json
   {
     "username": "yourusername",
     "email": "your@email.com",
     "password": "yourpassword"
   }
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

{
    "title": "My First Item",
    "description": "This is my first item"
}
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

{
    "title": "Updated Title"
}
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
