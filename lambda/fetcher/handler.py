"""
GoldSport Scheduler - Fetcher Lambda

Fetches data from external URLs and saves to S3 input bucket.
Triggered by EventBridge schedule (every 5 minutes).

Data sources configured via environment variables.
"""

import os
import json
import logging
import urllib.request
from datetime import datetime

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set by CDK)
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')
ORDERS_URL = os.environ.get('ORDERS_URL')

s3 = boto3.client('s3')


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

    Triggered by EventBridge schedule.
    """
    logger.info(f"Fetcher invoked: {json.dumps(event)}")
    timestamp = datetime.utcnow().strftime('%Y-%m-%d-%H%M%S')
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
