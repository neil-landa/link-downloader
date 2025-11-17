# Quick Deployment Reference

## TL;DR - Fastest Path to Deployment

### Option 1: Elastic Beanstalk (Easiest - 15 minutes)

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize
eb init -p python-3.11 link-downloader --region us-east-1

# 3. Create and deploy
eb create link-downloader-env

# 4. Get URL
eb status

# 5. Point DNS: script.neillanda.com → [EB URL from step 4]
```

### Option 2: EC2 (More Control - 30 minutes)

1. **Launch EC2:**
   - Amazon Linux 2023
   - t2.micro (free tier)
   - Security group: HTTP (80), HTTPS (443), SSH (22 from your IP)

2. **Connect:**
   ```bash
   ssh -i "your-key.pem" ec2-user@your-instance-ip
   ```

3. **Run deployment script:**
   ```bash
   # Upload files first (use SCP or Git)
   chmod +x deploy.sh
   ./deploy.sh
   ```

4. **Set up SSL:**
   ```bash
   sudo certbot --nginx -d script.neillanda.com
   ```

5. **Point DNS:**
   - CNAME or A record: `script` → [Your EC2 Elastic IP]

---

## What Goes Where?

### ❌ NOT in S3:
- Flask app (needs a server)
- Python code
- Dynamic content

### ✅ CAN go in S3 (optional):
- Static CSS/JS/images (for CDN)
- But you can serve from Flask too

### ✅ MUST go on server:
- `app.py` (Flask application)
- `requirements.txt` (dependencies)
- All Python code
- yt-dlp (installed on server)

---

## DNS Setup

### Route 53 (if using AWS DNS):
1. Route 53 → Hosted Zones → neillanda.com
2. Create Record:
   - Name: `script`
   - Type: `CNAME` (EB) or `A` (EC2)
   - Value: Your server URL/IP

### Other DNS Provider:
1. Add CNAME record:
   - Name: `script`
   - Target: Your server URL/IP

---

## Cost Breakdown

- **EC2 t2.micro:** FREE (first year), then ~$8/month
- **Elastic Beanstalk:** Same as EC2 + ~$16/month for load balancer
- **Route 53:** $0.50/month + $0.40 per million queries
- **Data Transfer:** First 1GB free, then $0.09/GB

**Total:** ~$10-30/month after free tier

---

## Common Issues

### "Connection refused"
- Check security groups (ports 80/443 open)
- Check if app is running: `sudo systemctl status link-downloader`

### "yt-dlp not found"
- Install: `pip3.11 install yt-dlp`
- Check PATH: `which yt-dlp`

### DNS not working
- Wait 5-30 minutes for propagation
- Check: `nslookup script.neillanda.com`
- Verify DNS record is correct

### Downloads timeout
- Increase Nginx timeouts (already in config)
- Check disk space: `df -h`
- Check logs: `sudo journalctl -u link-downloader -f`

---

## Security Checklist

- [ ] Security group: Only SSH from your IP
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Flask debug mode OFF in production
- [ ] Rate limiting enabled (add Flask-Limiter)
- [ ] Regular security updates: `sudo yum update -y`
- [ ] Firewall configured (optional)

---

## After Deployment

1. **Test the site:** Visit `https://script.neillanda.com`
2. **Monitor logs:** `sudo journalctl -u link-downloader -f`
3. **Set up CloudWatch alarms** (optional)
4. **Configure backups** (optional)
5. **Set up billing alerts** in AWS

---

## Updating Your App

### EC2:
```bash
# SSH into server
ssh -i "key.pem" ec2-user@your-ip

# Pull updates (if using Git)
cd link-downloader
git pull

# Restart service
sudo systemctl restart link-downloader
```

### Elastic Beanstalk:
```bash
# Make changes locally
# Then deploy
eb deploy
```

---

## Need Help?

1. Check logs first
2. Verify security groups
3. Test components individually (yt-dlp, Flask, Nginx)
4. Check AWS documentation
5. AWS Support (if on paid plan)

