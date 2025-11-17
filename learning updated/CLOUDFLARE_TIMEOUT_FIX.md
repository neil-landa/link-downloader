# Fixing Cloudflare 524 Timeout Errors

## The Problem

Cloudflare has a default timeout of **100 seconds** for free plans. YouTube downloads can take longer, causing 524 errors.

## Solution Options

### Option 1: Increase Cloudflare Timeout (If Available)

**For Free Plan:** Maximum is 100 seconds (may not be enough)

**For Pro Plan ($20/month):** Can increase to 600 seconds

1. Go to Cloudflare Dashboard
2. Select your domain
3. Go to **Rules** → **Page Rules** (or **Transform Rules**)
4. Create a new rule:
   - **URL Pattern:** `*script.neillanda.com/download*`
   - **Settings:**
     - **Origin Timeout:** Increase to 600 seconds (if on Pro plan)

### Option 2: Bypass Cloudflare for Downloads (Recommended - Free)

Create a subdomain that bypasses Cloudflare for the download endpoint:

1. **In Cloudflare DNS:**
   - Add a new **A record**:
     - **Name:** `direct` (or `dl`, `download`)
     - **IP:** Your server's IP address
     - **Proxy status:** **DNS only** (gray cloud, not orange)
2. **Update your JavaScript** to use the direct subdomain for downloads:

   ```javascript
   // Use direct subdomain to bypass Cloudflare
   const downloadUrl = window.location.hostname.includes("script.neillanda.com")
     ? "https://direct.neillanda.com/download"
     : "/download";
   ```

3. **Update nginx** to accept requests from the direct subdomain (add to your nginx config)

### Option 3: Make Downloads Async with Polling (Best UX)

Instead of waiting for the download, start it in the background and poll for completion:

1. **Backend:** Start download async, return job ID immediately
2. **Frontend:** Poll for status, download when ready
3. **Benefits:** No timeout issues, better UX with progress

### Option 4: Use Server-Sent Events (SSE) for Progress

Stream progress updates to the client without waiting for completion.

## Quick Fix: Bypass Cloudflare for /download

The easiest solution is Option 2 - create a direct subdomain:

1. **Add DNS record in Cloudflare:**

   ```
   Type: A
   Name: direct
   Content: [Your server IP]
   Proxy: OFF (gray cloud)
   ```

2. **Update nginx** to handle both domains (already configured if using server_name)

3. **Update JavaScript** (see code below)

## Recommended: Update JavaScript to Use Direct Subdomain

Update `js/script.js` to use direct connection for downloads:

```javascript
// In the fetch call, change:
const response = await fetch("/download", {
  method: "POST",
  body: formData,
});

// To:
const downloadEndpoint =
  window.location.hostname === "script.neillanda.com"
    ? "https://direct.neillanda.com/download" // Bypass Cloudflare
    : "/download"; // Local development

const response = await fetch(downloadEndpoint, {
  method: "POST",
  body: formData,
});
```

This way:

- Main site stays behind Cloudflare (for DDoS protection, caching, etc.)
- Downloads bypass Cloudflare (no timeout issues)
- Free solution, works on any Cloudflare plan
