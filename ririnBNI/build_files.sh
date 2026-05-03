#!/bin/bash

echo "🚀 Building Django app for Vercel..."

# Install dependencies
pip install -r requirements.txt

# Create staticfiles directory
mkdir -p staticfiles

# Collect static files
python manage.py collectstatic --noinput

echo "✅ Build completed!"
