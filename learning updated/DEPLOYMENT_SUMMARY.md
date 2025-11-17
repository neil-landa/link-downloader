# Deployment Summary - Direct Answers

## Your Questions Answered

### ❓ "What do I need to put into an S3 bucket?"

**Answer: NOTHING for the main app!**

S3 is for **static files only** (HTML, CSS, JS, images). Your Flask app needs a **server** to run Python code.

**Optional S3 usage:**

- You CAN put static assets (CSS, JS, images) in S3 + CloudFront for faster loading
- But you DON'T HAVE TO - Flask can serve them just fine
- The Flask app itself MUST run on EC2 or Elastic Beanstalk

### ❓ "How do I handle the requests, the API calls?"

**Answer: Your Flask app handles them!**

1. **User visits:** `https://script.neillanda.com`

   - DNS (Route 53/Cloudflare) → Points to your server
   - Nginx (reverse proxy) → Serves static files (CSS/JS/images) directly
   - Nginx → Forwards dynamic requests to Flask on port 5000
   - Flask serves `index.html`

2. **User submits form:**
   - JavaScript sends POST to `/download`
   - Nginx proxies request to Flask
   - Flask processes request:
     - Uses cookies.txt for YouTube authentication (if available)
     - Tries multiple download strategies (default → Android → impersonate → web)
     - Downloads files using yt-dlp (with Node.js support)
     - Creates ZIP file
   - Flask sends ZIP back through Nginx to user

**No separate API needed** - Flask IS your API!

### ❓ "I will create a CNAME script.neillanda.com"

**Answer: Perfect! Here's how:**

#### If using Elastic Beanstalk:

```
CNAME: script.neillanda.com → link-downloader-env.eba-xxxxx.us-east-1.elasticbeanstalk.com
```

#### If using EC2:

```
A Record: script.neillanda.com → [Your EC2 Elastic IP]
OR
CNAME: script.neillanda.com → ec2-xx-xx-xx-xx.compute-1.amazonaws.com
```

**Note:** Use A record if you have a static IP (Elastic IP), CNAME if using dynamic IP.

---

## What Goes Where?

### ✅ On Your Server (EC2/EB):

- `app.py` - Your Flask application
- `requirements.txt` - Python dependencies (includes curl-cffi)
- `index.html` - Your HTML
- `css/` - Stylesheets (served by Nginx)
- `js/` - JavaScript (served by Nginx)
- `img/` - Images (served by Nginx)
- `cookies.txt` - YouTube authentication cookies (optional but recommended)
- All Python code
- **System dependencies:**
  - Node.js (for YouTube default player client)
  - curl with OpenSSL support (for impersonate feature)
  - yt-dlp (installed via pip)
  - ffmpeg (for audio conversion)

### ✅ In Route 53 (DNS):

- CNAME or A record pointing `script` → your server

### ❌ NOT in S3:

- Flask app (needs server)
- Python code
- Dynamic content

### ✅ Optional in S3:

- Static assets (for CDN/caching)
- But not required!

---

## Recommended Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Route 53       │  (DNS: script.neillanda.com)
│  (DNS)          │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  CloudFront     │  (Optional - CDN for static files)
│  (Optional)     │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  EC2 Instance   │  OR  Elastic Beanstalk
│  ┌───────────┐  │
│  │  Nginx    │  │  (Serves static files, reverse proxy, SSL)
│  │           │  │  (Static: CSS/JS/images served directly)
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  Flask    │  │  (Your app.py)
│  │  (port    │  │  (Handles /download route)
│  │   5000)   │  │
│  └─────┬─────┘  │
│        │        │
│  ┌─────▼─────┐  │
│  │  yt-dlp   │  │  (Downloads videos)
│  │  + Node.js│  │  (YouTube player client)
│  │  + cookies │  │  (Authentication)
│  └───────────┘  │
└─────────────────┘
```

---

## Step-by-Step: What You Need to Do

### Step 1: Choose Deployment Method

**Option A: Elastic Beanstalk (Easier)**

- Follow: `AWS_DEPLOYMENT_GUIDE.md` → Option 1
- Time: ~15 minutes
- Best for: Quick deployment, less control needed

**Option B: EC2 (More Control)**

- Follow: `AWS_DEPLOYMENT_GUIDE.md` → Option 2
- Time: ~30 minutes
- Best for: Learning, full control, customization

### Step 2: Deploy Your Application

**If EC2:**

1. Launch EC2 instance (t2.micro, free tier)
2. Upload your files (Git or SCP)
3. Run `deploy.sh` script
4. Get your server's IP address

**If Elastic Beanstalk:**

1. Install EB CLI: `pip install awsebcli`
2. Run: `eb init` then `eb create`
3. Get your EB URL

### Step 3: Configure DNS

1. Go to Route 53 (or your DNS provider)
2. Find hosted zone for `neillanda.com`
3. Create record:
   - **Name:** `script`
   - **Type:** `CNAME` (EB) or `A` (EC2 with Elastic IP)
   - **Value:** Your server URL or IP
4. Wait 5-30 minutes for propagation

### Step 4: Set Up SSL (HTTPS)

**On EC2:**

```bash
sudo certbot --nginx -d script.neillanda.com
```

**On Elastic Beanstalk:**

- Use AWS Certificate Manager
- Configure in EB console

### Step 5: Test!

1. Visit `https://script.neillanda.com`
2. Try downloading a link
3. Check logs if issues: `sudo journalctl -u link-downloader -f`

