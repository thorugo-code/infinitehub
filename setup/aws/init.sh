#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Run the Django development server
nohup python3 manage.py runserver 0.0.0.0:8000 > output.log 2>&1 &
