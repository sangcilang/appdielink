# API Documentation

## Base URL
```
Development: http://localhost:8000/api/v1
Production: https://api.yourdomain.com/api/v1
```

## Authentication
All endpoints (except `/auth/login`) require JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "token_type": "bearer"
}
```

### Refresh Token
```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGci..."
}
```

### Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh_token": "eyJhbGci..."
}
```

---

## Document Endpoints

### Upload Document
```http
POST /documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <binary>
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "document",
  "description": null,
  "file_size": 1024000,
  "file_type": "pdf",
  "owner_id": "550e8400-e29b-41d4-a716-446655440001",
  "is_public": false,
  "created_at": "2024-01-15T10:30:00",
  "updated_at": "2024-01-15T10:30:00"
}
```

### List Documents
```http
GET /documents/?skip=0&limit=100
Authorization: Bearer <access_token>
```

**Response:**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "document1",
    "file_size": 1024000,
    ...
  }
]
```

### Get Document Details
```http
GET /documents/{document_id}
Authorization: Bearer <access_token>
```

### Update Document
```http
PUT /documents/{document_id}
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "title": "New Title",
  "description": "New description",
  "is_public": true
}
```

### Delete Document
```http
DELETE /documents/{document_id}
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

---

## Access Control Endpoints

### Share Document
```http
POST /access/documents/{document_id}/share
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "user_ids": ["550e8400-e29b-41d4-a716-446655440002"]
}
```

### Make Document Public
```http
POST /access/documents/{document_id}/make-public
Authorization: Bearer <access_token>
```

### Make Document Private
```http
POST /access/documents/{document_id}/make-private
Authorization: Bearer <access_token>
```

### Get Document Permissions
```http
GET /access/documents/{document_id}/permissions
Authorization: Bearer <access_token>
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "File size exceeds maximum limit"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or expired token"
}
```

### 403 Forbidden
```json
{
  "detail": "You don't have permission to access this resource"
}
```

### 404 Not Found
```json
{
  "detail": "Document not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting
- General endpoints: 100 req/s per IP
- API endpoints: 30 req/s per IP
- Headers included: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

## CORS
Allowed origins can be configured in `.env`:
```
CORS_ORIGINS=["http://localhost:3000","https://yourdomain.com"]
```

## Pagination
Default: `skip=0, limit=100`
Maximum limit: 1000 items per page

## Timestamps
All timestamps use ISO 8601 format: `2024-01-15T10:30:00`
