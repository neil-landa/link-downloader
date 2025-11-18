#!/usr/bin/env python3
"""
Cookie File Watcher - Logs when cookies.txt is updated

This script monitors the cookies.txt file and logs when it's updated.
Run this as a background service or cron job to track cookie updates.

Usage:
    python3 cookie-watcher.py
    # Or add to systemd service
"""

import os
import time
import logging
from pathlib import Path

# Configuration
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
COOKIE_LOG_FILE = os.path.join(LOG_DIR, 'cookie-updates.log')

# Set up logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(COOKIE_LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Track last known modification time
last_mtime = None
if os.path.exists(COOKIES_FILE):
    last_mtime = os.path.getmtime(COOKIES_FILE)
    logger.info(f"Initial cookie file state: {COOKIES_FILE} (mtime: {last_mtime})")


def check_cookie_file():
    """Check if cookie file has been updated"""
    global last_mtime
    
    if not os.path.exists(COOKIES_FILE):
        if last_mtime is not None:
            logger.warning(f"Cookie file removed: {COOKIES_FILE}")
            last_mtime = None
        return
    
    current_mtime = os.path.getmtime(COOKIES_FILE)
    
    if last_mtime is None:
        # First time seeing the file
        file_size = os.path.getsize(COOKIES_FILE)
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_mtime))
        logger.info(f"Cookie file detected: {COOKIES_FILE} (size: {file_size} bytes, modified: {mtime_str})")
        last_mtime = current_mtime
    elif current_mtime > last_mtime:
        # File has been updated
        file_size = os.path.getsize(COOKIES_FILE)
        mtime_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(current_mtime))
        time_diff = current_mtime - last_mtime
        
        logger.info(f"Cookie file updated: {COOKIES_FILE}")
        logger.info(f"  Size: {file_size} bytes")
        logger.info(f"  Modified: {mtime_str}")
        logger.info(f"  Time since last update: {time_diff:.1f} seconds")
        logger.info(f"  Update source: Likely from Windows cookie refresh script")
        
        last_mtime = current_mtime


if __name__ == '__main__':
    logger.info("Starting cookie file watcher...")
    logger.info(f"Monitoring: {COOKIES_FILE}")
    logger.info(f"Log file: {COOKIE_LOG_FILE}")
    
    try:
        while True:
            check_cookie_file()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("Cookie watcher stopped by user")
    except Exception as e:
        logger.error(f"Error in cookie watcher: {e}", exc_info=True)

