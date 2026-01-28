"""
GoldSport Scheduler - Parse Orders Processor

Parses TSV orders file from S3 into internal format.
Groups records by booking_id and lesson time slot.
"""

import csv
import logging
from datetime import datetime
from io import StringIO
from typing import List, Dict, Any, Optional

import boto3

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class ParseOrdersProcessor(Processor):
    """
    Parse TSV orders file and convert to internal lesson format.

    Reads TSV from S3, groups participants by booking_id and time slot,
    filters out invalid records (1970 dates).
    """

    # Required TSV columns
    REQUIRED_COLUMNS = [
        'date_lesson',
        'timestamp_start_lesson',
        'timestamp_end_lesson',
        'level',
        'name_sponsor',
        'name_participant',
        'language',
        'location_meeting',
    ]

    def __init__(self, s3_client=None):
        """
        Initialize the processor.

        Args:
            s3_client: Optional boto3 S3 client (for testing)
        """
        self.s3_client = s3_client or boto3.client('s3')

    def process(self, data: dict) -> dict:
        """
        Process orders TSV and add to data.

        Args:
            data: Pipeline data with trigger info

        Returns:
            Data with raw.orders populated
        """
        trigger = data.get('trigger', {})
        bucket = trigger.get('bucket')
        key = trigger.get('key')

        if not bucket or not key:
            raise ProcessorError(self.name, "Missing bucket or key in trigger")

        # Only process orders files
        if not key.startswith('orders/'):
            logger.info(f"Skipping non-orders file: {key}")
            return data

        try:
            # Read TSV from S3
            tsv_content = self._read_s3_file(bucket, key)

            # Parse TSV into records
            records = self._parse_tsv(tsv_content)
            logger.info(f"Parsed {len(records)} raw records from {key}")

            # Filter invalid records
            valid_records = self._filter_invalid(records)
            logger.info(f"Filtered to {len(valid_records)} valid records")

            # Group by booking and time slot
            lessons = self._group_into_lessons(valid_records)
            logger.info(f"Grouped into {len(lessons)} lessons")

            # Store in data
            data['raw']['orders'] = lessons
            data['metadata']['data_sources']['orders'] = key

        except ProcessorError:
            raise
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to parse orders: {e}", e)

        return data

    def _read_s3_file(self, bucket: str, key: str) -> str:
        """Read file content from S3."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to read s3://{bucket}/{key}: {e}", e)

    def _parse_tsv(self, content: str) -> List[Dict[str, Any]]:
        """Parse TSV content into list of dictionaries."""
        records = []
        reader = csv.DictReader(StringIO(content), delimiter='\t')

        # Validate required columns exist
        if reader.fieldnames:
            missing = set(self.REQUIRED_COLUMNS) - set(reader.fieldnames)
            if missing:
                raise ProcessorError(self.name, f"Missing required columns: {missing}")

        for row in reader:
            records.append(dict(row))

        return records

    def _filter_invalid(self, records: List[Dict]) -> List[Dict]:
        """
        Filter out invalid records.

        Invalid records:
        - date_lesson = "01.01.1970"
        - timestamp contains "1970-01-01"
        - Missing required fields
        """
        valid = []
        filtered_count = 0

        for record in records:
            # Check for 1970 dates (placeholder/invalid)
            date_lesson = record.get('date_lesson', '')
            timestamp_start = record.get('timestamp_start_lesson', '')

            if '1970' in date_lesson or '1970' in timestamp_start:
                logger.debug(f"Filtered invalid date: {date_lesson}")
                filtered_count += 1
                continue

            # Check for required fields
            missing = [col for col in self.REQUIRED_COLUMNS if not record.get(col)]
            if missing:
                logger.debug(f"Filtered missing fields: {missing}")
                filtered_count += 1
                continue

            valid.append(record)

        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} invalid records")

        return valid

    def _group_into_lessons(self, records: List[Dict]) -> List[Dict]:
        """
        Group records into lessons.

        Same booking_id + same time slot = same lesson with multiple participants.
        If booking_id is empty, use combination of time + sponsor as key.
        """
        lessons_map: Dict[str, Dict] = {}

        for record in records:
            # Create grouping key
            booking_id = record.get('booking_id', '').strip()
            start = record.get('timestamp_start_lesson', '')
            end = record.get('timestamp_end_lesson', '')
            date = record.get('date_lesson', '')

            if booking_id:
                key = f"{booking_id}_{start}_{end}"
            else:
                # Fallback: sponsor + time slot
                sponsor = record.get('name_sponsor', '')
                key = f"{sponsor}_{date}_{start}_{end}"

            if key not in lessons_map:
                # Create new lesson
                lessons_map[key] = {
                    'booking_id': booking_id or None,
                    'date_lesson': date,
                    'timestamp_start': start,
                    'timestamp_end': end,
                    'level': record.get('level', ''),
                    'language': record.get('language', ''),
                    'location_meeting': record.get('location_meeting', ''),
                    'name_sponsor': record.get('name_sponsor', ''),
                    'group_size': self._safe_int(record.get('group_size', '1')),
                    'participants': [],
                }

            # Add participant to lesson
            participant_name = record.get('name_participant', '').strip()
            if participant_name and participant_name not in lessons_map[key]['participants']:
                lessons_map[key]['participants'].append(participant_name)

        return list(lessons_map.values())

    def _safe_int(self, value: str) -> int:
        """Safely convert string to int, defaulting to 1."""
        try:
            return int(value) if value else 1
        except (ValueError, TypeError):
            return 1
