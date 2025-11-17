# Code Walkthrough - Line by Line

This document walks through the actual code files and explains what each important part does.

## app.py - The Flask Server

```python
import os
import subprocess
import zipfile
import tempfile
import shutil
from flask import Flask, request, send_file, render_template, jsonify
```

**What this does:** Imports all the tools we need

- `os`: File system operations (paths, directories)
- `subprocess`: Run command-line programs (yt-dlp)
- `zipfile`: Create ZIP archives
- `tempfile`: Create temporary directories
- `flask`: Web framework components

```python
app = Flask(__name__, static_folder='.', static_url_path='')
```

**What this does:** Creates the Flask application

- `__name__`: Python's way of identifying this file
- `static_folder='.'`: Serve static files (HTML/CSS/JS) from current directory
- `static_url_path=''`: No prefix needed (files at root URL)

```python
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), 'downloads')
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

COOKIES_FILE = os.path.join(os.path.dirname(__file__), 'cookies.txt')
```

**What this does:** Creates downloads folder and defines cookie path

- `__file__`: Path to this Python file
- `os.path.dirname()`: Gets the folder containing this file
- `os.path.join()`: Combines paths (works on Windows/Mac/Linux)
- `os.makedirs(..., exist_ok=True)`: Create folder if it doesn't exist
- `COOKIES_FILE`: Path to YouTube authentication cookies (optional but recommended)

```python
def download_audio(url, output_dir):
    """Download audio from a URL using yt-dlp"""
    try:
        output_path = os.path.join(output_dir, '%(title)s.%(ext)s')
```

**What this does:** Defines a reusable function

- `%(title)s`: yt-dlp placeholder for video title
- `%(ext)s`: yt-dlp placeholder for file extension
- Example result: "My Video.m4a"

```python
        # Check if cookies file exists and is valid
        use_cookies = os.path.exists(COOKIES_FILE)
        if use_cookies:
            if os.path.getsize(COOKIES_FILE) == 0:
                use_cookies = False  # Empty file, don't use it

        # Common options for all commands
        common_opts = [
            '--buffer-size', '16K',
            '--limit-rate', '1M',
            '--no-warnings',
            '-x',
            '--audio-format', 'm4a',
            '-o', output_path,
            url
        ]

        # Add cookies if available
        if use_cookies:
            common_opts = ['--cookies', COOKIES_FILE] + common_opts
```

**What this does:** Checks for cookies and builds base command

- Checks if cookies file exists and isn't empty
- Builds common options that all strategies will use
- Adds `--cookies` flag if cookies are available
- Cookies are required for YouTube to bypass bot detection

```python
        # Try multiple strategies for YouTube (with fallbacks)
        if is_youtube:
            # Strategy 1: Default player client (requires Node.js)
            cmd_default = ['yt-dlp', '--extractor-args', 'youtube:player_client=default'] + common_opts
            result = subprocess.run(cmd_default, ...)

            # Strategy 2: Android client (if default fails)
            if result.returncode != 0:
                cmd_android = ['yt-dlp', '--extractor-args', 'youtube:player_client=android'] + common_opts
                result = subprocess.run(cmd_android, ...)

            # Strategy 3: With impersonate (if Android fails)
            # Strategy 4: Web client (last resort)
```

**What this does:** Tries multiple download strategies with fallbacks

- YouTube has bot detection, so we try different approaches
- Default client (most reliable, needs Node.js)
- Android client (works without Node.js)
- With impersonate (if curl-cffi available)
- Web client (last resort)
- Each strategy is tried only if previous one fails

```python
        if result.returncode == 0:
            return True, None
        else:
            error_msg = result.stderr
            # Check for common cookie-related errors
            if 'cookies' in error_msg.lower() or 'sign in' in error_msg.lower():
                if use_cookies:
                    error_msg += " (Cookies may be expired or invalid. Try refreshing them.)"
                else:
                    error_msg += " (Cookies file not found. Export cookies from your browser.)"
            return False, error_msg
```

**What this does:** Check if command succeeded and provide helpful errors

- `returncode == 0`: Success (Unix/Linux convention)
- Returns tuple: `(success_boolean, error_message)`
- Detects cookie-related errors and adds helpful hints
- Helps users understand when cookies need refreshing

```python
# Error handler to ensure JSON responses for API errors
@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.route('/')
def index():
    return send_file('index.html')
```

**What this does:** Sets up error handlers and home page route

- `@app.errorhandler(500)`: Catches all 500 errors, returns JSON (not HTML)
- `@app.errorhandler(404)`: Catches 404 errors, returns JSON
- Ensures JavaScript always gets JSON, not HTML error pages
- `@app.route('/')`: Decorator - tells Flask this function handles "/"
- When user visits `http://localhost:5000/`, this function runs
- `send_file()`: Sends the HTML file to browser

```python
@app.route('/download', methods=['POST'])
def download():
```

**What this does:** Defines download endpoint

- `methods=['POST']`: Only accepts POST requests
- GET requests (like visiting a URL) will be rejected

