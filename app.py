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

        # Use the same command as your Python script
        cmd = [
            yt_dlp_path,
            '--impersonate', 'chrome',
            '--buffer-size', '16K',
            '--limit-rate', '1M',
            '-x',
            '--audio-format', 'm4a',
            '-o', output_path,
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout per download
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
            print(f"Downloading: {url}")
            success, error = download_audio(url, session_dir)
            if not success:
                print(f"Download failed for {url}: {error}")
                errors.append(f"{url}: {error}")
            else:
                print(f"Successfully downloaded: {url}")

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
                error_msg += ' Errors: ' + '; '.join(errors)
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
        print(f"Error in download route: {error_trace}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

    finally:
        # Clean up after a delay (give time for file to be sent)
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
