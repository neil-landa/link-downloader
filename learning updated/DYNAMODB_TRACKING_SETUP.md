# DynamoDB Visitor Tracking Setup Guide

This guide explains how to set up DynamoDB tracking for visitor analytics and download monitoring.

## Overview

The tracking system records:

- **User visits**: Each download session
- **Song titles**: Extracted from downloaded filenames
- **Timestamps**: When downloads occurred
- **Public IP**: Client IP address
- **Number of songs**: Count of downloaded files
- **Links**: All submitted URLs
- **User agent**: Browser/client information
- **Errors**: Any download failures

## DynamoDB Table Schema

### Table Structure

- **Table Name**: `link-downloader-visits` (configurable via `DYNAMODB_TABLE_NAME`)
- **Partition Key**: `date` (String, format: YYYY-MM-DD)
- **Sort Key**: `timestamp` (String, ISO format)

### Item Attributes

```json
{
  "date": "2025-01-15", // Partition key
  "timestamp": "2025-01-15T14:30:00.123456+00:00", // Sort key
  "session_id": "1705327800-a1b2c3d4",
  "client_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "num_links_submitted": 5,
  "num_files_downloaded": 4,
  "links": [
    "https://youtube.com/watch?v=abc123",
    "https://soundcloud.com/track/xyz"
  ],
  "titles": ["Song Title 1", "Song Title 2"],
  "filenames": ["Song Title 1.m4a", "Song Title 2.m4a"],
  "has_errors": false,
  "error_count": 0
}
```

## Setup Instructions

### 1. Install Dependencies

Add to `requirements.txt`:

```
boto3>=1.28.0
```

Then install:

```bash
pip install boto3
```

### 2. Configure AWS Credentials

You have two options:

#### Option A: AWS Credentials File (Recommended)

```bash
aws configure
```

This creates `~/.aws/credentials`:

```ini
[default]
aws_access_key_id = YOUR_ACCESS_KEY
aws_secret_access_key = YOUR_SECRET_KEY
region = us-east-1
```

#### Option B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Set Environment Variables

Add to your `.env` file or environment:

```bash
# DynamoDB Configuration
DYNAMODB_TABLE_NAME=link-downloader-visits
AWS_REGION=us-east-1
```

### 4. Create DynamoDB Table

#### Option A: Automatic (via Python)

```python
from dynamodb_tracker import create_dynamodb_table_if_not_exists
create_dynamodb_table_if_not_exists()
```

#### Option B: AWS CLI

```bash
aws dynamodb create-table \
    --table-name link-downloader-visits \
    --attribute-definitions \
        AttributeName=date,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=date,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

#### Option C: AWS Console

1. Go to AWS DynamoDB Console
2. Click "Create table"
3. Table name: `link-downloader-visits`
4. Partition key: `date` (String)
5. Sort key: `timestamp` (String)
6. Settings: Use default or customize
7. Create table

### 5. Verify Setup

The tracking system will automatically:

- ✅ Work if DynamoDB is configured (no errors)
- ✅ Fail gracefully if not configured (downloads still work)
- ✅ Log warnings if DynamoDB is unavailable

Check logs for:

- `"Saved visit record to DynamoDB: <session_id>"` - Success
- `"DynamoDB not available"` - Not configured (non-critical)

## Querying Data

### Query by Date

```python
from dynamodb_tracker import query_visits_by_date

# Get all visits for a specific date
visits = query_visits_by_date('2025-01-15', limit=100)

for visit in visits:
    print(f"IP: {visit['client_ip']}")
    print(f"Time: {visit['timestamp']}")
    print(f"Downloaded: {visit['num_files_downloaded']} files")
    print(f"Titles: {visit.get('titles', [])}")
```

### Query via AWS CLI

```bash
# Get visits for a specific date
aws dynamodb query \
    --table-name link-downloader-visits \
    --key-condition-expression "date = :date" \
    --expression-attribute-values '{":date":{"S":"2025-01-15"}}' \
    --scan-index-forward false
