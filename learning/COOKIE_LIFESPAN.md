# Cookie Lifespan and Usage Guide

## How Long Do Cookies Last?

### Typical Lifespan

- **2-4 weeks** on average
- Some cookies may last longer (up to 6 months)
- Some may expire sooner (1-2 weeks)

### It's NOT About Number of Uses

Cookies don't have a "download limit" - they're time-based, not usage-based. You can use them for:

- 1 download or 1000 downloads
- As long as they haven't expired

## When Cookies Fail

### Time-Based Expiration

- Cookies naturally expire after 2-4 weeks
- YouTube invalidates old sessions
- **Solution:** Refresh cookies every 2-3 weeks

### Activity-Based Issues

YouTube may invalidate cookies if:

- **Too many rapid requests** (rate limiting)
- **Suspicious patterns** detected
- **Account security changes** (password change, 2FA enabled)
- **Geographic changes** (if your IP location changes significantly)

### Signs Cookies Are Expired

- Error: "Sign in to confirm you're not a bot"
- Error: "Use --cookies-from-browser or --cookies"
- Downloads start failing after working fine
- All downloads fail with authentication errors

## How to Check If Cookies Are Still Valid

### Quick Test on Server

```bash
# Test if cookies work:
yt-dlp --cookies /home/ubuntu/www/link-downloader/cookies.txt \
  --list-formats https://www.youtube.com/watch?v=dQw4w9WgXcQ

# If it works: Cookies are valid ✓
# If you get "Sign in to confirm": Cookies are expired ✗
```

### Check Cookie File Age

```bash
# On server:
ls -lh /home/ubuntu/www/link-downloader/cookies.txt
# Check the date - if older than 2-3 weeks, refresh them
```

## Best Practices

### 1. Refresh Regularly

- **Weekly:** If you use it frequently
- **Every 2-3 weeks:** For normal use
- **When errors start:** Refresh immediately

### 2. Monitor for Errors

Watch your server logs:

```bash
sudo journalctl -u link-downloader -f | grep -i cookie
```

### 3. Set Up Automated Refresh

Use the `refresh-cookies-local.sh` script with a cron job to refresh weekly automatically.

### 4. Keep Backup

Before refreshing, backup old cookies (in case new ones don't work):

```bash
cp cookies.txt cookies.txt.backup
```

## How to Refresh Cookies

### Quick Method (Local Machine)

1. Make sure you're logged into YouTube in your browser
2. Use browser extension to export cookies
3. Upload to server:
   ```bash
   scp cookies.txt ubuntu@your-server:/home/ubuntu/www/link-downloader/
   ```
4. Restart service:
   ```bash
   sudo systemctl restart link-downloader
   ```

### Automated Method

Set up `refresh-cookies-local.sh` to run weekly via cron (see `COOKIES_SETUP.md`)

## Troubleshooting

### "Cookies may be expired" Error

1. Export fresh cookies from browser
2. Upload to server
3. Restart Flask service
4. Test again

### Cookies Work Sometimes But Not Always

- May be rate limiting from YouTube
- Try spacing out downloads
- Consider implementing rate limiting in Flask

### Cookies Work for Some Videos But Not Others

- Some videos may have additional restrictions
- Age-restricted or region-locked content may need different handling
- This is normal YouTube behavior

## Expected Behavior

### Normal Usage

- **Fresh cookies:** Should work for 2-4 weeks
- **After 2 weeks:** May start failing occasionally
- **After 3-4 weeks:** Will likely fail consistently
- **Solution:** Refresh cookies

### High Usage

- **Many downloads quickly:** May trigger YouTube rate limiting
- **Solution:** Add delays between downloads or implement rate limiting

## Summary

- **Lifespan:** 2-4 weeks (time-based, not usage-based)
- **Refresh when:** Errors start appearing or every 2-3 weeks
- **No download limit:** Use as many times as you want while valid
- **Monitor:** Watch for "Sign in to confirm" errors
- **Automate:** Set up weekly refresh script

The key is: **Refresh cookies every 2-3 weeks, or when you see authentication errors.**
