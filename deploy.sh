#!/bin/bash
# Deployment script for EC2 instance
# Run this on your EC2 instance after uploading files

echo "=== Link Downloader Deployment Script ==="

# Update system
echo "Updating system..."
sudo yum update -y

# Install Python 3.11
echo "Installing Python 3.11..."
sudo yum install python3.11 python3.11-pip -y

# Install yt-dlp
echo "Installing yt-dlp..."
pip3.11 install yt-dlp

# Install ffmpeg (required for some audio formats)
echo "Installing ffmpeg..."
sudo yum install ffmpeg -y

# Install Python dependencies
echo "Installing Python dependencies..."
pip3.11 install -r requirements.txt

# Create downloads directory
echo "Creating downloads directory..."
mkdir -p downloads
chmod 755 downloads

# Install Nginx
echo "Installing Nginx..."
sudo yum install nginx -y

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/link-downloader.service > /dev/null <<EOF
[Unit]
Description=Link Downloader Flask App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/link-downloader
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 /home/ec2-user/link-downloader/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "Starting Flask service..."
sudo systemctl daemon-reload
sudo systemctl enable link-downloader
sudo systemctl start link-downloader

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/conf.d/link-downloader.conf > /dev/null <<EOF
server {
    listen 80;
    server_name script.neillanda.com;

    # Increase timeouts for long downloads
    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Test Nginx configuration
sudo nginx -t

# Start Nginx
echo "Starting Nginx..."
sudo systemctl enable nginx
sudo systemctl restart nginx

# Install Certbot for SSL
echo "Installing Certbot..."
sudo yum install certbot python3-certbot-nginx -y

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Next steps:"
echo "1. Configure DNS: Point script.neillanda.com to this server's IP"
echo "2. Set up SSL: sudo certbot --nginx -d script.neillanda.com"
echo "3. Check service status: sudo systemctl status link-downloader"
echo "4. Check logs: sudo journalctl -u link-downloader -f"
echo ""

