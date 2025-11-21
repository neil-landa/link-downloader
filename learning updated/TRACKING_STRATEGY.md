# DynamoDB Tracking Strategy

## Overview

This document outlines the strategy for tracking visitor usage and downloads using DynamoDB.

## Design Decisions

### 1. Table Structure

**Partition Key: `date` (YYYY-MM-DD)**
- Allows efficient querying by date
- Natural partitioning for time-based data
- Easy to query "all visits today" or "all visits this week"

**Sort Key: `timestamp` (ISO format)**
- Chronological ordering within each date
- Enables time-range queries within a day
- Most recent first (ScanIndexForward=False)

### 2. Data Collected

For each download session, we track:

| Field | Description | Example |
|-------|-------------|---------|
| `session_id` | Unique identifier | `1705327800-a1b2c3d4` |
| `timestamp` | When download occurred | `2025-01-15T14:30:00+00:00` |
| `date` | Date partition | `2025-01-15` |
| `client_ip` | User's public IP | `192.168.1.100` |
| `user_agent` | Browser/client info | `Mozilla/5.0...` |
| `num_links_submitted` | How many URLs submitted | `5` |
| `num_files_downloaded` | How many files downloaded | `4` |
| `links` | List of submitted URLs | `["https://youtube.com/..."]` |
| `titles` | Extracted song titles | `["Song Title 1", "Song Title 2"]` |
| `filenames` | Actual filenames | `["Song Title 1.m4a"]` |
| `has_errors` | Whether errors occurred | `false` |
| `error_count` | Number of errors | `0` |

### 3. Why DynamoDB?

**Advantages:**
- ✅ Serverless - no infrastructure to manage
- ✅ Auto-scaling - handles traffic spikes automatically
- ✅ Low cost for small-medium usage (~$0.01/month for 100 downloads/day)
- ✅ Fast queries by date
- ✅ No SQL needed - simple key-value queries
- ✅ Built-in AWS integration

**Alternatives Considered:**
- ❌ SQL Database (PostgreSQL/MySQL): Requires server management
- ❌ MongoDB: More complex setup, similar cost
- ❌ Simple file logging: Hard to query, not scalable
- ❌ CloudWatch Logs: More expensive, harder to query structured data

### 4. Query Patterns

**Primary Queries:**
1. **By Date**: Get all visits for a specific date
   ```python
   query_visits_by_date('2025-01-15')
   ```

2. **Time Range**: Query within a date (using sort key)
   ```python
   # Get visits after 2pm on 2025-01-15
   table.query(
       KeyConditionExpression='date = :date AND timestamp > :time',
       ...
   )
   ```

3. **Analytics**: Aggregate across dates
   - Most popular songs
   - Unique visitors
   - Success rates
   - Peak usage times

### 5. Performance Considerations

**Write Performance:**
- Writes are asynchronous (non-blocking)
- Uses background thread to avoid slowing downloads
- Errors in tracking don't affect user experience

**Read Performance:**
- Queries by date are fast (single partition)
- Limit results to prevent large scans
- Use pagination for large result sets

**Cost Optimization:**
- On-demand billing (pay per use)
- TTL for auto-deleting old records (optional)
- Archive old data to S3 if needed

### 6. Privacy & Compliance

**Data Privacy:**
- IP addresses are collected (may be PII)
- Consider hashing/truncating IPs for privacy
- Add privacy policy to inform users
- Consider GDPR compliance if serving EU users

**Recommendations:**
1. Add privacy policy page
2. Optionally anonymize IPs
3. Set TTL to auto-delete old records
4. Allow opt-out if required by law

### 7. Integration Points

**In `app.py`:**
- Integrated into `/download` route
- Runs after successful downloads
- Extracts filenames and titles
- Captures IP and user agent
- Tracks errors

**Error Handling:**
- Tracking failures are non-critical
- Downloads work even if DynamoDB is down
- Errors are logged but don't break functionality

### 8. Future Enhancements

**Possible Additions:**
1. **Real-time Dashboard**: WebSocket updates
2. **Analytics API**: REST endpoint for stats
3. **Export Functionality**: CSV/JSON export
4. **Alerts**: Notify on unusual activity
5. **Geolocation**: Map IPs to locations
6. **User Sessions**: Track returning visitors
7. **Rate Limiting**: Use tracking data for abuse detection

## Usage Examples

### View Today's Visits
```bash
python query_visits.py --date 2025-01-15
```

### Get Statistics
```bash
python query_visits.py --date 2025-01-15 --stats
```

### Export as JSON
```bash
python query_visits.py --date 2025-01-15 --json > visits.json
```

### Query via Python
```python
from dynamodb_tracker import query_visits_by_date

visits = query_visits_by_date('2025-01-15', limit=100)
for visit in visits:
    print(f"{visit['client_ip']}: {visit['num_files_downloaded']} files")
```

## Cost Estimate

For **100 downloads/day**:
- Writes: 100/day × 30 = 3,000/month = **$0.004/month**
- Reads: Minimal (only when querying) = **~$0.001/month**
- Storage: ~1KB/record × 3,000 = 3MB = **$0.00075/month**

**Total: ~$0.01/month** (practically free)

## Setup Checklist

- [ ] Install boto3: `pip install boto3`
- [ ] Configure AWS credentials
- [ ] Set environment variables
- [ ] Create DynamoDB table
- [ ] Test with a download
- [ ] Verify data in DynamoDB console
- [ ] Set up query script
- [ ] (Optional) Add TTL for auto-cleanup
- [ ] (Optional) Set up CloudWatch monitoring

## Monitoring

**Key Metrics to Watch:**
1. Write requests (should match download count)
2. Read requests (when querying)
3. Storage size (grows over time)
4. Error rate (should be near zero)
5. Cost (should be minimal)

**CloudWatch Alarms:**
- Set up billing alerts
- Monitor error rates
- Track table size

