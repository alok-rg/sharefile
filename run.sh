#!/bin/bash
# Simple script to run the file sharing server

echo "Starting File Sharing Server..."
echo "Server will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Run with uvicorn for WebSocket support
uvicorn file_share_project.asgi:application --host 0.0.0.0 --port 8000
