"""
GoldSport Scheduler - Processor Lambda

Processes input data (orders TSV, instructors JSON) through a modular pipeline
and outputs schedule.json to the website bucket.

Triggered by S3 events when new files are uploaded to the input bucket.
"""

import os
import json
import logging

import boto3

from pipeline import Pipeline, PipelineBuilder
from processors import ProcessorError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set by CDK)
DATA_TABLE = os.environ.get('DATA_TABLE')
WEBSITE_BUCKET = os.environ.get('WEBSITE_BUCKET')
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')


def build_pipeline() -> Pipeline:
    """
    Build the processing pipeline.

    Pipeline stages:
    1. ParseOrdersProcessor - TSV -> internal format
    2. ParseInstructorsProcessor - JSON -> internal format
    3. MergeDataProcessor - combine sources
    4. ValidateProcessor - filter invalid records
    5. PrivacyProcessor - apply name filtering
    6. StorageProcessor - save to DynamoDB
    7. OutputProcessor - generate schedule.json
    """
    # TODO: Add processors as they are implemented in Phase 2
    # For now, return empty pipeline
    return PipelineBuilder().build()


def create_initial_data(bucket: str, key: str) -> dict:
    """
    Create initial data dictionary for the pipeline.

    Args:
        bucket: S3 bucket name
        key: S3 object key that triggered the event

    Returns:
        Initial data dictionary for pipeline processing
    """
    return {
        # Source information
        'trigger': {
            'bucket': bucket,
            'key': key,
        },
        # Configuration (loaded by processors)
        'config': {
            'data_table': DATA_TABLE,
            'website_bucket': WEBSITE_BUCKET,
            'input_bucket': INPUT_BUCKET,
        },
        # Raw data (populated by parse processors)
        'raw': {
            'orders': [],
            'instructors': {},
            'overrides': [],
        },
        # Processed data (populated by merge/validate processors)
        'lessons': [],
        # Metadata
        'metadata': {
            'data_sources': {},
            'processing_errors': [],
            'records_filtered': 0,
        },
    }


def main(event, context):
    """
    Lambda handler - processes S3 upload events.

    Extracts S3 event info and runs the processing pipeline.
    """
    logger.info(f"Processing event: {json.dumps(event)}")

    results = []

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info(f"Processing file: s3://{bucket}/{key}")

        try:
            # Create initial data for pipeline
            data = create_initial_data(bucket, key)

            # Build and run pipeline
            pipeline = build_pipeline()
            result = pipeline.run(data)

            results.append({
                'key': key,
                'status': 'success',
                'lessons_processed': len(result.get('lessons', [])),
            })

        except ProcessorError as e:
            logger.error(f"Pipeline failed at {e.processor_name}: {e.message}")
            results.append({
                'key': key,
                'status': 'error',
                'error': str(e),
            })

        except Exception as e:
            logger.error(f"Unexpected error processing {key}: {e}")
            results.append({
                'key': key,
                'status': 'error',
                'error': str(e),
            })

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processing complete',
            'results': results,
        })
    }
