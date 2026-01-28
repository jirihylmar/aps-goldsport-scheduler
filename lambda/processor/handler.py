"""
GoldSport Scheduler - Processor Lambda

Processes input data (orders TSV, instructors JSON) through a modular pipeline
and outputs schedule.json to the website bucket.

Triggered by S3 events when new files are uploaded to the input bucket.
"""

import os
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set by CDK)
DATA_TABLE = os.environ.get('DATA_TABLE')
WEBSITE_BUCKET = os.environ.get('WEBSITE_BUCKET')
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')


def main(event, context):
    """
    Lambda handler - processes S3 upload events.

    Pipeline will be implemented in Phase 2:
    1. ParseOrdersProcessor - TSV -> internal format
    2. ParseInstructorsProcessor - JSON -> internal format
    3. MergeDataProcessor - combine sources
    4. ValidateProcessor - filter invalid records
    5. PrivacyProcessor - apply name filtering
    6. Store to DynamoDB
    7. Generate schedule.json -> S3 website bucket
    """
    logger.info(f"Processing event: {json.dumps(event)}")

    # Extract S3 event info
    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info(f"Processing file: s3://{bucket}/{key}")

        # TODO: Implement processing pipeline in Phase 2
        # For now, just log the event

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing complete',
            'records_processed': len(event.get('Records', []))
        })
    }
