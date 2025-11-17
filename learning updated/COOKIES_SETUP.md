# How to Set Up Cookies for YouTube Downloads

YouTube requires authentication cookies to bypass bot detection. Follow these steps to export cookies from your browser.

## Method 1: Using Browser Extension (Easiest)

### Chrome/Edge:

1. Install the "Get cookies.txt LOCALLY" extension:

   - Chrome: https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc
   - Edge: Available in Edge Add-ons store

2. Go to https://www.youtube.com (make sure you're logged in)

3. Click the extension icon → Click "Export" → Save as `cookies.txt`

4. Upload the file to your server at: `/home/ubuntu/www/link-downloader/cookies.txt`

### Firefox:

1. Install "cookies.txt" extension: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

2. Go to https://www.youtube.com (make sure you're logged in)

3. Click the extension icon → Click "Export" → Save as `cookies.txt`

4. Upload the file to your server at: `/home/ubuntu/www/link-downloader/cookies.txt`

## Method 2: Using yt-dlp Directly (Alternative)

You can also use yt-dlp to extract cookies from your browser:

```bash
# Extract cookies from Chrome
yt-dlp --cookies-from-browser chrome --cookies cookies.txt https://www.youtube.com/watch?v=test

# Or from Firefox
yt-dlp --cookies-from-browser firefox --cookies cookies.txt https://www.youtube.com/watch?v=test
```

Then copy the `cookies.txt` file to your server.

## Method 3: Manual Export (Advanced)

1. Open browser DevTools (F12)
2. Go to Application/Storage tab → Cookies → https://www.youtube.com
3. Export cookies in Netscape format
4. Save as `cookies.txt`

## Uploading to Server

Once you have the `cookies.txt` file:

```bash
# From your local machine, upload to server:
scp cookies.txt ubuntu@your-server:/home/ubuntu/www/link-downloader/

# Or if you're already on the server, just copy it there:
# Place cookies.txt in /home/ubuntu/www/link-downloader/
```

## File Permissions

Make sure the cookies file is readable:

```bash
chmod 644 /home/ubuntu/www/link-downloader/cookies.txt
```

## Important Notes

- **Cookies expire**: You'll need to refresh them periodically (usually every few weeks)
- **Keep cookies private**: Don't commit `cookies.txt` to git (it's already in .gitignore)
- **Log in first**: Make sure you're logged into YouTube when exporting cookies
- **File location**: The file must be at `/home/ubuntu/www/link-downloader/cookies.txt`

## Testing

After uploading cookies, restart your service:

```bash
sudo systemctl restart link-downloader
```

Then test a YouTube download. The service will automatically use cookies if the file exists.

---

## Automating Cookie Refresh

Cookies expire after a few weeks. Here are options to automate refreshing:

### Option 1: Automated Upload from Local Machine (Recommended)

**Best if:** You have a computer that's usually on (Mac/Windows/Linux)

1. **Edit `refresh-cookies-local.sh`** and set your server details:

   ```bash
   SERVER_USER="ubuntu"
   SERVER_HOST="your-server-ip"
   ```

2. **Make it executable:**

   ```bash
   chmod +x refresh-cookies-local.sh
   ```

3. **Set up a cron job** (runs weekly):

   ```bash
   # On Mac/Linux, edit crontab:
   crontab -e

   # Add this line (runs every Sunday at 2 AM):
   0 2 * * 0 /path/to/refresh-cookies-local.sh >> /tmp/cookie-refresh.log 2>&1
   ```

4. **On Windows**, use Task Scheduler to run the script weekly.

**Pros:** Simple, uses your existing browser login  
**Cons:** Requires a computer to be on

### Option 2: Server-Side Browser Cookie Extraction

**Best if:** Your server has a browser installed with a logged-in session

1. **Install browser on server** (if not already):

   ```bash
   # For Chrome/Chromium:
   sudo apt install chromium-browser -y

   # Or use yt-dlp's built-in extraction (no browser needed if you sync browser profile)
   ```

2. **Use the refresh script:**

   ```bash
   chmod +x refresh-cookies.sh
   ./refresh-cookies.sh --from-browser
   ```

3. **Set up cron job on server:**

   ```bash
   sudo crontab -e

   # Add (runs weekly on Sunday at 3 AM):
   0 3 * * 0 /home/ubuntu/www/link-downloader/refresh-cookies.sh --from-browser >> /var/log/cookie-refresh.log 2>&1
   ```

**Pros:** Fully automated on server  
**Cons:** Requires browser installation and logged-in session on server

### Option 3: Headless Browser Automation (Advanced)

**Best if:** You want fully automated login on the server

1. **Install dependencies:**

   ```bash
   pip3 install selenium playwright
   playwright install chromium
   ```

2. **Set up automated login** (modify `refresh-cookies-headless.py` with your credentials)

3. **Set up cron job:**
   ```bash
   sudo crontab -e
   0 3 * * 0 /usr/bin/python3 /home/ubuntu/www/link-downloader/refresh-cookies-headless.py
   ```

**Pros:** Fully automated, no local machine needed  
**Cons:** More complex, requires storing credentials securely

### Option 4: Manual Refresh (Simplest)

Just run the local script manually when cookies expire (usually every 2-4 weeks):

```bash
./refresh-cookies-local.sh
```

## Recommended Approach

For most users, **Option 1** (automated upload from local machine) is best:

- Uses your existing browser login
- Simple to set up
- No server-side browser needed
- Just needs your computer to be on weekly (or you can run manually)

## Troubleshooting

**Cookies expired?** Run the refresh script manually:

```bash
./refresh-cookies-local.sh
```

**Check cookie file:**

```bash
# On server:
ls -lh /home/ubuntu/www/link-downloader/cookies.txt
cat /home/ubuntu/www/link-downloader/cookies.txt | head -5
```

**Test cookie extraction locally:**

```bash
yt-dlp --cookies-from-browser chrome --cookies /tmp/test-cookies.txt https://www.youtube.com/watch?v=dQw4w9WgXcQ
```
