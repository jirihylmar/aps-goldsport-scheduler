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
from config_loader import ConfigLoader
from processors import ProcessorError
from processors.parse_orders import ParseOrdersProcessor
from processors.parse_instructors import ParseInstructorsProcessor
from processors.merge_data import MergeDataProcessor
from processors.validate import ValidateProcessor
from processors.privacy import PrivacyProcessor
from processors.storage import StorageProcessor
from processors.output import OutputProcessor

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables (set by CDK)
DATA_TABLE = os.environ.get('DATA_TABLE')
WEBSITE_BUCKET = os.environ.get('WEBSITE_BUCKET')
INPUT_BUCKET = os.environ.get('INPUT_BUCKET')

# AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Config loader
config_loader = ConfigLoader(s3_client=s3_client)


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
    return (PipelineBuilder()
        .add(ParseOrdersProcessor())
        .add(ParseInstructorsProcessor())
        .add(MergeDataProcessor())
        .add(ValidateProcessor())
        .add(PrivacyProcessor())
        .add(StorageProcessor())
        .add(OutputProcessor())
        .build())


def load_configs() -> dict:
    """
    Load configuration files from S3.

    Returns:
        Dictionary with all configurations
    """
    if not WEBSITE_BUCKET:
        logger.warning("No WEBSITE_BUCKET configured, using defaults")
        return {
            'ui_translations': {},
            'dictionaries': {},
            'enrichment': {},
        }

    try:
        return config_loader.load_all(WEBSITE_BUCKET)
    except Exception as e:
        logger.error(f"Failed to load configs: {e}")
        return {
            'ui_translations': {},
            'dictionaries': {},
            'enrichment': {},
        }


def create_initial_data(bucket: str, key: str, configs: dict) -> dict:
    """
    Create initial data dictionary for the pipeline.

    Args:
        bucket: S3 bucket name
        key: S3 object key that triggered the event
        configs: Loaded configuration files

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
            # Loaded configs
            'ui_translations': configs.get('ui_translations', {}),
            'dictionaries': configs.get('dictionaries', {}),
            'enrichment': configs.get('enrichment', {}),
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

    # Load configs once for all records
    configs = load_configs()
    logger.info(f"Loaded configs: {list(configs.keys())}")

    results = []

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        logger.info(f"Processing file: s3://{bucket}/{key}")

        try:
            # Create initial data for pipeline
            data = create_initial_data(bucket, key, configs)

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
