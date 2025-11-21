import os
import subprocess
import zipfile
import tempfile
import shutil
from flask import Flask, request, send_file, jsonify
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Import DynamoDB tracker (optional - fails gracefully if not configured)
try:
    from dynamodb_tracker import (
        create_visit_record,
        save_visit_to_dynamodb,
        DYNAMODB_AVAILABLE
    )
except ImportError:
    # DynamoDB tracking not available
    DYNAMODB_AVAILABLE = False
    def create_visit_record(*args, **kwargs):
        return None
    def save_visit_to_dynamodb(*args, **kwargs):
        return False

app = Flask(__name__, static_folder='.', static_url_path='')

# Error handler to ensure JSON responses for API errors


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

# Rate limiting (optional - uncomment to enable)
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
#
# limiter = Limiter(
#     app=app,
#     key_func=get_remote_address,
#     default_limits=["100 per hour", "10 per minute"]
# )


# Create a temporary directory for downloads
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Cookie file path for YouTube authentication
# Export cookies from your browser and save to this location
COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')


def clean_youtube_url(url):
    """Clean YouTube URLs by removing query parameters after the video ID"""
    if not url:
        return url

    url = url.strip()

    # Check if it's a YouTube URL
    if 'youtube.com' in url or 'youtu.be' in url:
        # Handle youtube.com/watch?v=VIDEO_ID&other_params
        if 'watch?v=' in url:
            # Split on '?' to get base URL and query string
            base_url = url.split('?')[0]
            query_string = url.split('?')[1] if '?' in url else ''

            # Extract just the v= parameter
            if 'v=' in query_string:
                video_id = query_string.split('v=')[1].split('&')[0]
                return f"{base_url}?v={video_id}"

        # Handle youtu.be/VIDEO_ID?other_params
        elif 'youtu.be/' in url:
            # Split on '?' to remove query parameters
            return url.split('?')[0]

    # Return original URL if not YouTube or doesn't match patterns
    return url


