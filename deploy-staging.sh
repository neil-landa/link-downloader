#!/bin/bash
# Staging Deployment Script
# Run this on your STAGING server to deploy from 'staging' branch

set -e  # Exit on any error

echo "=========================================="
echo "  STAGING DEPLOYMENT - staging.neillanda.com"
echo "=========================================="

# Configuration
APP_DIR="/home/ec2-user/link-downloader"
BRANCH="staging"
SERVICE_NAME="link-downloader-staging"
DOMAIN="staging.neillanda.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}Error: Directory $APP_DIR not found${NC}"
    echo "Please clone the repository first:"
    echo "  cd /home/ec2-user"
    echo "  git clone https://github.com/yourusername/link-downloader.git"
    exit 1
fi

cd "$APP_DIR"

# Check current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${YELLOW}Current branch: $CURRENT_BRANCH${NC}"

if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo -e "${YELLOW}Switching to $BRANCH branch...${NC}"
    git checkout "$BRANCH"
fi

# Pull latest changes
echo -e "${YELLOW}Pulling latest changes from $BRANCH...${NC}"
git fetch origin
git pull origin "$BRANCH"

# Show what changed
echo -e "${GREEN}Latest commit:${NC}"
git log -1 --oneline

# Install/update Python dependencies
echo -e "${YELLOW}Updating Python dependencies...${NC}"
pip3.11 install -r requirements.txt --quiet

# Install/update yt-dlp
echo -e "${YELLOW}Updating yt-dlp...${NC}"
pip3.11 install --upgrade yt-dlp --quiet

# Check if cookies file exists
if [ ! -f "cookies.txt" ]; then
    echo -e "${YELLOW}Warning: cookies.txt not found. Some downloads may fail.${NC}"
fi

# Restart the service
echo -e "${YELLOW}Restarting $SERVICE_NAME service...${NC}"
sudo systemctl restart "$SERVICE_NAME"

# Wait a moment for service to start
sleep 2

# Check service status
if sudo systemctl is-active --quiet "$SERVICE_NAME"; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start!${NC}"
    echo "Check logs with: sudo journalctl -u $SERVICE_NAME -n 50"
    exit 1
fi

# Test Nginx configuration
if sudo nginx -t > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Nginx configuration is valid${NC}"
else
    echo -e "${RED}✗ Nginx configuration has errors!${NC}"
    sudo nginx -t
    exit 1
fi

# Reload Nginx
sudo systemctl reload nginx

echo ""
echo -e "${GREEN}=========================================="
echo "  STAGING DEPLOYMENT COMPLETE"
echo "==========================================${NC}"
echo ""
echo "Service: $SERVICE_NAME"
echo "Domain: $DOMAIN"
echo "Branch: $BRANCH"
echo ""
echo "Check status: sudo systemctl status $SERVICE_NAME"
echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${YELLOW}Remember: Test thoroughly before merging to main!${NC}"
echo ""

