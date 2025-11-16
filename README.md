# Link Downloader

A web application that converts video links to high-quality audio files. Supports YouTube, SoundCloud, and more.

## Setup Instructions

### 1. Install Python Dependencies

Make sure you have Python 3.7+ installed, then install the required packages:

```bash
pip install -r requirements.txt
```

### 2. Install yt-dlp

The application uses `yt-dlp` for downloading. It should be installed automatically with the requirements, but if you need to install it separately:

```bash
pip install yt-dlp
```

Or if you prefer using the standalone executable:
- Windows: Download from [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases)
- Make sure `yt-dlp.exe` is in your PATH or in the project directory

### 3. Run the Server

Start the Flask development server:

```bash
python app.py
```

The server will start on `http://localhost:5000`

### 4. Use the Application

1. Open your browser and go to `http://localhost:5000`
2. Paste up to 10 video links in the form
3. Click "Download All"
4. Wait for the downloads to complete (this may take a few minutes depending on video length)
5. A ZIP file will be downloaded containing all the converted audio files

## Notes

- Downloads are stored temporarily in the `downloads/` folder
- Files are automatically cleaned up after 10 seconds
- The server runs in debug mode for development
- For production deployment, you'll want to:
  - Disable debug mode
  - Use a production WSGI server (like Gunicorn)
  - Set up proper error handling and logging
  - Configure timeouts appropriately

## Troubleshooting

- **"yt-dlp not found"**: Make sure yt-dlp is installed and accessible from your PATH
- **Downloads fail**: Check that the URLs are valid and accessible
- **Timeout errors**: Some videos may take longer to download. Consider increasing the timeout in `app.py`

