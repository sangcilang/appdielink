#!/bin/bash
# Backend development setup script

echo "Setting up Link1Die Backend..."

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file (please update with your configuration)"
fi

# Create necessary directories
mkdir -p logs uploads

# Run migrations
echo "Running database migrations..."
alembic upgrade head

echo "✓ Backend setup complete!"
echo "To start development server: python app/main.py"