```

### Query via AWS Console

1. Go to DynamoDB Console
2. Select `link-downloader-visits` table
3. Click "Explore table items"
4. Filter by `date` attribute

## Cost Considerations

### DynamoDB Pricing (On-Demand)

- **Write**: $1.25 per million write units
- **Read**: $0.25 per million read units
- **Storage**: $0.25 per GB-month

### Estimated Costs

For a typical usage:

- **100 downloads/day** = ~100 write units/day
- **Monthly writes**: ~3,000 = **$0.004/month**
- **Storage**: ~1KB per record = 100 records = 0.1MB = **$0.000025/month**

**Total: ~$0.01/month for 100 downloads/day**

### Cost Optimization Tips

1. Use **On-Demand** billing (no capacity planning needed)
2. Set up **TTL** to auto-delete old records (optional)
3. Use **CloudWatch** to monitor costs
4. Consider archiving old data to S3

## Advanced Features

### Add TTL (Time To Live)

To auto-delete records after 90 days:

1. Add TTL attribute to table:

```python
# In dynamodb_tracker.py, modify create_visit_record:
record['ttl'] = int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())
```

2. Enable TTL on table:

```bash
aws dynamodb update-time-to-live \
    --table-name link-downloader-visits \
    --time-to-live-specification Enabled=true,AttributeName=ttl
```

### Create Analytics Dashboard

Use AWS services:

- **AWS Athena**: Query DynamoDB data
- **QuickSight**: Create visualizations
- **CloudWatch**: Monitor metrics

### Export Data

```python
from dynamodb_tracker import query_visits_by_date
import json

visits = query_visits_by_date('2025-01-15', limit=1000)
with open('visits_2025-01-15.json', 'w') as f:
    json.dump(visits, f, indent=2, default=str)
```

## Privacy Considerations

### Data Collected

- IP addresses (may be considered PII)
- User agents
- URLs submitted
- Download timestamps

### Recommendations

1. **Anonymize IPs**: Hash or truncate IP addresses
2. **Add Privacy Policy**: Inform users about data collection
3. **GDPR Compliance**: Consider data retention policies
4. **Opt-out Option**: Allow users to disable tracking

### Example: Anonymize IPs

```python
import hashlib

def anonymize_ip(ip):
    """Hash IP address for privacy"""
    return hashlib.sha256(ip.encode()).hexdigest()[:16]
```

## Troubleshooting

### "DynamoDB not available" Warning

- Check AWS credentials are configured
- Verify table exists
- Check IAM permissions

### "Access Denied" Error

Required IAM permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem"],
      "Resource": "arn:aws:dynamodb:REGION:ACCOUNT:table/link-downloader-visits"
    }
  ]
}
```

### Tracking Not Working

1. Check logs for errors
2. Verify `DYNAMODB_AVAILABLE` is `True`
3. Test with a simple query
4. Check AWS CloudWatch for DynamoDB errors

## Example Queries

### Most Popular Songs

```python
from collections import Counter

visits = query_visits_by_date('2025-01-15', limit=1000)
all_titles = []
for visit in visits:
    all_titles.extend(visit.get('titles', []))

popular = Counter(all_titles).most_common(10)
print("Top 10 downloaded songs:")
for title, count in popular:
    print(f"  {title}: {count}")
```

### Unique Visitors

```python
visits = query_visits_by_date('2025-01-15', limit=1000)
unique_ips = set(visit['client_ip'] for visit in visits)
print(f"Unique visitors: {len(unique_ips)}")
```

### Download Success Rate

```python
visits = query_visits_by_date('2025-01-15', limit=1000)
total = len(visits)
successful = sum(1 for v in visits if not v.get('has_errors', False))
print(f"Success rate: {successful/total*100:.1f}%")
```
