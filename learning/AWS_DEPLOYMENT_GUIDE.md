# AWS Deployment Guide for Link Downloader

## ⚠️ Important: Why S3 Alone Won't Work

**S3 is for static files only** (HTML, CSS, JS, images). Your application has:
- **Backend server** (Flask) that processes requests
- **Python code** that runs yt-dlp
- **Dynamic responses** (downloads files, creates ZIPs)

**You need a compute service**, not just storage. Options:
1. **EC2** (Virtual server) - Most control, more setup
2. **Elastic Beanstalk** (Managed platform) - Easier, less control
3. **Lambda + API Gateway** (Serverless) - Complex for this use case
4. **ECS/Fargate** (Containers) - Good for scaling, more complex

**Recommendation:** Start with **EC2** or **Elastic Beanstalk** for simplicity.

---

## Option 1: AWS Elastic Beanstalk (Recommended for Beginners)

**Pros:**
- Easiest to set up
- Auto-scaling built-in
- Handles load balancing
- Free tier eligible

**Cons:**
- Less control over server
- Slightly more expensive than EC2

### Step-by-Step: Elastic Beanstalk Deployment

#### 1. Prepare Your Application

Create these files in your project:

**File: `application.py`** (Elastic Beanstalk looks for this name)
```python
# This is just app.py renamed - same content
# Or create a wrapper:
from app import app

if __name__ == '__main__':
    app.run()
```

**File: `.ebextensions/python.config`** (Create `.ebextensions` folder)
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application:app
```

**File: `Procfile`** (For process management)
```
web: python application.py
```

**File: `.ebignore`** (Like .gitignore, but for EB)
```
downloads/
__pycache__/
*.pyc
.env
.git/
```

#### 2. Install EB CLI

```bash
pip install awsebcli
```

#### 3. Initialize Elastic Beanstalk

```bash
eb init -p python-3.11 link-downloader --region us-east-1
```

- Choose default settings
- This creates `.elasticbeanstalk/` folder`

#### 4. Create Environment

```bash
eb create link-downloader-env
```

This will:
- Create EC2 instance
- Set up load balancer
- Configure security groups
- Deploy your app

#### 5. Set Environment Variables (if needed)

```bash
eb setenv FLASK_ENV=production
```

#### 6. Deploy Updates

```bash
eb deploy
```

#### 7. Get Your URL

```bash
eb status
```

You'll get a URL like: `link-downloader-env.eba-xxxxx.us-east-1.elasticbeanstalk.com`

---

## Option 2: EC2 (More Control, More Setup)

**Pros:**
- Full control over server
- Cheaper for single instance
- Can customize everything

**Cons:**
- More manual setup
- You manage updates/security
- Need to set up everything yourself

### Step-by-Step: EC2 Deployment

#### 1. Launch EC2 Instance

1. Go to **EC2 Console** → **Launch Instance**
2. Choose **Amazon Linux 2023** (free tier eligible)
3. Instance type: **t2.micro** (free tier)
4. Create/select key pair (save the `.pem` file!)
5. Configure security group:
   - **HTTP** (port 80) from anywhere (0.0.0.0/0)
   - **HTTPS** (port 443) from anywhere
   - **SSH** (port 22) from your IP only
6. Launch instance

#### 2. Connect to Your Instance

**Windows (using PowerShell or PuTTY):**
```bash
ssh -i "your-key.pem" ec2-user@your-instance-ip
```

**Note:** You'll need to get the public IP from EC2 console.

#### 3. Install Dependencies on Server

```bash
# Update system
sudo yum update -y

# Install Python 3.11
sudo yum install python3.11 python3.11-pip -y

# Install yt-dlp
pip3.11 install yt-dlp

# Install system dependencies for yt-dlp
sudo yum install ffmpeg -y
```

#### 4. Install Your Application

**Option A: Using Git (Recommended)**
```bash
# Install Git
sudo yum install git -y

# Clone your repository
cd /home/ec2-user
git clone https://github.com/yourusername/link-downloader.git
cd link-downloader

# Install Python dependencies
pip3.11 install -r requirements.txt
```

