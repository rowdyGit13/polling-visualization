#!/bin/bash
# Build script for Vercel deployment

# Install minimal dependencies (faster, fewer issues)
if [ -f vercel_requirements.txt ]; then
    echo "Installing minimal requirements for Vercel..."
    pip install -r vercel_requirements.txt
else
    echo "Installing full requirements..."
    pip install -r requirements.txt
fi

# Collect static files
python manage.py collectstatic --noinput

# Make script executable
chmod +x build_files.sh 