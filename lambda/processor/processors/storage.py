"""
GoldSport Scheduler - Storage Processor

Stores processed schedule data in DynamoDB.
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, List

import boto3
from botocore.exceptions import ClientError

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class StorageProcessor(Processor):
    """
    Store processed lessons in DynamoDB with versioning.

    Schema (with versioning):
    - PK: SCHEDULE#{date}, SK: META#{timestamp} - Schedule metadata
    - PK: SCHEDULE#{date}, SK: LESSON#{timestamp}#{id} - Individual lessons

    Each processing run creates new entries with unique timestamps,
    preserving history for auditing and debugging.
    """

    BATCH_SIZE = 25  # DynamoDB batch write limit

    def __init__(self, dynamodb_resource=None, timestamp_override=None):
        """
        Initialize the processor.

        Args:
            dynamodb_resource: Optional boto3 DynamoDB resource (for testing)
            timestamp_override: Optional timestamp string for testing
        """
        self.dynamodb = dynamodb_resource or boto3.resource('dynamodb')
        self._table = None
        self._timestamp_override = timestamp_override
        self._processing_timestamp = None

    def process(self, data: dict) -> dict:
        """
        Store lessons in DynamoDB with versioning.

        Args:
            data: Pipeline data with lessons

        Returns:
            Data with storage results in metadata
        """
        lessons = data.get('lessons', [])
        table_name = data.get('config', {}).get('data_table')

        if not table_name:
            raise ProcessorError(self.name, "No data_table configured")

        if not lessons:
            logger.info("No lessons to store")
            return data

        try:
            self._table = self.dynamodb.Table(table_name)

            # Generate processing timestamp (once per run for consistency)
            self._processing_timestamp = (
                self._timestamp_override or
                datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            )

            # Group lessons by date
            lessons_by_date = self._group_by_date(lessons)

            total_stored = 0
            for date, date_lessons in lessons_by_date.items():
                stored = self._store_date_schedule(date, date_lessons, data['metadata'])
                total_stored += stored

            data['metadata']['lessons_stored'] = total_stored
            logger.info(f"Stored {total_stored} lessons in DynamoDB")

        except ProcessorError:
            raise
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to store data: {e}", e)

        return data

    def _group_by_date(self, lessons: List[Dict]) -> Dict[str, List[Dict]]:
        """Group lessons by date."""
        by_date = {}
        for lesson in lessons:
            date = lesson.get('date', '')
            if date:
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(lesson)
        return by_date

    def _store_date_schedule(
        self,
        date: str,
        lessons: List[Dict],
        metadata: Dict
    ) -> int:
        """
        Store schedule for a specific date.

        Args:
            date: Date string (DD.MM.YYYY)
            lessons: List of lessons for this date
            metadata: Processing metadata

        Returns:
            Number of items stored
        """
        pk = f"SCHEDULE#{date}"
        ts = self._processing_timestamp

        # Store metadata item with versioned SK
        meta_item = {
            'PK': pk,
            'SK': f'META#{ts}',
            'date': date,
            'lesson_count': len(lessons),
            'generated_at': ts,
            'data_sources': metadata.get('data_sources', {}),
            'records_filtered': metadata.get('records_filtered', 0),
        }

        try:
            self._table.put_item(Item=meta_item)
        except ClientError as e:
            logger.error(f"Failed to store metadata: {e}")
            raise

        # Store lesson items in batches with versioned SK
        items_stored = 1  # Count metadata item

        with self._table.batch_writer() as batch:
            for lesson in lessons:
                lesson_id = self._generate_lesson_id(lesson)
                item = {
                    'PK': pk,
                    'SK': f'LESSON#{ts}#{lesson_id}',
                    **self._prepare_lesson_item(lesson)
                }
                batch.put_item(Item=item)
                items_stored += 1

        return items_stored

    def _generate_lesson_id(self, lesson: Dict) -> str:
        """
        Generate unique ID for a lesson.

        For private lessons with booking_id: hash of booking_id + start time
        For group lessons: hash of date + start + level + group_type + location
        """
        booking_id = lesson.get('booking_id', '')
        group_type = lesson.get('group_type_key', '')
        start = lesson.get('start', '')

        # Private lessons with booking_id get unique ID per booking + time slot
        if group_type == 'privát' and booking_id:
            key_data = f"{booking_id}_{start}"
            return hashlib.md5(key_data.encode()).hexdigest()[:16]

        # Group lessons: hash from grouping fields
        date = lesson.get('date', '')
        start = lesson.get('start', '')
        level = lesson.get('level_key', '')
        location = lesson.get('location_key', '')

        key_data = f"{date}_{start}_{level}_{group_type}_{location}"
        return hashlib.md5(key_data.encode()).hexdigest()[:16]

    def _prepare_lesson_item(self, lesson: Dict) -> Dict:
        """
        Prepare lesson dict for DynamoDB storage.

        Converts any non-serializable types.
        """
        item = {
            'booking_id': lesson.get('booking_id'),
            'date': lesson.get('date'),
            'start': lesson.get('start'),
            'end': lesson.get('end'),
            'level_key': lesson.get('level_key'),
            'group_type_key': lesson.get('group_type_key'),
            'location_key': lesson.get('location_key'),
            'people_count': lesson.get('people_count', 0),
            'people': lesson.get('people', []),
            'notes': lesson.get('notes'),
        }

        # Store instructor info
        instructor = lesson.get('instructor', {})
        if instructor:
            item['instructor_id'] = instructor.get('id')
            item['instructor_name'] = instructor.get('name')
            item['instructor_photo'] = instructor.get('photo')

        return item