**Option B: Using SCP (Copy files)**
```bash
# From your local machine:
scp -i "your-key.pem" -r * ec2-user@your-instance-ip:/home/ec2-user/link-downloader/
```

#### 5. Set Up Application as Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/link-downloader.service
```

Add this content:
```ini
[Unit]
Description=Link Downloader Flask App
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/link-downloader
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/python3.11 /home/ec2-user/link-downloader/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable link-downloader
sudo systemctl start link-downloader
sudo systemctl status link-downloader
```

#### 6. Install and Configure Nginx (Reverse Proxy)

```bash
# Install Nginx
sudo yum install nginx -y

# Configure Nginx
sudo nano /etc/nginx/conf.d/link-downloader.conf
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name script.neillanda.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for long downloads
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

Start Nginx:
```bash
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl restart nginx
```

#### 7. Update Flask App for Production

Modify `app.py`:
```python
if __name__ == '__main__':
    # Don't use debug mode in production!
    app.run(host='0.0.0.0', port=5000, debug=False)
```

#### 8. Set Up SSL with Let's Encrypt (Free HTTPS)

```bash
# Install Certbot
sudo yum install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d script.neillanda.com

# Auto-renewal (already set up by certbot)
```

---

## Domain Setup: script.neillanda.com

### Step 1: Get Your Server IP/URL

**If using Elastic Beanstalk:**
- Get the EB URL from `eb status`

**If using EC2:**
- Get the Elastic IP (recommended) or Public IP
- Go to EC2 → Elastic IPs → Allocate Elastic IP
- Associate it with your instance

### Step 2: Configure DNS

**If using Route 53:**
1. Go to Route 53 → Hosted Zones
2. Select `neillanda.com`
3. Create Record:
   - **Name:** `script`
   - **Type:** `CNAME` (for EB) or `A` (for EC2 with Elastic IP)
   - **Value:** 
     - EB: `link-downloader-env.eba-xxxxx.us-east-1.elasticbeanstalk.com`
     - EC2: Your Elastic IP address
   - **TTL:** 300

**If using another DNS provider:**
1. Log into your DNS provider
2. Add CNAME record:
   - **Name:** `script`
   - **Target:** Your EB URL or EC2 Elastic IP
   - **TTL:** 300

### Step 3: Wait for Propagation

DNS changes take 5 minutes to 48 hours (usually 5-30 minutes).

Test with:
```bash
nslookup script.neillanda.com
```

---

## What Goes in S3? (Optional - For Static Assets)

You **don't need S3** for this app, but you can use it for:

### Option: Serve Static Files from S3 + CloudFront

**Benefits:**
- Faster loading (CDN)
- Reduces server load
- Cheaper for high traffic

**Steps:**

1. **Create S3 Bucket:**
   - Name: `script-neillanda-static`
   - Enable static website hosting
   - Set bucket policy for public read

2. **Upload Static Files:**
   ```bash
   aws s3 sync css/ s3://script-neillanda-static/css/
   aws s3 sync js/ s3://script-neillanda-static/js/
   aws s3 sync img/ s3://script-neillanda-static/img/
   ```

3. **Update HTML to Use S3 URLs:**
   ```html
   <link rel="stylesheet" href="https://script-neillanda-static.s3.amazonaws.com/css/style.css">
   ```

4. **Set Up CloudFront** (Optional, for CDN):
   - Create CloudFront distribution
   - Point to S3 bucket
   - Use CloudFront URL in HTML

**Note:** For simplicity, you can skip S3 and serve everything from your Flask app.

---

## Security Considerations

### 1. Security Groups

**EC2 Security Group Rules:**
- SSH (22): Only from your IP
- HTTP (80): From anywhere (0.0.0.0/0)
- HTTPS (443): From anywhere
- Custom (5000): Only from localhost (127.0.0.1) - for Nginx

### 2. Environment Variables

Don't hardcode secrets! Use environment variables:

```bash
# On EC2:
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
```

Or create `.env` file (don't commit to git!):
```
FLASK_ENV=production
SECRET_KEY=your-secret-key
```

### 3. Firewall (Optional)

```bash
# Configure firewall
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. Rate Limiting (Important!)

Add rate limiting to prevent abuse:

**Install:**
```bash
pip install Flask-Limiter
```

**In app.py:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["10 per minute", "100 per hour"]
)

@app.route('/download', methods=['POST'])
@limiter.limit("5 per minute")  # Max 5 downloads per minute per IP
def download():
    # ... existing code
```

---

## Cost Estimation

### EC2 (t2.micro - Free Tier)
- **First 12 months:** FREE (750 hours/month)
- **After free tier:** ~$8-10/month
- **Data transfer:** First 1GB free, then $0.09/GB

### Elastic Beanstalk
- **EC2 instance:** Same as above
- **Load balancer:** ~$16/month (if not free tier)
- **Storage:** ~$0.10/GB/month

### S3 (if used)
- **Storage:** $0.023/GB/month (first 5GB free)
- **Requests:** $0.005 per 1,000 requests

### Route 53
- **Hosted zone:** $0.50/month
- **Queries:** $0.40 per million

**Estimated Total:** $10-30/month (after free tier)

---

## Monitoring and Logs

### View Application Logs

**EC2:**
```bash
# View Flask logs
sudo journalctl -u link-downloader -f

# View Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

**Elastic Beanstalk:**
```bash
eb logs
```

### Set Up CloudWatch Alarms

1. Go to CloudWatch → Alarms
2. Create alarm for:
   - High CPU usage
   - High memory usage
   - Application errors

---

## Troubleshooting

### App Not Starting

```bash
# Check service status
sudo systemctl status link-downloader

# Check logs
sudo journalctl -u link-downloader -n 50

# Test manually
cd /home/ec2-user/link-downloader
python3.11 app.py
```

### Can't Connect to Domain

1. Check DNS propagation: `nslookup script.neillanda.com`
2. Check security groups (ports 80/443 open)
3. Check Nginx: `sudo systemctl status nginx`
4. Check Nginx config: `sudo nginx -t`

### Downloads Failing

1. Check yt-dlp installation: `yt-dlp --version`
2. Check disk space: `df -h`
3. Check permissions: `ls -la downloads/`
4. Test yt-dlp manually: `yt-dlp --help`

### High Costs

1. Check data transfer (downloads use bandwidth)
2. Consider CloudFront for caching
3. Set up billing alerts in AWS

---

## Quick Start Checklist

### For EC2:
- [ ] Launch EC2 instance
- [ ] Configure security group
- [ ] Connect via SSH
- [ ] Install Python, yt-dlp, dependencies
- [ ] Upload application files
- [ ] Install and configure Nginx
- [ ] Set up systemd service
- [ ] Configure SSL (Let's Encrypt)
- [ ] Set up DNS (CNAME/A record)
- [ ] Test the application
- [ ] Set up monitoring

### For Elastic Beanstalk:
- [ ] Install EB CLI
- [ ] Prepare application files
- [ ] Run `eb init`
- [ ] Run `eb create`
- [ ] Configure DNS
- [ ] Test the application

---

## Next Steps After Deployment

1. **Set up automated backups** (for downloads folder)
2. **Configure CloudWatch monitoring**
3. **Set up email alerts** for errors
4. **Implement rate limiting**
5. **Add analytics** (optional)
6. **Set up CI/CD** for easy updates (GitHub Actions)

---

## Recommended Architecture

```
User → Route 53 (DNS) → CloudFront (CDN, optional) → 
Application Load Balancer (EB) or Nginx (EC2) → 
Flask App (EC2/EB) → yt-dlp → Downloads → ZIP → User
```

For your use case, start simple:
```
User → Route 53 → EC2 (Nginx + Flask) → yt-dlp → User
```

---

This guide should get you deployed! Start with EC2 if you want to learn, or Elastic Beanstalk if you want it working quickly.

