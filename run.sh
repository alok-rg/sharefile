#!/bin/bash
# Simple script to run the file sharing server

echo "Starting File Sharing Server..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run the server
python manage.py runserver 0.0.0.0:8000
