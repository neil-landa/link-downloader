#!/bin/bash
# Server Optimization Script for Low-RAM EC2 Instances
# Run this once on your server to optimize for 1GB RAM

echo "=== Optimizing Server for 1GB RAM ==="

# 1. Add Swap Space (Critical for 1GB RAM)
echo ""
echo "1. Setting up swap space..."
SWAP_SIZE="2G"  # 2GB swap (recommended for 1GB RAM)

# Check if swap already exists
if [ -f /swapfile ]; then
    echo "Swap file already exists. Skipping swap creation."
    echo "Current swap:"
    free -h
else
    echo "Creating ${SWAP_SIZE} swap file..."
    sudo fallocate -l ${SWAP_SIZE} /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    
    # Make swap permanent
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    
    echo "✓ Swap created successfully"
    free -h
fi

# 2. Optimize Swappiness (how aggressively system uses swap)
echo ""
echo "2. Optimizing swappiness..."
# Lower swappiness = prefer RAM, use swap less aggressively
# Good for systems with limited RAM
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
sudo sysctl vm.swappiness=10
echo "✓ Swappiness set to 10 (lower = less aggressive swap usage)"

# 3. Optimize Cache Pressure
echo ""
echo "3. Optimizing cache pressure..."
# How quickly system reclaims cache memory
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.conf
sudo sysctl vm.vfs_cache_pressure=50
echo "✓ Cache pressure optimized"

# 4. Update system packages
echo ""
echo "4. Updating system packages..."
sudo apt update -qq
sudo apt upgrade -y -qq

# 5. Install/update yt-dlp for best performance
echo ""
echo "5. Ensuring yt-dlp is up to date..."
pip3.11 install --upgrade yt-dlp --quiet

# 6. Clean up old packages and cache
echo ""
echo "6. Cleaning up system..."
sudo apt autoremove -y -qq
sudo apt autoclean -qq

echo ""
echo "=== Optimization Complete ==="
echo ""
echo "Summary of changes:"
echo "  ✓ Added 2GB swap space"
echo "  ✓ Optimized swappiness (10)"
echo "  ✓ Optimized cache pressure"
echo "  ✓ Updated yt-dlp"
echo ""
echo "Current memory status:"
free -h
echo ""
echo "Note: Reboot recommended for all optimizations to take full effect:"
echo "  sudo reboot"

