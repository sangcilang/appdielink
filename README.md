# Link1Die - Document Management System

## 🎯 Overview
Link1Die is a modern document management platform built with clean architecture principles. It allows users to upload, manage, share, and control access to their documents.

## 🏗️ Project Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **ORM**: SQLAlchemy
- **Authentication**: JWT (JSON Web Tokens)

### Frontend Stack
- **Web**: React + Vite
- **Mobile**: Flutter

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Web Server**: Nginx

## 📁 Project Structure

```
project/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── endpoints/    # API routes
│   │   │   └── router.py
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # Business logic
│   │   ├── repositories/     # Database layer
│   │   ├── utils/            # Helpers, logging
│   │   └── main.py           # App entry point
│   ├── tests/
│   ├── alembic/              # Database migrations
│   ├── requirements.txt
│   ├── .env
│   └── Dockerfile
│
├── frontend-web/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API client
│   │   └── App.jsx
│   └── package.json
│
├── mobile-app/
│   ├── lib/
│   │   ├── core/             # Config, API client
│   │   ├── features/         # Feature screens
│   │   ├── models/           # Data models
│   │   ├── services/         # Business logic
│   │   └── main.dart
│   └── pubspec.yaml
│
├── docker/
│   ├── docker-compose.yml
│   └── nginx/
│       └── nginx.conf
│
└── docs/
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- Flutter SDK (for mobile development)

### Run with Docker Compose
```bash
# Clone repository
git clone <repo-url>
cd project

# Start all services
docker-compose -f docker/docker-compose.yml up -d

# Services will be available at:
# API: http://localhost:8000
# Web: http://localhost:80
# Database: localhost:5432
# Redis: localhost:6379
```

### Local Development (Backend)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Database migrations
alembic upgrade head

# Run development server
python app/main.py
```

### Local Development (Frontend)

```bash
cd frontend-web

# Install dependencies
npm install

# Set API URL
echo "VITE_API_URL=http://localhost:8000/api/v1" > .env.local

# Run development server
npm run dev
```

### Local Development (Mobile)

```bash
cd mobile-app

# Install dependencies
flutter pub get

# Run app
flutter run
```

## Deploy on Vercel (Backend + Frontend)

This repository is a monorepo. Deploy **2 Vercel projects**:

### 1) Backend (FastAPI)

- **Root Directory**: `backend`
- Entry: `backend/index.py` (served via `backend/vercel.json`)
- Add **Vercel Postgres** to the project (so Vercel injects `POSTGRES_URL`).
- (Optional) Add **Vercel Blob** to the project (for large files / share download streaming).

**Backend environment variables (Vercel Project → Settings → Environment Variables):**
- `VERCEL=1`
- `SECRET_KEY=...` (random long string)
- `ALGORITHM=HS256`
- `CORS_ORIGINS=["https://<your-frontend-domain>"]`
- `PUBLIC_BASE_URL=https://<your-backend-domain>` (so generated share links are public)
- `BLOB_READ_WRITE_TOKEN=...` (only if using Vercel Blob)

After deploy, test:
- `https://<backend-domain>/health`
- `https://<backend-domain>/docs`

### 2) Frontend (React + Vite)

- **Root Directory**: `frontend-web`
- Add **Vercel Blob** to the project if you want uploads > ~4.5MB (client uploads directly to Blob).

**Frontend environment variables:**
- `VITE_API_URL=https://<backend-domain>/api/v1`
- `BACKEND_API_URL=https://<backend-domain>/api/v1` (used by `frontend-web/api/blob/upload.js`)

## Desktop App (Windows - như phần mềm cài trên máy)

Chạy như app desktop (không mở Chrome/Edge) bằng Electron + backend local.

### Yêu cầu
- Node.js 18+
- Python 3.11+

### Build installer .exe

1) Build UI (React) và copy vào backend:
```powershell
cd frontend-web
$env:VITE_API_URL="/api/v1"
npm install
npm run build
Copy-Item -Recurse -Force dist ..\\backend\\web_dist
```

2) Build backend server thành `Link1DieServer.exe`:
```powershell
cd ..\\backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --noconfirm --onefile --name Link1DieServer --add-data "web_dist;web_dist" desktop_server.py
```

3) Build bộ cài Windows (NSIS):
```powershell
cd ..\\desktop-app
npm install
npm run dist
```

Output: `project/desktop-app/dist/Link1Die-Setup-1.0.0.exe`

## 🔐 Security Best Practices

✅ **JWT Token Authentication**
- Access tokens: 30 minutes expiration
- Refresh tokens: 7 days expiration
- Secure token storage in LocalStorage/SharedPreferences

✅ **Password Security**
- Bcrypt hashing for passwords
- Minimum requirements enforced

✅ **CORS Protection**
- Configurable allowed origins
- Credentials validation

✅ **HTTPS/SSL**
- Nginx SSL termination
- Security headers (CSP, X-Frame-Options, etc.)

✅ **Rate Limiting**
- 100 req/s for general endpoints
- 30 req/s for API endpoints

## 📊 Database Schema

### Documents Table
```sql
- id (UUID, PK)
- title (String, indexed)
- description (Text, nullable)
- file_path (String)
- file_size (Integer)
- file_type (String)
- owner_id (UUID, FK, indexed)
- is_public (Boolean)
- created_at (Timestamp)
- updated_at (Timestamp)
```

### Tokens Table
```sql
- id (UUID, PK)
- user_id (UUID, FK, indexed)
- refresh_token (String, unique)
- is_revoked (Boolean)
- created_at (Timestamp)
- expires_at (Timestamp)
```

## 🔄 API Flow

```
Request → API Router → Service Layer → Repository → Database
  ↓           ↓           ↓              ↓            ↓
Validate   Route to    Business      DB Access     Persist
Request    Handler     Logic         Layer         Data
```

## 🚀 Scaling Strategy

### Phase 1 (Current)
- Single server deployment
- PostgreSQL with connection pooling
- Redis for session cache

### Phase 2 (Near Future)
- Kubernetes orchestration
- Celery + Message Queue for async tasks
- Database read replicas
- S3/Azure Blob for file storage

### Phase 3 (Future)
- Microservices architecture
- CDN for static content
- Multi-region deployment
- GraphQL API

## 📝 Key Features

✅ User authentication with JWT
✅ Document upload & management
✅ File sharing & access control
✅ Public link generation
✅ Token refresh mechanism
✅ Request logging
✅ Database migrations
✅ Responsive UI
✅ Mobile app support

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest -v --cov=app
```

### Frontend Tests
```bash
cd frontend-web
npm run test
```

## 📚 Logging

All logs are stored in `backend/logs/app.log` with:
- Request/Response logging
- Error tracking
- Performance metrics
- Rotating file handler (10MB per file, 10 backups)

## 🔧 Environment Variables

See [.env.example](backend/.env.example) for all configuration options.

Critical variables:
- `SECRET_KEY`: JWT signing key (change in production)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `CORS_ORIGINS`: Allowed frontend origins

## 📦 Deployment

### Docker Push
```bash
docker build -t link1die-api:latest ./backend
docker tag link1die-api:latest myregistry/link1die-api:latest
docker push myregistry/link1die-api:latest
```

### Production Deployment
```bash
# Pull latest image
docker pull myregistry/link1die-api:latest

# Start with production compose file
docker-compose -f docker/docker-compose.yml up -d
```

## 🤝 Contributing

1. Create feature branch
2. Follow code style guidelines
3. Write tests for new features
4. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 📞 Support

For issues and questions:
- GitHub Issues: [Project Issues]
- Documentation: [Wiki]
- Email: support@link1die.com
