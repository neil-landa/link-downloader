#!/usr/bin/env python3
"""
Query DynamoDB visit records

Usage:
    python query_visits.py --date 2025-01-15
    python query_visits.py --date 2025-01-15 --limit 50
    python query_visits.py --stats
"""

import argparse
import json
from datetime import datetime, timedelta
from collections import Counter
from dynamodb_tracker import query_visits_by_date, DYNAMODB_AVAILABLE


def format_timestamp(iso_str):
    """Format ISO timestamp to readable format"""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return iso_str


def print_visit(visit):
    """Print a single visit record"""
    print(f"\n{'='*60}")
    print(f"Session ID: {visit.get('session_id', 'N/A')}")
    print(f"Timestamp: {format_timestamp(visit.get('timestamp', ''))}")
    print(f"IP Address: {visit.get('client_ip', 'N/A')}")
    print(f"User Agent: {visit.get('user_agent', 'N/A')[:50]}...")
    print(f"\nSubmitted: {visit.get('num_links_submitted', 0)} links")
    print(f"Downloaded: {visit.get('num_files_downloaded', 0)} files")
    
    if visit.get('has_errors'):
        print(f"⚠️  Errors: {visit.get('error_count', 0)}")
    
    if visit.get('links'):
        print(f"\nLinks:")
        for i, link in enumerate(visit['links'][:5], 1):
            print(f"  {i}. {link}")
        if len(visit['links']) > 5:
            print(f"  ... and {len(visit['links']) - 5} more")
    
    if visit.get('titles'):
        print(f"\nDownloaded Titles:")
        for i, title in enumerate(visit['titles'][:10], 1):
            print(f"  {i}. {title}")
        if len(visit['titles']) > 10:
            print(f"  ... and {len(visit['titles']) - 10} more")


def print_statistics(visits):
    """Print aggregated statistics"""
    if not visits:
        print("No visits found")
        return
    
    total_visits = len(visits)
    total_downloads = sum(v.get('num_files_downloaded', 0) for v in visits)
    total_links = sum(v.get('num_links_submitted', 0) for v in visits)
    unique_ips = len(set(v.get('client_ip', '') for v in visits))
    successful = sum(1 for v in visits if not v.get('has_errors', False))
    
    print(f"\n{'='*60}")
    print("STATISTICS")
    print(f"{'='*60}")
    print(f"Total Visits: {total_visits}")
    print(f"Unique IPs: {unique_ips}")
    print(f"Total Downloads: {total_downloads}")
    print(f"Total Links Submitted: {total_links}")
    print(f"Successful Downloads: {successful}")
    print(f"Failed Downloads: {total_visits - successful}")
    if total_visits > 0:
        print(f"Success Rate: {successful/total_visits*100:.1f}%")
    
    # Most popular titles
    all_titles = []
    for visit in visits:
        all_titles.extend(visit.get('titles', []))
    
    if all_titles:
        print(f"\nTop 10 Downloaded Songs:")
        popular = Counter(all_titles).most_common(10)
        for i, (title, count) in enumerate(popular, 1):
            print(f"  {i}. {title} ({count} downloads)")


def main():
    parser = argparse.ArgumentParser(description='Query DynamoDB visit records')
    parser.add_argument('--date', type=str, help='Date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of results (default: 100)')
    parser.add_argument('--stats', action='store_true', help='Show statistics instead of individual records')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    
    args = parser.parse_args()
    
    if not DYNAMODB_AVAILABLE:
        print("ERROR: DynamoDB not available. Check your AWS configuration.")
        return
    
    # Default to today if no date specified
    if not args.date:
        args.date = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Querying visits for date: {args.date}")
    visits = query_visits_by_date(args.date, limit=args.limit)
    
    if not visits:
        print(f"No visits found for {args.date}")
        return
    
    if args.json:
        # Output as JSON
        print(json.dumps(visits, indent=2, default=str))
    elif args.stats:
        # Show statistics
        print_statistics(visits)
    else:
        # Show individual records
        print(f"\nFound {len(visits)} visits\n")
        for visit in visits:
            print_visit(visit)
        
        # Show summary at end
        print(f"\n{'='*60}")
        print(f"Total: {len(visits)} visits")
        print(f"{'='*60}")


if __name__ == '__main__':
    main()

