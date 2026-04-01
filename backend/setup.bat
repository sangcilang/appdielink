@echo off
REM Backend development setup script for Windows

echo Setting up Link1Die Backend...

REM Create virtual environment
python -m venv venv
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Setup environment file
if not exist .env (
    copy .env.example .env
    echo ✓ Created .env file ^(please update with your configuration^)
)

REM Create necessary directories
if not exist logs mkdir logs
if not exist uploads mkdir uploads

REM Run migrations
echo Running database migrations...
alembic upgrade head

echo ✓ Backend setup complete!
echo To start development server: python app/main.py
