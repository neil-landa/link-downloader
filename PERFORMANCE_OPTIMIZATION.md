# Performance Optimization Guide

## Current Settings (Optimized for 1GB RAM)

### yt-dlp Settings

- **Buffer Size:** `64K` (increased from 16K)
  - Larger buffer = fewer system calls = faster downloads
  - Uses ~64KB RAM per download (safe for 1GB RAM)
- **Rate Limit:** Removed (was 1M)
  - No artificial speed cap
  - Uses full available bandwidth
  - Your EC2 instance network speed is the limit, not the code

### Why These Settings?

**For 1GB RAM:**

- `64K` buffer is optimal balance (not too small, not too large)
- Removing rate limit lets downloads use full bandwidth
- With 494Mi available RAM, you have plenty of headroom

**If you had more RAM (2GB+):**

- Could increase buffer to `128K` or `256K`
- Could add `--concurrent-fragments 4` for parallel downloads

---

## Server Optimizations

### 1. Swap Space (Critical!)

Your server has **0B swap** - this is dangerous for 1GB RAM!

**Why swap matters:**

- When RAM fills up, system uses swap (disk space as RAM)
- Without swap, system will kill processes (OOM killer)
- Can cause downloads to fail mid-way

**Solution:** Run `optimize-server.sh` to add 2GB swap

```bash
chmod +x optimize-server.sh
./optimize-server.sh
```

### 2. System Tuning

The optimization script also:

- Sets `swappiness=10` (less aggressive swap usage)
- Optimizes cache pressure
- Updates packages

---

## Performance Comparison

### Before Optimization

- Buffer: 16K (small, many system calls)
- Rate limit: 1M (artificially slow)
- Swap: 0B (risky, OOM kills possible)
- **Result:** Slow downloads, potential crashes

### After Optimization

- Buffer: 64K (efficient, fewer system calls)
- Rate limit: None (full bandwidth)
- Swap: 2GB (safety net)
- **Result:** Faster downloads, more stable

---

## Expected Performance

### Network Speed Limits

Your EC2 instance network speed depends on instance type:

- **t2.micro/t3.micro:** ~1 Gbps (up to 125 MB/s)
- **t2.small/t3.small:** ~Up to 5 Gbps
- **t2.medium/t3.medium:** ~Up to 5 Gbps

**Real-world speeds:**

- With 1M limit: ~125 KB/s (very slow)
- Without limit: Depends on YouTube's server, typically 5-20 MB/s for audio

### Download Time Estimates

**Audio file (5-10 MB typical):**

- Before (1M limit): ~40-80 seconds
- After (no limit): ~1-3 seconds

**Multiple files:**

- Downloads happen sequentially (one at a time)
- Each file benefits from full speed

---

## Advanced Optimizations (If You Upgrade RAM)

### For 2GB+ RAM

You could add these to `app.py`:

```python
common_opts = [
    '--buffer-size', '128K',  # Larger buffer
    '--concurrent-fragments', '4',  # Download fragments in parallel
    # ... rest of options
]
```

**Warning:** `--concurrent-fragments` uses more RAM. Only use if you have 2GB+ RAM.

---

## Monitoring Performance

### Check Memory Usage

```bash
free -h
```

### Check Swap Usage

```bash
swapon --show
```

### Monitor During Download

```bash
# Watch memory in real-time
watch -n 1 free -h

# Check if swap is being used
watch -n 1 'swapon --show'
```

### Check Download Speed

Look at Flask logs during download - yt-dlp shows speed:

```
[download] 45.2% of 8.5MiB at 12.3MiB/s ETA 00:00:03
```

---

## Troubleshooting

### "Out of Memory" Errors

**Symptoms:**

- Downloads fail randomly
- System becomes unresponsive
- Process killed messages

**Solution:**

1. Add swap space (run `optimize-server.sh`)
2. Reduce buffer size back to 32K if needed
3. Consider upgrading to t2.small (2GB RAM)

### Downloads Still Slow

**Possible causes:**

1. **Network:** Check EC2 instance type (t2.micro has burstable network)
2. **YouTube throttling:** YouTube may limit speed (cookies help)
3. **Server load:** Other processes using CPU/RAM

**Check:**

```bash
# CPU usage
top

# Network speed
iftop  # (install: sudo apt install iftop)

# Disk I/O
iostat -x 1
```

### High Swap Usage

If swap is constantly being used:

- System is under memory pressure
- Consider upgrading RAM
- Or reduce buffer size to 32K

---

## Cost vs Performance

### Current Setup (t2.micro - 1GB RAM)

- **Cost:** Free tier or ~$8/month
- **Performance:** Good for audio downloads
- **Limitation:** Can't handle many concurrent downloads

### Upgrade Option (t2.small - 2GB RAM)

- **Cost:** ~$15/month
- **Performance:** Better, can handle more load
- **Benefit:** More headroom, less swap usage

---

## Summary

**What we optimized:**

1. ✅ Increased buffer from 16K → 64K
2. ✅ Removed 1M rate limit
3. ✅ Added swap space (run optimize-server.sh)
4. ✅ System tuning for low RAM

**Expected improvement:**

- **10-20x faster downloads** (removing 1M limit)
- **More stable** (swap prevents OOM kills)
- **Better efficiency** (larger buffer)

**Next steps:**

1. Run `optimize-server.sh` on your server
2. Test a download and check speed
3. Monitor memory usage during downloads