```python
        links = []
        for i in range(1, 11):
            link_key = f'link-{i}'
            if link_key in request.form:
                url = request.form[link_key].strip()
                if url:
                    links.append(url)
```

**What this does:** Extracts URLs from form

- `range(1, 11)`: Numbers 1 through 10
- `f'link-{i}'`: String formatting (creates "link-1", "link-2", etc.)
- `request.form`: Dictionary of form data
- `.strip()`: Removes whitespace from start/end
- Only adds non-empty URLs to list

```python
        session_dir = tempfile.mkdtemp(dir=DOWNLOAD_DIR)
```

**What this does:** Creates unique temporary folder

- `mkdtemp()`: Makes temporary directory
- Returns path like: `downloads/tmpABC123/`
- Each request gets its own folder (prevents conflicts)

```python
        files_before = set(os.listdir(session_dir))
```

**What this does:** Records files before downloads

- `os.listdir()`: Lists all files in directory
- `set()`: Converts to set for easy comparison
- We'll compare later to find new files

```python
        for url in links:
            print(f"Downloading: {url}")
            success, error = download_audio(url, session_dir)
            if not success:
                print(f"Download failed for {url}: {error}")
                errors.append(f"{url}: {error}")
```

**What this does:** Downloads each URL

- Loops through all URLs
- Calls `download_audio()` function
- Collects errors but continues (doesn't stop on first failure)

```python
        time.sleep(3)
```

**What this does:** Waits for downloads to finish

- `subprocess.run()` doesn't always wait for file writes
- Gives filesystem time to finish writing
- **Note:** This is a simple solution. Better: poll for file existence

```python
        files_after = set(os.listdir(session_dir))
        new_files = files_after - files_before
```

**What this does:** Finds downloaded files

- `files_after - files_before`: Set subtraction
- Only gets files that weren't there before
- Filters out any temp files created by yt-dlp

```python
        all_files = [os.path.join(session_dir, f) for f in new_files
                     if os.path.isfile(os.path.join(session_dir, f))]
```

**What this does:** Creates full file paths

- List comprehension: creates list in one line
- `os.path.join()`: Combines directory + filename
- `os.path.isfile()`: Only includes files (not subdirectories)

```python
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in all_files:
                if os.path.exists(file_path) and file_path != zip_path:
                    zipf.write(file_path, os.path.basename(file_path))
```

**What this does:** Creates ZIP file

- `with` statement: Automatically closes file when done
- `'w'`: Write mode (creates new file)
- `ZIP_DEFLATED`: Compression method
- `zipf.write()`: Adds file to ZIP
- `os.path.basename()`: Gets just filename (not full path)

```python
        return send_file(
            zip_path,
            as_attachment=True,
            download_name='link-downloader-files.zip',
            mimetype='application/zip'
        )
```

**What this does:** Sends ZIP to browser

- `as_attachment=True`: Forces download (not view)
- `download_name`: What user sees as filename
- `mimetype`: Tells browser it's a ZIP file

```python
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in download route: {error_trace}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500
```

**What this does:** Handles any errors

- `except Exception`: Catches all errors
- `traceback.format_exc()`: Gets full error details
- `jsonify()`: Converts to JSON (JavaScript can read it)
- `500`: HTTP status code for server error

```python
        def cleanup():
            time.sleep(10)
            if os.path.exists(session_dir):
                shutil.rmtree(session_dir, ignore_errors=True)

        threading.Thread(target=cleanup, daemon=True).start()
```

**What this does:** Cleans up files later

- `threading.Thread()`: Runs function in background
- `daemon=True`: Thread dies when main program ends
- Waits 10 seconds (gives time for file download)
- `shutil.rmtree()`: Deletes entire directory
- `ignore_errors=True`: Doesn't crash if delete fails

---

## js/script.js - The Frontend Logic

```javascript
const downloadForm = document.querySelector("#linkDownloadForm");
```

**What this does:** Finds the form element

- `document`: The HTML document
- `querySelector()`: CSS selector to find element
- `"#linkDownloadForm"`: ID selector (the `#` means ID)
- Stores reference in variable

```javascript
if (downloadForm) {
```

**What this does:** Safety check

- Only runs if form exists
- Prevents errors if JavaScript loads before HTML

```javascript
  downloadForm.addEventListener("submit", async function (e) {
```

**What this does:** Listens for form submission

- `addEventListener()`: Attaches event handler
- `"submit"`: Event type (form button clicked or Enter pressed)
- `async function`: Can use `await` inside
- `e`: Event object (contains info about the event)

```javascript
e.preventDefault();
```

**What this does:** Stops default behavior

- Default: Form submits, page reloads
- We want: Stay on page, show feedback

```javascript
const submitBtn = downloadForm.querySelector('button[type="submit"]');
const originalText = submitBtn.textContent;
```

**What this does:** Gets the button

- Finds submit button in the form
- Saves original text to restore later

```javascript
submitBtn.disabled = true;
submitBtn.textContent = "Downloading... Please wait";
```

**What this does:** Shows loading state

- `disabled = true`: Prevents clicking again
- Changes button text to show progress

```javascript
let errorDiv = document.querySelector(".error-message");
if (!errorDiv) {
  errorDiv = document.createElement("div");
  errorDiv.className = "error-message";
  errorDiv.style.cssText = "...";
  downloadForm.appendChild(errorDiv);
}
```

**What this does:** Creates error display element

- Checks if error div exists
- If not, creates new `<div>` element
- Sets CSS styles inline
- Adds to form (so it appears on page)

```javascript
const formData = new FormData(downloadForm);
```

**What this does:** Collects form data

- `FormData`: Browser API for form data
- Automatically gets all inputs with `name` attribute
- Creates: `{ "link-1": "url1", "link-2": "url2", ... }`

```javascript
const response = await fetch("/download", {
  method: "POST",
  body: formData,
});
```

**What this does:** Sends request to server

- `fetch()`: Modern way to make HTTP requests
- `await`: Waits for response (doesn't block other code)
- `method: "POST"`: HTTP method
- `body: formData`: The data to send

```javascript
    if (response.ok) {
```

**What this does:** Checks if request succeeded

- `response.ok`: True if status code 200-299
- False if 400+ (client error) or 500+ (server error)

```javascript
const blob = await response.blob();
```

**What this does:** Gets file data

- `blob()`: Converts response to binary data
- `Blob`: Binary Large Object (file data)

```javascript
const url = window.URL.createObjectURL(blob);
const a = document.createElement("a");
a.href = url;
a.download = "link-downloader-files.zip";
document.body.appendChild(a);
a.click();
window.URL.revokeObjectURL(url);
document.body.removeChild(a);
```

**What this does:** Triggers download

- `createObjectURL()`: Creates temporary URL for blob
- Creates `<a>` (anchor/link) element
- Sets `href` to blob URL
- Sets `download` attribute (forces download)
- Adds to page (required for click to work)
- Programmatically clicks it
- Cleans up URL and element

```javascript
    } else {
      // Handle error response - try to parse as JSON, fallback to text
      let errorMessage = "Unknown error occurred";
      try {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.includes("application/json")) {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } else {
          // If not JSON, get text response
          const text = await response.text();
          errorMessage = text.substring(0, 200); // Limit length
        }
      } catch (parseError) {
        errorMessage = `Server returned error (status ${response.status})`;
      }
      errorDiv.textContent = `Error: ${errorMessage}`;
      errorDiv.style.display = "block";
```

**What this does:** Handles errors gracefully

- Checks if response is JSON or HTML
- Tries to parse JSON first
- Falls back to text if not JSON (handles HTML error pages)
- Prevents "Unexpected token" errors when server returns HTML
- Limits error message length for display

```javascript
    } catch (error) {
      console.error("Download error:", error);
      errorDiv.textContent = `Error: ${error.message || "Failed to connect"}`;
```

**What this does:** Catches network errors

- `catch`: Handles exceptions (network failures, etc.)
- `console.error()`: Logs to browser console
- Shows user-friendly error message

---

## index.html - The Structure

```html
<form method="POST" action="/download" id="linkDownloadForm"></form>
```

**What this does:** Defines the form

- `method="POST"`: How to send data
- `action="/download"`: Where to send it
- `id="linkDownloadForm"`: Unique identifier

```html
<input type="url" name="link-1" id="link-1" />
```

**What this does:** Creates input field

- `type="url"`: Browser validates URL format
- `name="link-1"`: Key in form data
- `id="link-1"`: For JavaScript/CSS targeting

```html
<button type="submit">Download All</button>
```

**What this does:** Submit button

- `type="submit"`: Triggers form submission
- Clicking this runs the JavaScript handler

---

## Key Patterns to Recognize

### 1. Request-Response Pattern

```
Client sends request → Server processes → Server sends response
```

### 2. Error Handling Pattern

```python
try:
    # Do something risky
except Exception as e:
    # Handle error gracefully
```

### 3. Async Pattern

```javascript
async function doSomething() {
  const result = await someAsyncOperation();
  // Use result here
}
```

### 4. Event-Driven Pattern

```javascript
element.addEventListener("event", function () {
  // React to event
});
```

---

## Common Modifications You Might Want

### Add Progress Indicator

```javascript
// In JavaScript, before fetch:
const progressDiv = document.createElement("div");
progressDiv.textContent = "Processing...";
form.appendChild(progressDiv);

// In Flask, you'd need to use Server-Sent Events or WebSockets
// (More advanced - for later!)
```

### Change Download Format

```python
# In download_audio(), change:
'--audio-format', 'mp3',  # Instead of 'm4a'
```

### Add More Input Fields Dynamically

```javascript
function addLinkField() {
  const newInput = document.createElement("input");
  newInput.type = "url";
  newInput.name = `link-${linkCount++}`;
  form.appendChild(newInput);
}
```

### Show Individual Download Status

```python
# In Flask, return JSON with status:
return jsonify({
    'status': 'processing',
    'completed': 3,
    'total': 10
})
```

---

This walkthrough should help you understand every part of the code. Try modifying small parts and see what happens!
