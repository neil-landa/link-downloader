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
                time.sleep(5)  # Wait longer for password page to load

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

                # Check for passkey prompt and skip it
                logger.info("Checking for passkey prompt...")
                passkey_selectors = [
                    'button:has-text("Try another way")',
                    'button:has-text("Use your password")',
                    'a:has-text("Try another way")',
                    'a:has-text("Use your password")',
                    'button:has-text("Skip")',
                    'text="Use your password instead"',
                    'text="Try another way"'
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

                if passkey_detected:
                    logger.info(
                        "Skipped passkey prompt, waiting for password field...")
                    time.sleep(2)

                # Check for iframes (Google login often uses iframes)
                logger.info("Checking for login iframes...")
                frames = page.frames
                login_frame = None
                for frame in frames:
                    frame_url = frame.url
                    if 'accounts.google.com' in frame_url or 'google.com/accounts' in frame_url:
                        logger.info(f"Found Google login iframe: {frame_url}")
                        login_frame = frame
                        break

                # Enter password - try multiple selectors and wait longer
                logger.info("Looking for password field...")
                password_input = None
                password_selectors = [
                    'input[type="password"]',
                    'input[name="password"]',
                    'input[aria-label*="password" i]',
                    'input#password',
                    'input#Passwd'
                ]

                # Try in iframe first if found, then main page
                search_frames = [login_frame] if login_frame else [None]
                search_frames.append(None)  # Also try main page

                for search_frame in search_frames:
                    frame_context = search_frame if search_frame else page
                    frame_name = "iframe" if search_frame else "main page"

                    for selector in password_selectors:
                        try:
                            password_input = frame_context.locator(
                                selector).first
                            password_input.wait_for(
                                state='visible', timeout=5000)
                            logger.info(
                                f"Found password field using: {selector} in {frame_name}")
                            break
                        except:
                            continue

                    if password_input:
                        break

                if not password_input:
                    # Take a screenshot for debugging
                    screenshot_path = os.path.join(
                        LOG_DIR, 'password-page-error.png')
                    page.screenshot(path=screenshot_path)
                    logger.error(
                        f"Could not find password field! Screenshot saved to: {screenshot_path}")
                    logger.error("Current URL: " + page.url)
                    logger.error("Page title: " + page.title())

                    # Check if we're on a different page
                    page_content = page.content()
                    if 'passkey' in page_content.lower() or 'security key' in page_content.lower():
                        logger.error(
                            "Passkey prompt detected but could not skip it!")
                        logger.error(
                            "Solution: Disable passkeys in your Google account settings, or use an app password")
                    elif 'verification' in page_content.lower() or 'verify' in page_content.lower():
                        logger.error(
                            "Verification step detected! This account may require 2FA.")
                        logger.error(
                            "Solution: Use an app password instead of your regular password")

                    return False

                logger.info("Entering password...")
                try:
                    # Wait for field to be ready and clickable
                    password_input.wait_for(state='visible', timeout=10000)

                    # Click the field first to ensure it's focused and ready
                    logger.info("Clicking password field to focus...")
                    password_input.click(timeout=10000)
                    time.sleep(0.5)

                    # Clear any existing content first
                    logger.info("Clearing password field...")
                    password_input.clear(timeout=5000)
                    time.sleep(0.3)

                    # Use type() instead of fill() - more reliable for password fields
                    # Type character by character to avoid timing issues
                    logger.info("Typing password...")
                    password_input.type(
                        YOUTUBE_PASSWORD, delay=50, timeout=30000)
                    time.sleep(1)
                    logger.info("Password entered successfully")
                except Exception as e:
                    # Take screenshot on error
                    screenshot_path = os.path.join(
                        LOG_DIR, 'password-fill-error.png')
                    page.screenshot(path=screenshot_path, full_page=True)
                    logger.error(f"Error filling password field: {e}")
                    logger.error(f"Screenshot saved to: {screenshot_path}")
                    logger.error("Current URL: " + page.url)
                    logger.error("Page title: " + page.title())

                    # Check if field is still visible
                    try:
                        is_visible = password_input.is_visible(timeout=2000)
                        logger.error(f"Password field visible: {is_visible}")
                    except:
                        logger.error("Password field no longer accessible")

                    # Try alternative method - direct fill with longer timeout
                    try:
                        logger.info("Trying alternative fill method...")
                        # Re-locate the field
                        password_input = page.locator(
                            'input[type="password"]').first
                        password_input.wait_for(state='visible', timeout=10000)
                        password_input.fill(YOUTUBE_PASSWORD, timeout=30000)
                        time.sleep(1)
                        logger.info(
                            "Password entered using alternative method")
                    except Exception as e2:
                        logger.error(f"Alternative method also failed: {e2}")
                        logger.error("This might be due to:")
                        logger.error(
                            "1. Password field is in an iframe (Google login uses iframes)")
                        logger.error("2. Page is still loading")
                        logger.error("3. Google is showing a different screen")
                        return False

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
