# 🏗️ Architecture & Design Patterns

## Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│         Presentation Layer (API)         │
│  - HTTP Endpoints                        │
│  - Request/Response Handling             │
│  - Input Validation (Pydantic Schemas)  │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       Business Logic Layer (Service)     │
│  - Token Generation                      │
│  - File Processing                       │
│  - Authorization Checks                  │
│  - Business Rules                        │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    Data Access Layer (Repository)        │
│  - Database Queries                      │
│  - CRUD Operations                       │
│  - Data Transformation                   │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       Database Layer                     │
│  - PostgreSQL                            │
│  - Tables & Indexes                      │
└─────────────────────────────────────────┘
```

## Request Flow Example: Upload File

```
1. Client Upload Request
        ↓
2. API Endpoint (document.py)
   - Receive file
   - Validate format/size with Pydantic
        ↓
3. Service Layer (file_service.py, document_service)
   - Validate file
   - Save to storage
   - Generate metadata
        ↓
4. Repository Layer (document_repo.py)
   - Create document record in DB
   - Return Document model
        ↓
5. Response
   - DocumentResponse schema
   - JSON response to client
```

## Design Patterns Used

### 1. **Repository Pattern**
- **Purpose**: Abstract database access
- **Location**: `app/repositories/`
- **Benefits**: Easy testing, database agnostic, centralized queries
```python
# Usage
doc_repo = DocumentRepository(db)
documents = doc_repo.get_user_documents(user_id)
```

### 2. **Service Layer Pattern**
- **Purpose**: Contain business logic
- **Location**: `app/services/`
- **Benefits**: Reusable across endpoints, testable, single responsibility
```python
# Usage
token_service = TokenService(token_repo)
tokens = token_service.create_tokens(user_id)
```

### 3. **Dependency Injection**
- **Purpose**: Loose coupling, testability
- **FastAPI Feature**: `Depends()`
```python
@router.post("/documents/")
async def create(
    file: UploadFile,
    db: Session = Depends(get_db)  # Dependency injection
):
    pass
```

### 4. **Middleware Pattern**
- **Purpose**: Cross-cutting concerns
- **Usage**: CORS, logging, error handling
```python
app.add_middleware(CORSMiddleware, ...)
```

### 5. **Schema Validation Pattern**
- **Purpose**: Data validation & serialization
- **Location**: `app/schemas/`
- **Library**: Pydantic
```python
class DocumentCreate(BaseModel):
    title: str
    description: Optional[str]
    # Automatic validation
```

## Database Design Principles

### ✅ Normalization
- No duplicate data
- Proper relationships (Foreign Keys)

### ✅ Indexing
- Index frequently queried columns
- `owner_id`, `title` indexed in documents table
- `user_id` indexed in tokens table

### ✅ Soft Deletes (Future)
- Add `deleted_at` timestamp
- Don't physically delete records
- Better audit trail

### ✅ Timestamps
- `created_at`: Immutable record creation
- `updated_at`: Automatically updated

## Security Architecture

```
┌─────────────────────────────┐
│    Client Request            │
└──────────────┬──────────────┘
               ↓
         HTTPS/TLS
               ↓
    ┌──────────────────┐
    │  Nginx (Reverse) │
    │  - SSL/TLS       │
    │  - Rate Limit    │
    │  - Headers       │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  FastAPI App     │
    │  - JWT Validation│
    │  - Cors Check    │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Service Layer   │
    │  - Auth Check    │
    │  - Permissions   │
    └────────┬─────────┘
             ↓
         Database
```

## Testing Strategy

### Unit Tests
- Test individual functions
- Mock dependencies
- Location: `tests/unit/`

### Integration Tests
- Test components together
- Use test database
- Location: `tests/integration/`

### E2E Tests
- Full request/response cycle
- Real database
- Location: `tests/e2e/`

## Error Handling

```python
# Centralized error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
```

## Logging Strategy

```python
# Structured logging
logger.info(
    "Document uploaded",
    extra={
        "user_id": user_id,
        "file_size": file_size,
        "duration_ms": duration
    }
)
```

## Performance Optimizations

### 1. Database
- Connection pooling (20 connections)
- Indexed queries
- Pagination (limit 100 items)

### 2. Caching
- Redis for session storage
- Token caching

### 3. Compression
- Gzip compression in Nginx
- Reduce payload size

### 4. Async Operations
- FastAPI async endpoints
- Non-blocking I/O

## Scalability Path

### Stage 1 (Current)
- Single monolith
- Shared database
- In-memory cache

### Stage 2 (Soon)
- API auto-scaling
- Load balancer
- Database read replicas
- S3 for file storage

### Stage 3 (Future)
- Microservices
- Message queues (RabbitMQ/Kafka)
- Event-driven architecture
- Multi-region deployment
