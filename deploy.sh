#!/bin/bash
# Deployment script for Link1Die

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Link1Die Deployment Script${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}"
else
    echo -e "${RED}❌ .env file not found${NC}"
    exit 1
fi

# Build services
echo -e "${YELLOW}Building services...${NC}"
docker-compose -f docker/docker-compose.yml build

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 5

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose -f docker/docker-compose.yml exec -T api alembic upgrade head

# Health check
echo -e "${YELLOW}Health Check...${NC}"
API_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$API_HEALTH" = "200" ]; then
    echo -e "${GREEN}✓ API Health Check: OK${NC}"
else
    echo -e "${RED}❌ API Health Check: Failed (Status: $API_HEALTH)${NC}"
    exit 1
fi

DB_CHECK=$(docker-compose -f docker/docker-compose.yml exec -T db pg_isready -U postgres)
if [[ $DB_CHECK == *"accepting connections"* ]]; then
    echo -e "${GREEN}✓ Database: OK${NC}"
else
    echo -e "${RED}❌ Database check failed${NC}"
    exit 1
fi

# Display service status
echo -e "${YELLOW}Service Status:${NC}"
docker-compose -f docker/docker-compose.yml ps

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo -e "${YELLOW}Services Available:${NC}"
echo "  API: http://localhost:8000"
echo "  Docs: http://localhost:8000/docs"
echo "  Web: http://localhost:80"
echo "  Database: localhost:5432 (postgres:password)"
echo "  Redis: localhost:6379"
echo ""
echo -e "${YELLOW}Useful Commands:${NC}"
echo "  View logs: docker-compose -f docker/docker-compose.yml logs -f api"
echo "  Stop services: docker-compose -f docker/docker-compose.yml down"
echo "  Database shell: docker-compose -f docker/docker-compose.yml exec db psql -U postgres -d link1die_db"
