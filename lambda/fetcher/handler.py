"""
GoldSport Scheduler - Fetcher Lambda

Fetches data from external URLs and saves to S3 input bucket.
Triggered by EventBridge schedule (every 5 minutes).

Time-based filtering:
- 08:00-12:00 CET: Fetch on every trigger (5-min intervals)
- 12:00-17:00 CET: Fetch only on 10-min marks (12:00, 12:10, etc.)
- Outside hours: Skip

Data sources configured via environment variables.
"""

import os
import json
import logging
import urllib.request
from datetime import datetime, timezone, timedelta

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set by CDK)
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')
ORDERS_URL = os.environ.get('ORDERS_URL')

s3 = boto3.client('s3')

# CET timezone offset (UTC+1 in winter, UTC+2 in summer)
# This is a simplified approach - for production, consider using pytz
CET_OFFSET = timedelta(hours=1)  # Adjust to +2 for CEST (summer)


def should_fetch_now() -> tuple[bool, str]:
    """
    Check if we should fetch based on current time (CET).

    Returns:
        tuple: (should_fetch: bool, reason: str)
    """
    now_utc = datetime.now(timezone.utc)
    now_cet = now_utc + CET_OFFSET
    hour = now_cet.hour
    minute = now_cet.minute

    # Before 08:00 or after 17:00 - skip
    if hour < 8 or hour >= 17:
        return False, f"Outside operating hours ({hour:02d}:{minute:02d} CET)"

    # 08:00-12:00 - always fetch (peak hours, 5-min intervals)
    if hour < 12:
        return True, f"Peak hours ({hour:02d}:{minute:02d} CET)"

    # 12:00-17:00 - fetch only on 10-min marks
    if minute % 10 == 0:
        return True, f"Afternoon 10-min mark ({hour:02d}:{minute:02d} CET)"
    else:
        return False, f"Skipping - not a 10-min mark ({hour:02d}:{minute:02d} CET)"


def fetch_url(url: str, timeout: int = 30) -> bytes:
    """Fetch content from URL."""
    logger.info(f"Fetching URL: {url}")
    request = urllib.request.Request(url, headers={'User-Agent': 'GoldSport-Fetcher/1.0'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def save_to_s3(bucket: str, key: str, data: bytes, content_type: str = 'text/plain'):
    """Save data to S3 bucket."""
    logger.info(f"Saving to s3://{bucket}/{key}")
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=data,
        ContentType=content_type
    )


def main(event, context):
    """
    Lambda handler - fetches data from configured URLs and saves to S3.

    Triggered by EventBridge schedule. Uses time-based filtering to
    determine whether to actually fetch.
    """
    logger.info(f"Fetcher invoked: {json.dumps(event)}")

    # Check if we should fetch at this time
    should_fetch, reason = should_fetch_now()
    logger.info(f"Time check: {reason}")

    if not should_fetch:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Skipped - time-based filtering',
                'reason': reason
            })
        }

    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d-%H%M%S')
    results = []

    # Fetch orders TSV
    if ORDERS_URL:
        try:
            data = fetch_url(ORDERS_URL)
            key = f'orders/orders-{timestamp}.tsv'
            save_to_s3(INPUT_BUCKET, key, data, 'text/tab-separated-values')
            results.append({'source': 'orders', 'status': 'success', 'key': key})
            logger.info(f"Orders fetched successfully: {len(data)} bytes")
        except Exception as e:
            logger.error(f"Failed to fetch orders: {e}")
            results.append({'source': 'orders', 'status': 'error', 'error': str(e)})
    else:
        logger.warning("ORDERS_URL not configured, skipping orders fetch")

    # Future: Add more data sources here
    # e.g., instructors roster, locations, etc.

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Fetch complete',
            'timestamp': timestamp,
            'results': results
        })
    }
