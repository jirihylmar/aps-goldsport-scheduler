"""
GoldSport Scheduler - Parse Instructors Processor

Parses instructor roster and profiles JSON from S3 into internal format.
"""

import json
import logging
from typing import Dict, Any, Optional, List

import boto3

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class ParseInstructorsProcessor(Processor):
    """
    Parse instructor JSON files from S3.

    Handles two types of files:
    - roster-YYYY-MM-DD.json: Daily assignments (instructor -> booking_ids)
    - profiles.json: Instructor profiles (name, photo, languages)
    """

    def __init__(self, s3_client=None):
        """
        Initialize the processor.

        Args:
            s3_client: Optional boto3 S3 client (for testing)
        """
        self.s3_client = s3_client or boto3.client('s3')

    def process(self, data: dict) -> dict:
        """
        Process instructor JSON files.

        Args:
            data: Pipeline data with trigger info

        Returns:
            Data with raw.instructors populated
        """
        trigger = data.get('trigger', {})
        bucket = trigger.get('bucket')
        key = trigger.get('key')
        input_bucket = data.get('config', {}).get('input_bucket', bucket)

        if not bucket or not key:
            raise ProcessorError(self.name, "Missing bucket or key in trigger")

        try:
            # If triggered by an instructor file, process it directly
            if key.startswith('instructors/'):
                self._process_instructor_file(data, bucket, key)
            else:
                # Otherwise, try to load latest instructor files from input bucket
                self._load_latest_instructors(data, input_bucket)

        except ProcessorError:
            raise
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to parse instructors: {e}", e)

        return data

    def _process_instructor_file(self, data: dict, bucket: str, key: str) -> None:
        """Process a specific instructor file."""
        if 'roster' in key:
            content = self._read_s3_json(bucket, key)
            data['raw']['instructors']['roster'] = content
            data['metadata']['data_sources']['roster'] = key
            logger.info(f"Loaded roster from {key}")
        elif 'profiles' in key:
            content = self._read_s3_json(bucket, key)
            data['raw']['instructors']['profiles'] = content
            data['metadata']['data_sources']['profiles'] = key
            logger.info(f"Loaded profiles from {key}")

    def _load_latest_instructors(self, data: dict, bucket: str) -> None:
        """
        Load latest instructor files from the bucket.

        Looks for:
        - instructors/profiles.json (static)
        - instructors/roster-*.json (latest by filename)
        """
        # Try to load profiles (static file)
        try:
            profiles = self._read_s3_json(bucket, 'instructors/profiles.json')
            data['raw']['instructors']['profiles'] = profiles
            data['metadata']['data_sources']['profiles'] = 'instructors/profiles.json'
            logger.info("Loaded instructor profiles")
        except Exception as e:
            logger.warning(f"Could not load profiles.json: {e}")

        # Try to find and load latest roster
        try:
            roster_key = self._find_latest_roster(bucket)
            if roster_key:
                roster = self._read_s3_json(bucket, roster_key)
                data['raw']['instructors']['roster'] = roster
                data['metadata']['data_sources']['roster'] = roster_key
                logger.info(f"Loaded roster from {roster_key}")
        except Exception as e:
            logger.warning(f"Could not load roster: {e}")

    def _find_latest_roster(self, bucket: str) -> Optional[str]:
        """Find the latest roster file by listing S3 prefix."""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix='instructors/roster-'
            )
            if 'Contents' not in response:
                return None

            # Sort by key (filename) descending to get latest date
            files = sorted(
                [obj['Key'] for obj in response['Contents']],
                reverse=True
            )
            return files[0] if files else None

        except Exception as e:
            logger.warning(f"Error listing roster files: {e}")
            return None

    def _read_s3_json(self, bucket: str, key: str) -> Dict[str, Any]:
        """Read and parse JSON file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except self.s3_client.exceptions.NoSuchKey:
            logger.info(f"File not found: s3://{bucket}/{key}")
            return {}
        except json.JSONDecodeError as e:
            raise ProcessorError(self.name, f"Invalid JSON in {key}: {e}", e)
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to read s3://{bucket}/{key}: {e}", e)


def get_instructor_for_booking(
    instructors_data: dict,
    booking_id: str
) -> Optional[Dict[str, Any]]:
    """
    Helper function to find instructor for a booking.

    Args:
        instructors_data: The raw.instructors data
        booking_id: The booking_id to look up

    Returns:
        Instructor profile dict or None if not found
    """
    roster = instructors_data.get('roster', {})
    profiles = instructors_data.get('profiles', {})

    # Find instructor in roster assignments
    for assignment in roster.get('assignments', []):
        if booking_id in assignment.get('booking_ids', []):
            instructor_id = assignment.get('instructor_id')
            if instructor_id and instructor_id in profiles:
                profile = profiles[instructor_id].copy()
                profile['id'] = instructor_id
                return profile

    return None
