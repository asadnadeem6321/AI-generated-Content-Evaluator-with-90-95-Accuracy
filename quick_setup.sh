#!/bin/bash

# AI Detection Backend - Quick Setup Script
# This script automates the initial setup process

set -e  # Exit on error

echo "🚀 AI Detection Backend - Quick Setup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version || { echo -e "${RED}Python 3 is required${NC}"; exit 1; }

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements/dev.txt

# Create directories
echo -e "${BLUE}Creating directories...${NC}"
mkdir -p media/uploads
mkdir -p media/reports
mkdir -p static
mkdir -p logs
touch logs/.gitkeep

# Copy environment file
echo -e "${BLUE}Setting up environment variables...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}.env file created. Please update with your settings.${NC}"
else
    echo -e "${BLUE}.env file already exists.${NC}"
fi

# Check PostgreSQL
echo -e "${BLUE}Checking PostgreSQL...${NC}"
if command -v psql &> /dev/null; then
    echo -e "${GREEN}PostgreSQL is installed${NC}"
else
    echo -e "${RED}PostgreSQL not found. Please install it:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install postgresql"
    echo "  macOS: brew install postgresql"
fi

# Check Redis
echo -e "${BLUE}Checking Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}Redis is running${NC}"
    else
        echo -e "${RED}Redis is installed but not running. Start it with:${NC}"
        echo "  Linux: sudo service redis-server start"
        echo "  macOS: brew services start redis"
    fi
else
    echo -e "${RED}Redis not found. Please install it:${NC}"
    echo "  Ubuntu/Debian: sudo apt-get install redis-server"
    echo "  macOS: brew install redis"
fi

# Run migrations
echo -e "${BLUE}Running database migrations...${NC}"
python manage.py migrate

# Create superuser (optional)
echo -e "${BLUE}Would you like to create a superuser? (y/n)${NC}"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run: python manage.py runserver"
echo "3. Visit: http://localhost:8000/health/"
echo "4. Admin: http://localhost:8000/admin/"
echo "5. API Docs: http://localhost:8000/api/docs/"
echo ""
echo "For Celery worker:"
echo "  celery -A config worker -l info"
echo ""