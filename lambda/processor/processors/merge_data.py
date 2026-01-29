"""
GoldSport Scheduler - Merge Data Processor

Merges orders with instructor assignments to create unified lesson records.
"""

import logging
from typing import Dict, Any, List, Optional

from processors import Processor, ProcessorError
from processors.parse_instructors import get_instructor_for_booking

logger = logging.getLogger(__name__)


class MergeDataProcessor(Processor):
    """
    Merge orders with instructor data.

    Combines:
    - Order data (participants, times, levels)
    - Instructor assignments (from roster)
    - Instructor profiles (name, photo)

    Applies default instructor if no assignment found.
    """

    DEFAULT_INSTRUCTOR = {
        'id': None,
        'name': 'GoldSport Team',
        'photo': 'assets/logo.png',
    }

    def process(self, data: dict) -> dict:
        """
        Merge orders with instructor data.

        Args:
            data: Pipeline data with raw.orders and raw.instructors

        Returns:
            Data with lessons populated
        """
        orders = data.get('raw', {}).get('orders', [])
        instructors = data.get('raw', {}).get('instructors', {})

        if not orders:
            logger.warning("No orders to merge")
            data['lessons'] = []
            return data

        try:
            lessons = []
            merged_count = 0
            default_count = 0

            for order in orders:
                lesson = self._create_lesson(order, instructors)
                if lesson.get('instructor', {}).get('id') is None:
                    default_count += 1
                else:
                    merged_count += 1
                lessons.append(lesson)

            data['lessons'] = lessons
            logger.info(
                f"Merged {len(lessons)} lessons: "
                f"{merged_count} with instructors, {default_count} with defaults"
            )

        except Exception as e:
            raise ProcessorError(self.name, f"Failed to merge data: {e}", e)

        return data

    def _create_lesson(
        self,
        order: Dict[str, Any],
        instructors: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a unified lesson record.

        Args:
            order: Order record from ParseOrdersProcessor
            instructors: Instructor data from ParseInstructorsProcessor

        Returns:
            Unified lesson record
        """
        booking_id = order.get('booking_id')

        # Try to find instructor for this booking
        instructor = None
        if booking_id:
            instructor = get_instructor_for_booking(instructors, booking_id)

        if not instructor:
            instructor = self.DEFAULT_INSTRUCTOR.copy()

        # Extract time from timestamp
        start_time = self._extract_time(order.get('timestamp_start', ''))
        end_time = self._extract_time(order.get('timestamp_end', ''))

        # Get people list (new format with name, language, sponsor per person)
        people = order.get('people', [])

        return {
            'order_id': order.get('order_id', ''),  # Always present for private lessons
            'booking_id': booking_id,
            'date': order.get('date_lesson', ''),
            'start': start_time,
            'end': end_time,
            'level_key': order.get('level', ''),
            'group_type_key': order.get('group_type', ''),  # privát, malá skupina, velká skupina
            'location_key': order.get('location_meeting', ''),
            'people_count': order.get('people_count', len(people)),
            'people': people,  # [{name, language, sponsor}, ...]
            'instructor': instructor,
            'notes': None,
        }

    def _extract_time(self, timestamp: str) -> str:
        """
        Extract HH:MM time from ISO timestamp.

        Args:
            timestamp: ISO 8601 timestamp (e.g., "2025-12-28T09:00:00+01:00")

        Returns:
            Time string in HH:MM format (e.g., "09:00")
        """
        if not timestamp:
            return ''

        # Handle ISO format: 2025-12-28T09:00:00+01:00
        if 'T' in timestamp:
            time_part = timestamp.split('T')[1]
            # Take just HH:MM
            return time_part[:5]

        return timestamp
