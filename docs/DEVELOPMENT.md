# Development Guidelines

## Code Style & Best Practices

### Python (Backend)

#### Naming Conventions
```python
# Variables & functions: snake_case
user_id = "123"
def get_user_documents():
    pass

# Classes: PascalCase
class DocumentRepository:
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 100 * 1024 * 1024

# Private methods: _leading_underscore
def _validate_file(self, file):
    pass
```

#### Code Organization
```python
# 1. Imports
from typing import Optional
from sqlalchemy.orm import Session
from app.models import Document

# 2. Type hints (always use)
def create_document(
    db: Session,
    title: str,
    owner_id: str
) -> Document:
    pass

# 3. Docstrings
def get_user_documents(user_id: str) -> List[Document]:
    """
    Get all documents for a specific user.
    
    Args:
        user_id: User UUID
    
    Returns:
        List of Document objects
    
    Raises:
        ValueError: If user_id is invalid
    """
    pass
```

### JavaScript/React (Frontend)

#### Component Structure
```jsx
// 1. Imports
import React, { useState } from 'react';
import styles from './Component.module.css';

// 2. Component definition
export const MyComponent = ({ prop1, prop2 }) => {
  const [state, setState] = useState('');
  
  // 3. Effects
  React.useEffect(() => {
    // Setup
  }, [dependencies]);
  
  // 4. Handlers
  const handleClick = () => {
    setState('new value');
  };
  
  // 5. Render
  return <div onClick={handleClick}>{state}</div>;
};

export default MyComponent;
```

#### File Naming
```
Components: PascalCase.jsx
  ✅ Upload.jsx
  ✅ FileList.jsx
  
Services: camelCase.js
  ✅ api.js
  ✅ authService.js

Hooks: camelCase.js
  ✅ useAuth.js
  ✅ useDocuments.js
```

### Dart/Flutter (Mobile)

#### Class & Function Naming
```dart
// Classes: PascalCase
class DocumentService {
  // Methods: camelCase
  Future<Document> getDocument(String id) async {
    // Local variables: camelCase
    final document = await fetchDocument(id);
    return document;
  }
  
  // Private methods: _leadingUnderscore
  Future<List<Document>> _parseDocuments(Response response) async {
    // ...
  }
}
```

## Git Workflow

### Branch Naming
```bash
feature/add-user-authentication
bugfix/fix-file-upload-error
hotfix/security-patch
refactor/improve-api-performance
docs/update-readme
```

### Commit Messages
```bash
# Good
git commit -m "feat: add JWT token refresh mechanism"
git commit -m "fix: correct file size validation"
git commit -m "docs: update deployment guide"

# Bad
git commit -m "update"
git commit -m "fix stuff"
git commit -m "wip"
```

### Commit Message Format
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## Code Review Checklist

### Backend
- [ ] Tests written
- [ ] Type hints present
- [ ] Docstrings complete
- [ ] Security checks included
- [ ] Logging implemented
- [ ] Database migrations created
- [ ] Error handling proper
- [ ] No hardcoded values

### Frontend
- [ ] Components reusable
- [ ] Proper error handling
- [ ] Loading states shown
- [ ] Responsive design
- [ ] Accessibility considered
- [ ] No console errors
- [ ] Performance optimized

### Mobile
- [ ] Null safety enforced
- [ ] Error handling complete
- [ ] User feedback provided
- [ ] Memory efficient
- [ ] Proper state management

## Testing Best Practices

### Backend Testing
```python
# Use fixtures for test data
@pytest.fixture
def test_user():
    return {"id": "test-id", "username": "test"}

def test_create_document(test_user):
    # Arrange
    service = DocumentService(mock_repo)
    
    # Act
    result = service.create_document(test_user['id'], "Title")
    
    # Assert
    assert result.title == "Title"
    assert result.owner_id == test_user['id']
```

### Frontend Testing
```jsx
import { render, screen, userEvent } from '@testing-library/react';
import Upload from './Upload';

test('should upload file', async () => {
  render(<Upload onSuccess={jest.fn()} />);
  const button = screen.getByText('Upload');
  
  await userEvent.click(button);
  
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

## Performance Checklist

### Backend
- [ ] Database queries optimized
- [ ] Indexes on frequently queried columns
- [ ] Connection pooling configured
- [ ] Async operations used
- [ ] Caching implemented for hot paths
- [ ] Pagination enforced

### Frontend
- [ ] Bundle size < 200KB
- [ ] Images optimized
- [ ] Code splitting used
- [ ] Lazy loading implemented
- [ ] No unnecessary re-renders
- [ ] API calls debounced

### Mobile
- [ ] Images cached
- [ ] Unnecessary rebuilds prevented
- [ ] Memory leaks avoided
- [ ] Loading indicators shown
- [ ] Offline support considered

## Documentation Requirements

- [ ] README with setup instructions
- [ ] API documentation with examples
- [ ] Architecture diagram
- [ ] Database schema documented
- [ ] Environment variables documented
- [ ] Deployment guide
- [ ] Troubleshooting guide

## Security Checklist

- [ ] No secrets in code
- [ ] HTTPS enforced
- [ ] JWT tokens used
- [ ] Input validation done
- [ ] SQL injection prevented (use ORM)
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Logs don't contain sensitive data
- [ ] Files uploaded safely
- [ ] Sensitive data encrypted
