# File Sharing Server for Termux

Lightweight real-time file sharing server that runs on Android Termux.

## Features
- Real-time online users list
- File sharing with accept/reject
- Handles large files (GB+) efficiently
- Memory-efficient streaming
- Works on mobile devices

## Termux Setup

```bash
# Update packages
pkg update && pkg upgrade

# Install Python
pkg install python

# Clone the project
git clone https://github.com/alok-rg/sharefile.git
cd sharefile

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start server
chmod +x run.sh
./run.sh
```

## Quick Start (if already set up)

```bash
./run.sh
```

Server runs on: `http://localhost:8000`

## Access from other devices

1. Find your phone's IP:
   ```bash
   ifconfig wlan0
   ```

2. Connect other devices to same WiFi

3. Access: `http://YOUR_PHONE_IP:8000`

## Usage

1. Enter your name
2. See online users
3. Click "Share" next to any user
4. Select file from your device
5. Receiver accepts/rejects
6. File transfers

## Stop Server

Press `Ctrl + C`

## Requirements
- Android phone with Termux
- Python 3.8+
- ~50MB storage
- WiFi for sharing between devices

## Notes
- Uses single-worker in-memory channels (lightweight)
- Files stored temporarily in /tmp
- Auto-cleanup after transfer
- Works without Redis or external dependencies
