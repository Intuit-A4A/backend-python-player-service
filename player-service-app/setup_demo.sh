#!/bin/bash

# Player Service Demo Setup Script
# This script sets up everything needed for the Intuit interview demo

set -e  # Exit on error

echo "🚀 Setting up Player Service Demo Environment..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check Python version
echo "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check if Redis is installed
echo ""
echo "Checking Redis..."
if command -v redis-cli &> /dev/null; then
    print_success "Redis CLI found"
    
    # Try to ping Redis
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis is installed but not running"
        echo "Starting Redis..."
        
        # Try to start Redis
        if command -v brew &> /dev/null; then
            brew services start redis
            sleep 2
            if redis-cli ping &> /dev/null; then
                print_success "Redis started successfully"
            else
                print_error "Failed to start Redis"
            fi
        else
            print_warning "Please start Redis manually: redis-server"
        fi
    fi
else
    print_warning "Redis not found"
    echo "Installing Redis (this may take a few minutes)..."
    
    if command -v brew &> /dev/null; then
        brew install redis
        brew services start redis
        sleep 2
        print_success "Redis installed and started"
    else
        print_error "Homebrew not found. Please install Redis manually:"
        echo "  macOS: brew install redis"
        echo "  Ubuntu: sudo apt-get install redis-server"
        echo "  Or use Docker: docker run -d -p 6379:6379 --name redis redis:latest"
    fi
fi

# Create virtual environment
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d "env" ]; then
    python3 -m venv env
    print_success "Virtual environment created"
else
    print_warning "Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate
print_success "Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Check if Player.csv exists
echo ""
echo "Checking data files..."
if [ -f "Player.csv" ]; then
    print_success "Player.csv found"
else
    print_error "Player.csv not found. Database initialization may fail."
fi

# Create .env file if it doesn't exist
echo ""
echo "Setting up environment variables..."
if [ ! -f ".env" ]; then
    if [ -f "../.env.example" ]; then
        cp ../.env.example .env
        print_success ".env file created from template"
        print_warning "Please update .env with your configuration"
    else
        print_warning ".env.example not found, skipping .env creation"
    fi
else
    print_warning ".env already exists"
fi

# Remove old database to start fresh
echo ""
echo "Cleaning up old database..."
if [ -f "player.db" ]; then
    rm player.db
    print_success "Old database removed"
fi

# Test imports
echo ""
echo "Testing Python imports..."
python3 -c "import flask; import pandas; import redis; import jwt" 2>/dev/null
if [ $? -eq 0 ]; then
    print_success "All required packages are importable"
else
    print_error "Some packages failed to import"
    exit 1
fi

# Check Ollama (optional)
echo ""
echo "Checking Ollama (optional for AI demo)..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q ollama; then
        print_success "Ollama container is running"
    else
        print_warning "Ollama container not running"
        echo "To start Ollama for AI demo, run:"
        echo "  docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama"
        echo "  docker exec -it ollama ollama run tinyllama"
    fi
else
    print_warning "Docker not found. Ollama features will not be available."
fi

# Final summary
echo ""
echo "============================================"
echo "🎉 Demo Environment Setup Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "1. Review the implementation files:"
echo "   - INTERVIEW_PREP_GUIDE.md (concepts & explanations)"
echo "   - DEMO_IMPLEMENTATION.md (code to implement)"
echo "   - CHEAT_SHEET.md (day-of quick reference)"
echo ""
echo "2. Start the application:"
echo "   python3 app.py"
echo ""
echo "3. Test the application:"
echo "   curl http://localhost:8000/health"
echo ""
echo "4. Login to get a token:"
echo "   curl -X POST http://localhost:8000/v1/auth/login \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d '{\"email\": \"admin@intuit.com\", \"password\": \"admin123\"}'"
echo ""
echo "5. Run tests:"
echo "   pytest test_demo.py -v"
echo ""
echo "Good luck with your interview! 🚀"
echo ""

