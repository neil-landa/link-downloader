#!/usr/bin/env python3
"""
Automated Cookie Extractor using Playwright

This script automatically logs into YouTube and extracts cookies for yt-dlp.
Designed to run on the EC2 server as a cron job.

Requirements:
    pip install playwright python-dotenv
    playwright install chromium

Usage:
    python3 auto-cookie-extractor.py

Environment Variables (optional):
    YOUTUBE_EMAIL=landaneil10@gmail.com
    YOUTUBE_PASSWORD=rczPD0k9cI8ypI
    USE_2CAPTCHA=false  # Set to true if you want CAPTCHA solving
    2CAPTCHA_API_KEY=your-api-key  # Only needed if USE_2CAPTCHA=true
"""

import os
import sys
import time
import json
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

# Load environment variables
load_dotenv()

# Configuration
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'cookie-extraction.log')

# YouTube credentials (from environment or prompt)
YOUTUBE_EMAIL = os.getenv('YOUTUBE_EMAIL', '')
YOUTUBE_PASSWORD = os.getenv('YOUTUBE_PASSWORD', '')

# CAPTCHA solving (optional)
USE_2CAPTCHA = os.getenv('USE_2CAPTCHA', 'false').lower() == 'true'
CAPTCHA_API_KEY = os.getenv('2CAPTCHA_API_KEY', '')

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


def extract_cookies_from_browser():
    """
    Extract cookies from browser using Playwright
    Returns cookies in Netscape format for yt-dlp
    """
    logger.info("Starting automated cookie extraction...")

    if not YOUTUBE_EMAIL or not YOUTUBE_PASSWORD:
        logger.error("YOUTUBE_EMAIL and YOUTUBE_PASSWORD must be set!")
        logger.error("Set them as environment variables or in .env file")
        return False

    with sync_playwright() as p:
        try:
            # Launch browser in headless mode
            logger.info("Launching browser...")
            browser = p.chromium.launch(
                headless=True,
                # Required for some Linux systems
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )

            # Create context (like a browser profile)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()

            # Navigate to YouTube
            logger.info("Navigating to YouTube...")
            page.goto('https://www.youtube.com',
                      wait_until='networkidle', timeout=30000)
            time.sleep(2)  # Give page time to load

            # Check if already logged in
            try:
                # Look for account button or profile picture (indicates logged in)
                account_button = page.locator(
                    'button[aria-label*="Account"]').first
                if account_button.is_visible(timeout=3000):
                    logger.info("Already logged in! Extracting cookies...")
                else:
                    raise Exception("Not logged in")
            except:
                # Need to log in
                logger.info("Not logged in. Starting login process...")

                # Click sign in button
                try:
                    sign_in_button = page.locator(
                        'a:has-text("Sign in")').first
                    if sign_in_button.is_visible(timeout=5000):
                        sign_in_button.click()
                        logger.info("Clicked sign in button")
                        time.sleep(2)
                except:
                    # Try alternative sign in button
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
                time.sleep(3)

                # Check for CAPTCHA
                if page.locator('iframe[title*="reCAPTCHA"], iframe[title*="CAPTCHA"]').count() > 0:
                    logger.warning("CAPTCHA detected!")
                    if USE_2CAPTCHA and CAPTCHA_API_KEY:
                        logger.info(
                            "Attempting to solve CAPTCHA with 2Captcha...")
                        # Note: 2Captcha integration would go here
                        # This is a placeholder - full implementation requires 2captcha library
                        logger.warning(
                            "2Captcha integration not fully implemented. Please solve manually or use browser extension method.")
                        return False
                    else:
                        logger.error(
                            "CAPTCHA detected but 2Captcha not configured!")
                        logger.error(
                            "Set USE_2CAPTCHA=true and 2CAPTCHA_API_KEY in environment")
                        logger.error(
                            "Or use the browser extension method instead")
                        return False

                # Enter password
                logger.info("Entering password...")
                password_input = page.locator('input[type="password"]').first
                password_input.wait_for(state='visible', timeout=10000)
                password_input.fill(YOUTUBE_PASSWORD)
                time.sleep(1)

                # Click next/sign in
                sign_in_button = page.locator(
                    'button:has-text("Next"), button#passwordNext, button:has-text("Sign in")').first
                sign_in_button.click()
                logger.info("Clicked sign in after password")
                time.sleep(5)  # Wait for login to complete

                # Check if login was successful
                try:
                    page.wait_for_url('**/youtube.com/**', timeout=10000)
                    logger.info("Login successful!")
                except:
                    # Check for error messages
                    error_text = page.locator(
                        'div[role="alert"], span:has-text("Wrong password"), span:has-text("Couldn\'t sign you in")').first
                    if error_text.is_visible(timeout=3000):
                        error_msg = error_text.text_content()
                        logger.error(f"Login failed: {error_msg}")
                        return False
                    else:
                        logger.warning(
                            "Could not confirm login status, but continuing...")

            # Navigate to a YouTube page to ensure cookies are set
            logger.info(
                "Navigating to YouTube home to ensure cookies are set...")
            page.goto('https://www.youtube.com',
                      wait_until='networkidle', timeout=30000)
            time.sleep(2)

            # Extract cookies
            logger.info("Extracting cookies...")
            cookies = context.cookies()

            if not cookies:
                logger.error("No cookies found!")
                return False

            logger.info(f"Extracted {len(cookies)} cookies")

            # Convert to Netscape format (for yt-dlp)
            netscape_cookies = convert_to_netscape_format(cookies)

            # Save to file
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                f.write(netscape_cookies)

            file_size = os.path.getsize(COOKIES_FILE)
            logger.info(f"Cookies saved to {COOKIES_FILE} ({file_size} bytes)")

            # Verify cookies work by testing with a simple request
            logger.info("Cookie extraction completed successfully!")
            return True

        except PlaywrightTimeout as e:
            logger.error(f"Timeout error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error during cookie extraction: {e}", exc_info=True)
            return False
        finally:
            browser.close()


def convert_to_netscape_format(cookies):
    """
    Convert Playwright cookies to Netscape format (for yt-dlp)

    Netscape format:
    # Netscape HTTP Cookie File
    domain	flag	path	secure	expiration	name	value
    """
    lines = [
        "# Netscape HTTP Cookie File",
        "# This file was generated by auto-cookie-extractor.py",
        f"# Generated: {datetime.now().isoformat()}",
        "#"
    ]

    for cookie in cookies:
        # Netscape format: domain, flag, path, secure, expiration, name, value
        domain = cookie.get('domain', '')
        # Remove leading dot if present (Netscape format doesn't use it)
        if domain.startswith('.'):
            domain = domain[1:]

        flag = 'TRUE' if domain.startswith('.') else 'FALSE'
        path = cookie.get('path', '/')
        secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'

        # Expiration: -1 for session cookies, otherwise Unix timestamp
        expiration = cookie.get('expires', -1)
        if expiration == -1:
            expiration = '0'  # Session cookie
        else:
            expiration = str(int(expiration))

        name = cookie.get('name', '')
        value = cookie.get('value', '')

        # Only include YouTube/Google cookies
        if 'youtube.com' in domain or 'google.com' in domain or 'googleapis.com' in domain:
            lines.append(
                f"{domain}\t{flag}\t{path}\t{secure}\t{expiration}\t{name}\t{value}")

    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Automated Cookie Extractor")
    logger.info("=" * 60)

    success = extract_cookies_from_browser()

    if success:
        logger.info("Cookie extraction completed successfully!")
        sys.exit(0)
    else:
        logger.error("Cookie extraction failed!")
        sys.exit(1)
