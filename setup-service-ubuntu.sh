#!/bin/bash
# Set up systemd service and Nginx for Ubuntu

APP_DIR="/home/ubuntu/link-downloader"

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/link-downloader.service > /dev/null <<EOF
[Unit]
Description=Link Downloader Flask App
After=network.target

[Service]
User=ubuntu
WorkingDirectory=$APP_DIR
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 $APP_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/link-downloader > /dev/null <<EOF
server {
    listen 80;
    server_name script.neillanda.com;

    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;
    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

# Enable site
sudo ln -sf /etc/nginx/sites-available/link-downloader /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Test and restart Nginx
sudo nginx -t
sudo systemctl restart nginx

# Enable and start Flask service
echo "Starting Flask service..."
sudo systemctl daemon-reload
sudo systemctl enable link-downloader
sudo systemctl start link-downloader

echo ""
echo "=== Service Setup Complete ==="
echo ""
echo "Check status: sudo systemctl status link-downloader"
echo "View logs: sudo journalctl -u link-downloader -f"
echo "Set up SSL: sudo certbot --nginx -d script.neillanda.com"
echo ""

