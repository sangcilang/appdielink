#!/bin/bash
# Quick local development setup

echo "🚀 Link1Die Development Setup"

# Backend setup
echo "Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Copy env file
cp .env.example .env
echo "✓ Backend setup complete"
echo "Run: cd backend && python app/main.py"

cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend-web
npm install
cp .env.example .env.local
echo "✓ Frontend setup complete"
echo "Run: cd frontend-web && npm run dev"

cd ..

# Mobile setup (optional)
echo ""
echo "Setting up mobile app..."
cd mobile-app
flutter pub get
echo "✓ Mobile setup complete"
echo "Run: cd mobile-app && flutter run"

echo ""
echo "✅ All setup complete!"
echo ""
echo "Commands:"
echo "  Backend: cd backend && python app/main.py"
echo "  Frontend: cd frontend-web && npm run dev"
echo "  Mobile: cd mobile-app && flutter run"
