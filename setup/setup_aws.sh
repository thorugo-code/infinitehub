#!/bin/bash

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py makemigrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Run the Django development server
nohup python3 manage.py runserver 0.0.0.0:8000 > /dev/log/out.log 2>&1 &
