#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

# Colors & Formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper functions for clean logging
log_info() {
    echo -e "${BLUE}${BOLD}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}${BOLD}✔${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}${BOLD}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}${BOLD}✘${NC} $1"
}

print_header() {
    clear
    echo -e "${CYAN}${BOLD}┌────────────────────────────────────────────────────────┐${NC}"
    echo -e "${CYAN}${BOLD}│          Django Development Server Helper              │${NC}"
    echo -e "${CYAN}${BOLD}└────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

print_header

# 1. Check if virtual environment exists, create if missing
if [ ! -d "venv" ]; then
    log_warning "Virtual environment 'venv' not found. Let's set it up!"
    
    log_info "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        log_success "Virtual environment created."
    else
        log_error "Failed to create virtual environment."
        exit 1
    fi
    
    log_info "Activating virtual environment..."
    source venv/bin/activate
    
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    if [ -f "requirements.txt" ]; then
        log_info "Installing requirements from requirements.txt..."
        pip install -r requirements.txt
        log_success "Requirements installed successfully."
    else
        log_warning "No requirements.txt found. Skipping dependency installation."
    fi
else
    # 2. Activate the virtual environment
    log_info "Activating virtual environment..."
    source venv/bin/activate
    log_success "Virtual environment activated."
fi

# 3. Check if project1 exists
if [ ! -d "project1" ]; then
    log_error "Directory 'project1' not found. Cannot proceed."
    exit 1
fi

cd project1

if [ $# -eq 0 ]; then
    log_info "Starting development server on http://127.0.0.1:8000/ ..."
    echo -e "${CYAN}Press Ctrl+C to stop the server.${NC}"
    echo ""
    python manage.py runserver
else
    log_info "Executing command: ${BOLD}python manage.py $@${NC}"
    echo ""
    python manage.py "$@"
fi

