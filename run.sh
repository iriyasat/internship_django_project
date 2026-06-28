#!/bin/bash

# Navigate to the script's directory
cd "$(dirname "$0")"

echo "=== Django Virtual Environment Helper ==="

# 1. Check if virtual environment exists, create if missing
if [ ! -d "venv" ]; then
    echo "Virtual environment 'venv' not found. Creating it..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Upgrading pip..."
    pip install --upgrade pip
    echo "Installing requirements..."
    pip install -r requirements.txt
else
    # 2. Activate the virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# 3. Run the development server or other manage.py command
cd project1

if [ $# -eq 0 ]; then
    echo "Starting development server..."
    python manage.py runserver
else
    echo "Executing: python manage.py $@"
    python manage.py "$@"
fi
