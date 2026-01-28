"""
GoldSport Scheduler - Output Processor

Generates schedule.json for the website bucket.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List

import boto3

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class OutputProcessor(Processor):
    """
    Generate schedule.json and upload to website bucket.

    Separates lessons into current and upcoming based on time.
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
        Generate schedule.json and upload to S3.

        Args:
            data: Pipeline data with lessons

        Returns:
            Data with output info in metadata
        """
        lessons = data.get('lessons', [])
        website_bucket = data.get('config', {}).get('website_bucket')

        if not website_bucket:
            raise ProcessorError(self.name, "No website_bucket configured")

        try:
            # Build schedule JSON
            schedule = self._build_schedule(lessons, data['metadata'])

            # Upload to S3
            self._upload_schedule(website_bucket, schedule)

            data['metadata']['output'] = {
                'bucket': website_bucket,
                'key': 'data/schedule.json',
                'current_lessons': len(schedule.get('current_lessons', [])),
                'upcoming_lessons': len(schedule.get('upcoming_lessons', [])),
            }

            logger.info(
                f"Generated schedule.json: "
                f"{len(schedule['current_lessons'])} current, "
                f"{len(schedule['upcoming_lessons'])} upcoming"
            )

        except ProcessorError:
            raise
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to generate output: {e}", e)

        return data

    def _build_schedule(self, lessons: List[Dict], metadata: Dict) -> Dict:
        """
        Build the schedule.json structure.

        Args:
            lessons: Processed lessons
            metadata: Processing metadata

        Returns:
            Schedule JSON structure
        """
        now = datetime.now(timezone.utc)
        today = now.strftime('%Y-%m-%d')
        today_ddmmyyyy = now.strftime('%d.%m.%Y')

        # Filter to today's lessons
        today_lessons = [
            l for l in lessons
            if self._is_today(l.get('date', ''), today_ddmmyyyy)
        ]

        # Separate current vs upcoming
        current_lessons = []
        upcoming_lessons = []

        current_time = now.strftime('%H:%M')

        for lesson in today_lessons:
            formatted = self._format_lesson(lesson)
            if self._is_current(lesson, current_time):
                current_lessons.append(formatted)
            elif self._is_upcoming(lesson, current_time):
                upcoming_lessons.append(formatted)

        # Sort by start time
        current_lessons.sort(key=lambda x: x['start'])
        upcoming_lessons.sort(key=lambda x: x['start'])

        # For debugging: include all lessons by date
        all_by_date = self._group_all_by_date(lessons)

        return {
            'generated_at': now.isoformat(),
            'date': today,
            'data_sources': metadata.get('data_sources', {}),
            'current_lessons': current_lessons,
            'upcoming_lessons': upcoming_lessons,
            'all_lessons_by_date': all_by_date,  # Debug: all lessons grouped by date
        }

    def _is_today(self, lesson_date: str, today: str) -> bool:
        """Check if lesson is for today."""
        return lesson_date == today

    def _group_all_by_date(self, lessons: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group all lessons by date for debugging.

        Returns dict like: {"28.01.2026": [...lessons...], "29.01.2026": [...]}
        """
        by_date = {}
        for lesson in lessons:
            date = lesson.get('date', '')
            if not date:
                continue
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(self._format_lesson(lesson))

        # Sort lessons within each date by start time
        for date in by_date:
            by_date[date].sort(key=lambda x: x['start'])

        return by_date

    def _is_current(self, lesson: Dict, current_time: str) -> bool:
        """
        Check if lesson is currently happening.

        A lesson is current if: start <= now < end
        """
        start = lesson.get('start', '')
        end = lesson.get('end', '')

        if not start or not end:
            return False

        return start <= current_time < end

    def _is_upcoming(self, lesson: Dict, current_time: str) -> bool:
        """
        Check if lesson is upcoming (hasn't started yet).
        """
        start = lesson.get('start', '')
        return start > current_time if start else False

    def _format_lesson(self, lesson: Dict) -> Dict:
        """
        Format lesson for output JSON.

        Args:
            lesson: Internal lesson format

        Returns:
            Output format for schedule.json
        """
        instructor = lesson.get('instructor', {})

        return {
            'start': lesson.get('start', ''),
            'end': lesson.get('end', ''),
            'level_key': lesson.get('level_key', ''),
            'language_key': lesson.get('language_key', ''),
            'location_key': lesson.get('location_key', ''),
            'sponsor': lesson.get('sponsor', ''),
            'participants': lesson.get('participants', []),
            'participant_count': lesson.get('participant_count', 0),
            'instructor': {
                'id': instructor.get('id'),
                'name': instructor.get('name', ''),
                'photo': instructor.get('photo', ''),
            } if instructor else None,
            'booking_id': lesson.get('booking_id'),
            'notes': lesson.get('notes'),
        }

    def _upload_schedule(self, bucket: str, schedule: Dict) -> None:
        """Upload schedule.json to S3."""
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key='data/schedule.json',
                Body=json.dumps(schedule, ensure_ascii=False, indent=2),
                ContentType='application/json',
                CacheControl='max-age=60',  # Short cache for frequent updates
            )
            logger.info(f"Uploaded schedule.json to s3://{bucket}/data/schedule.json")
        except Exception as e:
            raise ProcessorError(self.name, f"Failed to upload to S3: {e}", e)
