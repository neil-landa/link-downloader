#!/bin/bash
# Deployment script for Ubuntu EC2 instance

echo "=== Link Downloader Deployment Script (Ubuntu) ==="

# Update system
echo "Updating system..."
sudo apt update
sudo apt upgrade -y

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install yt-dlp
echo "Installing yt-dlp..."
pip3 install yt-dlp

# Install ffmpeg (required for some audio formats)
echo "Installing ffmpeg..."
sudo apt install ffmpeg -y

# Install Nginx
echo "Installing Nginx..."
sudo apt install nginx -y

# Install Certbot for SSL
echo "Installing Certbot..."
sudo apt install certbot python3-certbot-nginx -y

# Create downloads directory
echo "Creating downloads directory..."
mkdir -p downloads
chmod 755 downloads

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Upload your application files to /home/ubuntu/link-downloader/"
echo "2. Install Python dependencies: cd link-downloader && pip3 install -r requirements.txt"
echo "3. Run: sudo ./setup-service.sh (or follow manual setup in guide)"
echo ""