---

## File Structure on Server

```
/home/ec2-user/link-downloader/
├── app.py                 # Flask application
├── application.py         # EB entry point (if using EB)
├── requirements.txt       # Python dependencies
├── index.html            # Your HTML
├── css/                  # Stylesheets
├── js/                   # JavaScript
├── img/                  # Images
├── downloads/            # Temporary download folder (created automatically)
├── nginx.conf            # Nginx config (reference)
└── deploy.sh            # Deployment script
```

---

## Quick Commands Reference

### Check if app is running:

```bash
sudo systemctl status link-downloader
```

### View logs:

```bash
sudo journalctl -u link-downloader -f
```

### Restart app:

```bash
sudo systemctl restart link-downloader
```

### Test Nginx config:

```bash
sudo nginx -t
```

### Restart Nginx:

```bash
sudo systemctl restart nginx
```

### Check yt-dlp:

```bash
yt-dlp --version
```

### Check Node.js:

```bash
node --version
npm --version
```

### Check cookies:

```bash
ls -lh /home/ubuntu/www/link-downloader/cookies.txt
yt-dlp --cookies /path/to/cookies.txt --list-formats https://www.youtube.com/watch?v=test
```

### Check nginx static file serving:

```bash
curl -I https://script.neillanda.com/css/style.css
# Should return 200 OK, not 404
```

---

## Cost Estimate

**Monthly costs (after free tier):**

- EC2 t2.micro: ~$8-10
- Route 53: ~$0.50
- Data transfer: ~$1-5 (depends on usage)
- **Total: ~$10-20/month**

**Free tier (first 12 months):**

- EC2: 750 hours/month FREE
- Route 53: First hosted zone FREE
- **Total: ~$0.50/month** (just Route 53 queries)

---

## Common Mistakes to Avoid

1. ❌ **Putting Flask app in S3** - Won't work, needs a server
2. ❌ **Forgetting to open ports** - Security group must allow 80/443
3. ❌ **Leaving debug mode on** - Security risk in production
4. ❌ **Not setting up SSL** - Users expect HTTPS
5. ❌ **Forgetting to install yt-dlp** - Downloads will fail
6. ❌ **Not installing Node.js** - YouTube downloads may fail
7. ❌ **Not setting up cookies** - YouTube will block with "Sign in to confirm" errors
8. ❌ **Wrong nginx location order** - Static files must come before `location /`
9. ❌ **Wrong file permissions** - www-data can't read files (CSS/JS won't load)
10. ❌ **Not setting up rate limiting** - Can be abused

---

## Next Steps After Deployment

1. ✅ Test the application
2. ✅ **Set up YouTube cookies** (export from browser, upload to server)
3. ✅ Verify static files load (CSS/JS/images)
4. ✅ Set up monitoring (CloudWatch)
5. ✅ Enable rate limiting (uncomment in app.py)
6. ✅ Set up cookie refresh automation (see `refresh-cookies-local.sh`)
7. ✅ Set up backups (optional)
8. ✅ Configure billing alerts
9. ✅ Set up automated updates (optional)

---

## Need Help?

1. **Check logs first:** `sudo journalctl -u link-downloader -f`
2. **Verify security groups:** Ports 80/443 must be open
3. **Test DNS:** `nslookup script.neillanda.com`
4. **Read full guide:** `AWS_DEPLOYMENT_GUIDE.md`
5. **Quick reference:** `QUICK_DEPLOY.md`

---

**TL;DR:**

- **S3:** Not needed (or optional for static files only)
- **Server:** EC2 or Elastic Beanstalk (required)
- **DNS:** Point `script.neillanda.com` to your server
- **Flask:** Handles all requests automatically
- **No separate API needed:** Flask IS your API

Good luck with deployment! 🚀
