#!/bin/bash
# Build script for Vercel deployment

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Make script executable
chmod +x build_files.sh 