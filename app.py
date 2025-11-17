import os
import subprocess
import zipfile
import tempfile
import shutil
from flask import Flask, request, send_file, render_template, jsonify
from werkzeug.utils import secure_filename
import threading
import time

app = Flask(__name__, static_folder='.', static_url_path='')

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


def download_audio(url, output_dir):
    """Download audio from a URL using yt-dlp"""
    try:
        # Find yt-dlp in PATH or common locations
        import shutil
        yt_dlp_path = shutil.which('yt-dlp')
        if not yt_dlp_path:
            # Try common locations
            for path in ['/usr/local/bin/yt-dlp', '/usr/bin/yt-dlp',
                         '/home/ubuntu/.local/bin/yt-dlp', 'yt-dlp']:
                if os.path.exists(path) or path == 'yt-dlp':
                    yt_dlp_path = path
                    break

        if not yt_dlp_path or (yt_dlp_path != 'yt-dlp' and not os.path.exists(yt_dlp_path)):
            return False, "yt-dlp not found. Please install it: pip install yt-dlp"

        # Create a safe filename - yt-dlp uses %(title)s.%(ext)s format
        output_path = os.path.join(output_dir, '%(title)s.%(ext)s')

        # Common options for all commands
        common_opts = [
            '--buffer-size', '16K',
            '--limit-rate', '1M',
            '--no-warnings',  # Reduce noise in logs
            '--extract-flat', 'false',  # Ensure full extraction
            '-x',  # Extract audio only
            '--audio-format', 'm4a',
            '-o', output_path,
            url
        ]

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
            return False, result.stderr
    except subprocess.TimeoutExpired:
        return False, "Download timeout"
    except FileNotFoundError:
        return False, "yt-dlp not found. Please install it: pip install yt-dlp"
    except Exception as e:
        return False, str(e)


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_file('index.html')


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
                    links.append(url)

        print(f"Received {len(links)} links to download")

        if not links:
            return jsonify({'error': 'No links provided'}), 400

        # Create a temporary directory for this download session
        session_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR)
        # Download all links
        errors = []

        # Track files before download
        files_before = set(os.listdir(session_dir))

        for url in links:
            try:
                print(f"Downloading: {url}")
                success, error = download_audio(url, session_dir)
                if not success:
                    print(f"Download failed for {url}: {error}")
                    # Truncate long error messages for user display
                    error_msg = str(error)[:200] if len(
                        str(error)) > 200 else str(error)
                    errors.append(f"{url}: {error_msg}")
                else:
                    print(f"Successfully downloaded: {url}")
            except Exception as e:
                # Catch individual download errors so one doesn't stop the others
                error_msg = f"Unexpected error: {str(e)[:200]}"
                print(f"Exception downloading {url}: {error_msg}")
                errors.append(f"{url}: {error_msg}")

        # Wait a moment for all downloads to complete
        time.sleep(3)

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

            threading.Thread(target=cleanup, daemon=True).start()


if __name__ == '__main__':
    # Development mode
    import os
    debug_mode = os.getenv('FLASK_ENV') != 'production'

    print("Starting Link Downloader server...")
    print("Make sure yt-dlp is installed: pip install yt-dlp")
    print("Server will be available at http://localhost:5000")
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