def download_audio(url, output_dir):
    """Download audio from a URL using yt-dlp"""
    try:
        # Find yt-dlp in PATH (should work now that PATH includes ~/.local/bin)
        yt_dlp_path = shutil.which('yt-dlp')

        # Fallback: if PATH doesn't work, try common locations (safety net)
        if not yt_dlp_path:
            for path in ['/home/ubuntu/.local/bin/yt-dlp', '/home/ec2-user/.local/bin/yt-dlp',
                         '/usr/local/bin/yt-dlp', '/usr/bin/yt-dlp', 'yt-dlp']:
                if os.path.exists(path) or path == 'yt-dlp':
                    yt_dlp_path = path
                    break

        if not yt_dlp_path or (yt_dlp_path != 'yt-dlp' and not os.path.exists(yt_dlp_path)):
            return False, "yt-dlp not found. Please install it: pip install yt-dlp"

        # Check yt-dlp version (for debugging)
        try:
            version_check = subprocess.run(
                [yt_dlp_path, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if version_check.returncode == 0:
                version = version_check.stdout.strip()
                print(f"Using yt-dlp version: {version} from: {yt_dlp_path}")
                # Warn if using system-installed version (might be old)
                if '/usr/bin/yt-dlp' in yt_dlp_path:
                    print(
                        f"Warning: Using system-installed yt-dlp. Consider using pip version: pip install --upgrade yt-dlp")
                # Warn if version seems old
                if version and not version.startswith('2025') and not version.startswith('2024'):
                    print(
                        f"Warning: yt-dlp version {version} may be outdated. Consider updating: pip install --upgrade yt-dlp")
        except Exception as e:
            print(f"Warning: Could not check yt-dlp version: {e}")

        # Create a safe filename - yt-dlp uses %(title)s.%(ext)s format
        output_path = os.path.join(output_dir, '%(title)s.%(ext)s')

        # Check if cookies file exists and is valid
        use_cookies = os.path.exists(COOKIES_FILE)
        if use_cookies:
            # Check if cookies file is not empty
            if os.path.getsize(COOKIES_FILE) == 0:
                print(f"Warning: Cookies file is empty at {COOKIES_FILE}")
                use_cookies = False
            else:
                # Get file modification time for logging
                try:
                    mtime = os.path.getmtime(COOKIES_FILE)
                    mtime_str = time.strftime(
                        '%Y-%m-%d %H:%M:%S', time.localtime(mtime))
                    file_size = os.path.getsize(COOKIES_FILE)
                    print(
                        f"Using cookies file: {COOKIES_FILE} (size: {file_size} bytes, modified: {mtime_str})")
                except Exception:
                    print(f"Using cookies file: {COOKIES_FILE}")
        else:
            print(
                f"Warning: Cookies file not found at {COOKIES_FILE}. Some downloads may fail.")

        # Common options for all commands
        # Optimized for 1GB RAM: larger buffer for efficiency, no rate limit for speed
        common_opts = [
            # Increased from 16K for better performance (uses ~64KB RAM)
            '--buffer-size', '64K',
            # Removed --limit-rate to use full available bandwidth
            '--no-warnings',  # Reduce noise in logs
            '-x',  # Extract audio only
            '--audio-format', 'm4a',
            '-o', output_path,
            url
        ]

        # Add cookies if available
        if use_cookies:
            common_opts = ['--cookies', COOKIES_FILE] + common_opts

        # Strategy: Try multiple approaches for YouTube to bypass bot detection
        # 1. Try default player client (requires Node.js) - most reliable
        # 2. Try Android client (no Node.js needed)
        # 3. Try with impersonate as fallback

        result = None
        is_youtube = 'youtube' in url.lower()

        if is_youtube:
            # Try 1: Default player client with Node.js (most reliable, requires Node.js)
            print(
                f"Trying default YouTube player client (requires Node.js) for: {url}")
            cmd_default = [
                yt_dlp_path,
                '--extractor-args', 'youtube:player_client=default',
            ] + common_opts

            result = subprocess.run(
                cmd_default,
                capture_output=True,
                text=True,
                timeout=600
            )

            # Try 2: Android client (no Node.js needed, less likely to trigger bot detection)
            if result.returncode != 0:
                print(
                    f"Default client failed, trying Android client for: {url}")
                cmd_android = [
                    yt_dlp_path,
                    '--extractor-args', 'youtube:player_client=android',
                ] + common_opts

                result = subprocess.run(
                    cmd_android,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            # Try 3: Android client with impersonate
            if result.returncode != 0:
                print(
                    f"Android client failed, trying with impersonate for: {url}")
                cmd_impersonate = [
                    yt_dlp_path,
                    '--impersonate', 'chrome',
                    '--extractor-args', 'youtube:player_client=android',
                ] + common_opts

                result = subprocess.run(
                    cmd_impersonate,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            # Try 4: Web client as last resort
            if result.returncode != 0:
                print(f"Trying web client as last resort for: {url}")
                cmd_web = [
                    yt_dlp_path,
                    '--extractor-args', 'youtube:player_client=web',
                ] + common_opts

                result = subprocess.run(
                    cmd_web,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

            # Try 5: If format error, try without specifying format (let yt-dlp choose best)
            if result.returncode != 0 and ('format is not available' in result.stderr.lower() or
                                           'requested format' in result.stderr.lower()):
                print(
                    f"Format error detected, trying with best available audio format for: {url}")
                # Use fallback options (no specific format - let yt-dlp choose)
                fallback_opts = [
                    '--buffer-size', '64K',
                    '--no-warnings',
                    '-x',  # Extract audio only (no format specified)
                    '-o', output_path,
                    url
                ]
                if use_cookies:
                    fallback_opts = ['--cookies', COOKIES_FILE] + fallback_opts

                # Try Android client with fallback format
                cmd_fallback = [
                    yt_dlp_path,
                    '--extractor-args', 'youtube:player_client=android',
                ] + fallback_opts

                result = subprocess.run(
                    cmd_fallback,
                    capture_output=True,
                    text=True,
                    timeout=600
                )
        else:
            # For non-YouTube URLs, use standard command
            cmd_standard = [yt_dlp_path] + common_opts
            result = subprocess.run(
                cmd_standard,
                capture_output=True,
                text=True,
                timeout=600
            )

        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr
            # Check for common cookie-related errors
            if 'cookies' in error_msg.lower() or 'sign in' in error_msg.lower() or 'bot' in error_msg.lower():
                if use_cookies:
                    error_msg += " (Cookies may be expired or invalid. Try refreshing them.)"
                else:
                    error_msg += " (Cookies file not found. Export cookies from your browser.)"
            return False, error_msg
    except subprocess.TimeoutExpired:
        return False, "Download timeout"
    except FileNotFoundError:
        return False, "yt-dlp not found. Please install it: pip install yt-dlp"
    except Exception as e:
        return False, str(e)


# Track active downloads
ACTIVE_DOWNLOADS = set()
DOWNLOAD_LOCK_FILE = os.path.join(
    os.path.dirname(__file__), '.download_in_progress')


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')


@app.route('/status', methods=['GET'])
def status():
    """Check if downloads are in progress - safe to restart service"""
    try:
        # Check if lock file exists (indicates download in progress)
        has_lock_file = os.path.exists(DOWNLOAD_LOCK_FILE)

        # Check if downloads directory has recent activity (within last 5 minutes)
        recent_activity = False
        if os.path.exists(DOWNLOAD_DIR):
            try:
                # Check for directories modified in last 5 minutes
                current_time = time.time()
                for item in os.listdir(DOWNLOAD_DIR):
                    item_path = os.path.join(DOWNLOAD_DIR, item)
                    if os.path.isdir(item_path):
                        # Check modification time
                        mtime = os.path.getmtime(item_path)
                        if current_time - mtime < 300:  # 5 minutes
                            recent_activity = True
                            break
            except Exception:
                pass

        is_busy = has_lock_file or recent_activity or len(ACTIVE_DOWNLOADS) > 0

        return jsonify({
            'status': 'busy' if is_busy else 'idle',
            'active_downloads': len(ACTIVE_DOWNLOADS),
            'has_lock_file': has_lock_file,
            'recent_activity': recent_activity,
            'safe_to_restart': not is_busy
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/<path:path>')
def serve_static(path):
    """Serve static files (CSS, JS, images)"""
    # Security: prevent directory traversal
    if '..' in path or path.startswith('/'):
        return "Not found", 404

    file_path = os.path.join(os.path.dirname(__file__), path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_file(file_path)
    return "Not found", 404


@app.route('/download', methods=['POST'])
# @limiter.limit("5 per minute")  # Uncomment to enable rate limiting
def download():
    """Handle the download request"""
    session_dir = None
    try:
        # Get all links from the form
        links = []
        for i in range(1, 11):
            link_key = f'link-{i}'
            if link_key in request.form:
                url = request.form[link_key].strip()
                if url:
                    # Clean YouTube URLs to remove extra query parameters
                    url = clean_youtube_url(url)
                    links.append(url)

        print(f"Received {len(links)} links to download")

        if not links:
            return jsonify({'error': 'No links provided'}), 400

        # Create a temporary directory for this download session
        session_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR)

        # Create lock file to indicate download in progress
        try:
            with open(DOWNLOAD_LOCK_FILE, 'w') as f:
                f.write(str(time.time()))
        except Exception:
            pass  # Non-critical, continue anyway

        # Track this download session
        ACTIVE_DOWNLOADS.add(session_dir)

        # Download all links in parallel
        errors = []

        # Track files before download
        files_before = set(os.listdir(session_dir))

        # Parallel download configuration
        # Use 2-3 workers for 1GB RAM (safe, allows 2-3x speedup)
        # Each download uses ~64KB buffer + process overhead (~50-100MB per download)
        MAX_PARALLEL_DOWNLOADS = 4  # 3 is safe for 1GB RAM, have not tested 5

        print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting parallel downloads: {len(links)} links, {MAX_PARALLEL_DOWNLOADS} at a time")

        def download_with_error_handling(url):
            """Download a single URL and return (url, success, error)"""
            try:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [PARALLEL] Downloading: {url}")
                success, error = download_audio(url, session_dir)
                if not success:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] [PARALLEL] Download failed for {url}: {error}")
                    # Truncate long error messages for user display
                    error_msg = str(error)[:200] if len(
                        str(error)) > 200 else str(error)
                    return (url, False, error_msg)
                else:
                    print(
                        f"[{datetime.now().strftime('%H:%M:%S')}] [PARALLEL] Successfully downloaded: {url}")
                    return (url, True, None)
            except Exception as e:
                # Catch individual download errors so one doesn't stop the others
                error_msg = f"Unexpected error: {str(e)[:200]}"
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] [PARALLEL] Exception downloading {url}: {error_msg}")
                return (url, False, error_msg)

        # Execute downloads in parallel
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
            # Submit all download tasks
            future_to_url = {executor.submit(
                download_with_error_handling, url): url for url in links}

            # Collect results as they complete
            completed_count = 0
            for future in as_completed(future_to_url):
                url, success, error = future.result()
                completed_count += 1
                if not success:
                    errors.append(f"{url}: {error}")
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Progress: {completed_count}/{len(links)} downloads completed")

        elapsed_time = time.time() - start_time
        print(f"[{datetime.now().strftime('%H:%M:%S')}] All downloads completed in {elapsed_time:.1f} seconds ({len(links)} links, {MAX_PARALLEL_DOWNLOADS} parallel)")

        # Wait a moment for all downloads to fully complete and files to be written
        time.sleep(2)

        # Get all downloaded files (files that weren't there before)
        files_after = set(os.listdir(session_dir))
        new_files = files_after - files_before
        all_files = [os.path.join(session_dir, f) for f in new_files if os.path.isfile(
            os.path.join(session_dir, f))]

        if not all_files:
            error_msg = 'No files were downloaded.'
            if errors:
                # Limit total error message length
                error_msg += ' Errors: ' + \
                    '; '.join(errors[:5])  # Show max 5 errors
                if len(errors) > 5:
                    error_msg += f' (and {len(errors) - 5} more errors)'
            return jsonify({'error': error_msg}), 500

        # Extract filenames (just basenames, not full paths) for tracking
        downloaded_filenames = [os.path.basename(f) for f in all_files]
        
        # Track visit/download in DynamoDB (non-blocking, errors won't break download)
        if DYNAMODB_AVAILABLE:
            try:
                visit_record = create_visit_record(
                    request=request,
                    links=links,
                    downloaded_files=downloaded_filenames,
                    errors=errors if errors else None
                )
                if visit_record:
                    # Save asynchronously to avoid blocking the response
                    def save_tracking():
                        try:
                            save_visit_to_dynamodb(visit_record)
                        except Exception as e:
                            print(f"Error saving tracking data (non-critical): {e}")
                    
                    threading.Thread(target=save_tracking, daemon=True).start()
            except Exception as e:
                # Tracking errors should never break downloads
                print(f"Error creating visit record (non-critical): {e}")

        # Create a zip file
        zip_path = os.path.join(session_dir, 'downloads.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in all_files:
                if os.path.exists(file_path) and file_path != zip_path:
                    zipf.write(file_path, os.path.basename(file_path))

        # Send the zip file
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='link-downloader-files.zip',
            mimetype='application/zip'
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        # Log full error to server logs
        print(f"Error in download route: {error_trace}")
        # Return user-friendly error (don't expose full traceback)
        return jsonify({'error': f'Server error: {str(e)[:200]}'}), 500

    finally:
        # Clean up after a delay (give time for file to be sent)
        if session_dir:
            def cleanup():
                time.sleep(10)  # Wait 10 seconds before cleanup
                if os.path.exists(session_dir):
                    shutil.rmtree(session_dir, ignore_errors=True)

                # Remove from active downloads
                ACTIVE_DOWNLOADS.discard(session_dir)

                # Remove lock file if no more active downloads
                if len(ACTIVE_DOWNLOADS) == 0:
                    try:
                        if os.path.exists(DOWNLOAD_LOCK_FILE):
                            os.remove(DOWNLOAD_LOCK_FILE)
                    except Exception:
                        pass  # Non-critical

            threading.Thread(target=cleanup, daemon=True).start()


if __name__ == '__main__':
    # Development mode
    environment = os.getenv('ENVIRONMENT', 'production')
    debug_mode = os.getenv('FLASK_ENV') != 'production'

    print(f"Starting Link Downloader server...")
    print(f"Environment: {environment}")
    print(f"Debug mode: {debug_mode}")
    print(f"Make sure yt-dlp is installed: pip install yt-dlp")
    print(f"Server will be available at http://localhost:5000")
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
