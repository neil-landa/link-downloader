#!/bin/bash
# Deployment script for Ubuntu EC2 instance

echo "=== Link Downloader Deployment Script (Ubuntu) ==="

# Update system
echo "Updating system..."
sudo apt update
sudo apt upgrade -y

# Install Python 3.11 and pip
echo "Installing Python 3.11..."
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install yt-dlp via pip (apt version is often outdated)
echo "Installing yt-dlp via pip (for latest version)..."
python3.11 -m pip install --upgrade yt-dlp
echo "Also installing via apt as fallback (but pip version takes precedence in PATH)..."
# Also install via apt as fallback (but pip version takes precedence in PATH)
sudo apt install yt-dlp -y || true
sudo apt update

# Install ffmpeg (required for some audio formats)
echo "Installing ffmpeg..."
sudo apt install ffmpeg -y
sudo apt update

# Install Nginx
echo "Installing Nginx..."
sudo apt install nginx -y
sudo apt update

# Install Certbot for SSL
echo "Installing Certbot..."
# Create the certbot cert later
# sudo apt install certbot python3-certbot-nginx -y
sudo apt update

# Install Node.js (OPTIONAL - for best YouTube download reliability)
# The app works without Node.js (uses Android client fallback), but default client is more reliable
# echo ""
# echo "Installing Node.js (optional but recommended for YouTube downloads)..."
# curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
# sudo apt install -y nodejs
# echo "Node.js version: $(node --version)"
# echo "npm version: $(npm --version)"

# Create downloads directory
echo "Creating downloads directory..."
mkdir -p downloads
chmod 755 downloads
chmod 755 /home/ubuntu
chmod 755 /home/ubuntu/www
chmod 755 /home/ubuntu/www/link-downloader

# Set proper permissions for www-data (Nginx) to access static files
# This ensures css/, js/, and img/ folders are readable by www-data
echo "Setting permissions for static files (www-data read access)..."
# Set permissions for static file directories if they exist
for dir in css js img; do
    if [ -d "$dir" ]; then
        find "$dir" -type d -exec chmod 755 {} \; 2>/dev/null || true
        find "$dir" -type f -exec chmod 644 {} \; 2>/dev/null || true
    fi
done
# Also set permissions for root-level files (index.html, etc.)
if [ -f "index.html" ]; then
    chmod 644 index.html
fi
# Ensure app.py is executable
if [ -f "app.py" ]; then
    chmod 755 app.py
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Install Python dependencies: cd link-downloader && python3.11 -m pip install -r requirements.txt"
echo "2. "
echo "3. Run: sudo ./setup-service.sh (or follow manual setup in guide)"
echo ""

