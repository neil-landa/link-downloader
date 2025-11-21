#!/usr/bin/env python3
"""
Automated Cookie Extractor using Playwright - LOCAL VERSION

This script runs on your local 24/7 computer, extracts cookies, and uploads to your EC2 server.
Uses non-headless browser (real browser window) which is more likely to pass Google's checks.

Requirements:
    pip install playwright python-dotenv paramiko
    playwright install chromium

Usage:
    python3 auto-cookie-extractor-local.py

Environment Variables (in .env file):
    YOUTUBE_EMAIL=your-email@gmail.com
    YOUTUBE_PASSWORD=your-app-password
    SERVER_USER=ubuntu
    SERVER_HOST=your-server-ip
    SERVER_PATH=/home/ubuntu/www/link-downloader
    SSH_KEY_PATH=/path/to/your-key.pem  # Optional, if using SSH key
    USE_SSH_KEY=true  # true for SSH key, false for password
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("ERROR: Playwright not installed!")
    print("Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

try:
    import paramiko
    from scp import SCPClient
except ImportError:
    print("ERROR: paramiko or scp not installed!")
    print("Install with: pip install paramiko scp")
    sys.exit(1)

# Load environment variables
# Check if .env file exists and handle encoding issues
env_file = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_file):
    try:
        load_dotenv(env_file, encoding='utf-8')
    except UnicodeDecodeError:
        # Try to fix encoding issues (file might be UTF-16 or have BOM)
        print("Warning: .env file has encoding issues. Trying to fix...")
        try:
            # Try reading with different encodings
            for encoding in ['utf-8-sig', 'utf-16', 'latin-1']:
                try:
                    with open(env_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    # Rewrite as UTF-8
                    with open(env_file, 'w', encoding='utf-8', newline='\n') as f:
                        f.write(content)
                    load_dotenv(env_file, encoding='utf-8')
                    print("Fixed .env file encoding")
                    break
                except:
                    continue
            else:
                print("ERROR: Could not fix .env file encoding")
                print("Please recreate .env file as UTF-8 (no BOM)")
                print("You can use Notepad++ or VS Code to save as UTF-8")
                sys.exit(1)
        except Exception as e:
            print(f"ERROR: Could not fix .env file encoding: {e}")
            print("Please recreate .env file as UTF-8 (no BOM)")
            sys.exit(1)
    except Exception as e:
        print(f"Warning: Error loading .env file: {e}")
else:
    # Try loading from current directory anyway (might be in different location)
    try:
        load_dotenv()
    except:
        pass  # Will check for required vars later

# Configuration
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'cookie-extraction-local.log')
BROWSER_DATA_DIR = os.path.join(
    os.path.dirname(__file__), '.browser-data-local')

# YouTube credentials
YOUTUBE_EMAIL = os.getenv('YOUTUBE_EMAIL', '')
YOUTUBE_PASSWORD = os.getenv('YOUTUBE_PASSWORD', '')

# Server configuration
SERVER_USER = os.getenv('SERVER_USER', 'ubuntu')
SERVER_HOST = os.getenv('SERVER_HOST', '')
SERVER_PATH = os.getenv('SERVER_PATH', '/home/ubuntu/www/link-downloader')
SSH_KEY_PATH = os.getenv('SSH_KEY_PATH', '')
USE_SSH_KEY = os.getenv('USE_SSH_KEY', 'true').lower() == 'true'
SERVER_PASSWORD = os.getenv('SERVER_PASSWORD', '')

# Set up logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def upload_cookies_to_server(local_file, remote_path):
    """Upload cookies.txt to server via SCP"""
    try:
        logger.info(f"Connecting to server: {SERVER_USER}@{SERVER_HOST}")

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if USE_SSH_KEY and SSH_KEY_PATH:
            # Use SSH key
            if not os.path.exists(SSH_KEY_PATH):
                logger.error(f"SSH key not found at: {SSH_KEY_PATH}")
                return False
            ssh.connect(SERVER_HOST, username=SERVER_USER,
                        key_filename=SSH_KEY_PATH)
        else:
            # Use password
            if not SERVER_PASSWORD:
                logger.error("SERVER_PASSWORD not set in .env file")
                return False
            ssh.connect(SERVER_HOST, username=SERVER_USER,
                        password=SERVER_PASSWORD)

        # Upload file
        with SCPClient(ssh.get_transport()) as scp:
            scp.put(local_file, remote_path)

        ssh.close()
        logger.info(
            f"Successfully uploaded cookies to {SERVER_USER}@{SERVER_HOST}:{remote_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to upload cookies: {e}")
        return False


def extract_cookies_from_browser():
    """
    Extract cookies from browser using Playwright
    Uses NON-HEADLESS mode (real browser) which is more likely to pass Google's checks
    """
    logger.info("Starting automated cookie extraction (LOCAL - Non-Headless)...")

    if not YOUTUBE_EMAIL or not YOUTUBE_PASSWORD:
        logger.error(
            "YOUTUBE_EMAIL and YOUTUBE_PASSWORD must be set in .env file!")
        return False

    if not SERVER_HOST:
        logger.error("SERVER_HOST must be set in .env file!")
        return False

    with sync_playwright() as p:
        try:
            # Launch browser in NON-HEADLESS mode (real browser window)
            # This is much more likely to pass Google's "browser not secure" check
            logger.info("Launching browser (non-headless mode)...")
            browser = p.chromium.launch(
                headless=False,  # NON-HEADLESS - shows real browser window
                args=[
                    '--disable-blink-features=AutomationControlled',  # Hide automation
                    '--window-size=1920,1080',
                ]
            )

            # Create persistent browser context
            os.makedirs(BROWSER_DATA_DIR, exist_ok=True)
            storage_state_path = os.path.join(BROWSER_DATA_DIR, 'state.json')

            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                timezone_id='America/New_York',
                storage_state=storage_state_path if os.path.exists(
                    storage_state_path) else None,
            )

            page = context.new_page()

            # Remove webdriver property
            page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Navigate to YouTube with longer timeout
            logger.info("Navigating to YouTube...")
            try:
                # Try networkidle first (waits for network to be idle)
                page.goto('https://www.youtube.com',
                          wait_until='networkidle', timeout=60000)
                time.sleep(2)
            except PlaywrightTimeout:
                logger.warning(
                    "Navigation timeout with networkidle, trying domcontentloaded...")
                # Try with domcontentloaded instead (faster, doesn't wait for all network)
                try:
                    page.goto('https://www.youtube.com',
                              wait_until='domcontentloaded', timeout=30000)
                    time.sleep(3)  # Give page time to load
                    logger.info("Page loaded (domcontentloaded)")
                except PlaywrightTimeout:
                    logger.warning("Still timing out, trying load event...")
                    # Last resort - just wait for load event
                    try:
                        page.goto('https://www.youtube.com',
                                  wait_until='load', timeout=30000)
                        time.sleep(5)  # Give extra time for page to fully load
                        logger.info("Page loaded (load event)")
                    except:
                        logger.error(
                            "Failed to load YouTube page after multiple attempts")
                        logger.error("Check your internet connection")
                        return False

            # Check if already logged in
            try:
                account_button = page.locator(
                    'button[aria-label*="Account"]').first
                if account_button.is_visible(timeout=3000):
                    logger.info("Already logged in! Extracting cookies...")
                else:
                    raise Exception("Not logged in")
            except:
                # Need to log in
                logger.info("Not logged in. Starting login process...")
                logger.info(
                    "NOTE: Browser window will open - you can watch the process!")

                # Click sign in button
                try:
                    sign_in_button = page.locator(
                        'a:has-text("Sign in")').first
                    if sign_in_button.is_visible(timeout=5000):
                        sign_in_button.click()
                        logger.info("Clicked sign in button")
                        time.sleep(2)
                except:
                    try:
                        sign_in_button = page.locator(
                            'button:has-text("Sign in")').first
                        if sign_in_button.is_visible(timeout=5000):
                            sign_in_button.click()
                            logger.info("Clicked sign in button (alternative)")
                            time.sleep(2)
                    except:
                        logger.warning(
                            "Could not find sign in button, trying direct navigation...")
                        page.goto(
                            'https://accounts.google.com/signin/v2/identifier?service=youtube', wait_until='networkidle')
                        time.sleep(2)

                # Enter email
                logger.info("Entering email...")
                email_input = page.locator('input[type="email"]').first
                email_input.wait_for(state='visible', timeout=10000)
                email_input.fill(YOUTUBE_EMAIL)
                time.sleep(1)

                # Click next
                next_button = page.locator(
                    'button:has-text("Next"), button#identifierNext').first
                next_button.click()
                logger.info("Clicked next after email")
                time.sleep(5)

                # Check for passkey prompt and skip it
                logger.info("Checking for passkey prompt...")
                passkey_selectors = [
                    'button:has-text("Try another way")',
                    'button:has-text("Use your password")',
                    'a:has-text("Try another way")',
                    'a:has-text("Use your password")',
                ]

                passkey_detected = False
                for selector in passkey_selectors:
                    try:
                        passkey_button = page.locator(selector).first
                        if passkey_button.is_visible(timeout=3000):
                            logger.info(
                                f"Passkey prompt detected, clicking: {selector}")
                            passkey_button.click()
                            time.sleep(2)
                            passkey_detected = True
                            break
                    except:
                        continue

                # Enter password
                logger.info("Looking for password field...")
                password_input = None
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input#password',
                    'input#Passwd'
                ]

                for selector in password_selectors:
                    try:
                        password_input = page.locator(selector).first
                        password_input.wait_for(state='visible', timeout=5000)
                        logger.info(f"Found password field using: {selector}")
                        break
                    except:
                        continue

                if not password_input:
                    screenshot_path = os.path.join(
                        LOG_DIR, 'password-page-error.png')
                    page.screenshot(path=screenshot_path)
                    logger.error(
                        f"Could not find password field! Screenshot: {screenshot_path}")
                    return False

                logger.info("Entering password...")
                password_input.click(timeout=10000)
                time.sleep(0.5)
                password_input.clear(timeout=5000)
                time.sleep(0.3)
                password_input.type(YOUTUBE_PASSWORD, delay=50, timeout=30000)
                time.sleep(1)

                # Click next/sign in
                sign_in_button = page.locator(
                    'button:has-text("Next"), button#passwordNext, button:has-text("Sign in")').first
                sign_in_button.click()
                logger.info("Clicked sign in after password")
                time.sleep(5)

                # Check if login was successful
                try:
                    page.wait_for_url('**/youtube.com/**', timeout=10000)
                    logger.info("Login successful!")
                except:
                    error_text = page.locator(
                        'div[role="alert"], span:has-text("Wrong password"), span:has-text("Couldn\'t sign you in")').first
                    if error_text.is_visible(timeout=3000):
                        error_msg = error_text.text_content()
                        logger.error(f"Login failed: {error_msg}")
                        return False

            # Navigate to YouTube to ensure cookies are set
            logger.info(
                "Navigating to YouTube home to ensure cookies are set...")
            try:
                page.goto('https://www.youtube.com',
                          wait_until='domcontentloaded', timeout=30000)
                time.sleep(2)
            except PlaywrightTimeout:
                logger.warning(
                    "Timeout on final navigation, but continuing with cookie extraction...")
                time.sleep(2)

            # Extract cookies
            logger.info("Extracting cookies...")
            cookies = context.cookies()

            if not cookies:
                logger.error("No cookies found!")
                return False

            logger.info(f"Extracted {len(cookies)} cookies")

            # Convert to Netscape format
            netscape_cookies = convert_to_netscape_format(cookies)

            # Save to local file
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                f.write(netscape_cookies)

            file_size = os.path.getsize(COOKIES_FILE)
            logger.info(
                f"Cookies saved locally to {COOKIES_FILE} ({file_size} bytes)")

            # Save browser state
            try:
                context.storage_state(path=storage_state_path)
                logger.info("Browser state saved for next run")
            except:
                pass

            # Upload to server
            logger.info("Uploading cookies to server...")
            remote_path = f"{SERVER_PATH}/cookies.txt"
            if upload_cookies_to_server(COOKIES_FILE, remote_path):
                logger.info(
                    "Cookie extraction and upload completed successfully!")
                return True
            else:
                logger.error("Cookie extraction succeeded but upload failed!")
                logger.info(f"Local cookies file saved at: {COOKIES_FILE}")
                logger.info("You can manually upload it to the server")
                return False

        except PlaywrightTimeout as e:
            logger.error(f"Timeout error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during cookie extraction: {e}", exc_info=True)
            return False
        finally:
            # Keep browser open for a moment so user can see result
            time.sleep(2)
            browser.close()


def convert_to_netscape_format(cookies):
    """Convert Playwright cookies to Netscape format"""
    lines = [
        "# Netscape HTTP Cookie File",
        "# This file was generated by auto-cookie-extractor-local.py",
        f"# Generated: {datetime.now().isoformat()}",
        "#"
    ]

    for cookie in cookies:
        domain = cookie.get('domain', '')
        if domain.startswith('.'):
            domain = domain[1:]

        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = cookie.get('path', '/')
        secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'

        expiration = cookie.get('expires', -1)
        if expiration == -1:
            expiration = '0'
        else:
            expiration = str(int(expiration))

        name = cookie.get('name', '')
        value = cookie.get('value', '')

        if 'youtube.com' in domain or 'google.com' in domain or 'googleapis.com' in domain:
            lines.append(
                f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Automated Cookie Extractor - LOCAL VERSION")
    logger.info("=" * 60)

    success = extract_cookies_from_browser()

    if success:
        logger.info("Cookie extraction and upload completed successfully!")
        sys.exit(0)
    else:
        logger.error("Cookie extraction failed!")
        sys.exit(1)
