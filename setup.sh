#!/bin/bash
# One-time setup script for Termux

echo "File Sharing Server - Setup"
echo "==========================="
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "Running migrations..."
python manage.py migrate

echo ""
echo "Making run script executable..."
chmod +x run.sh

echo ""
echo "==========================="
echo "Setup complete!"
echo ""
echo "To start the server, run: ./run.sh"
echo ""
