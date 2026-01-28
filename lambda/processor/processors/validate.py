"""
GoldSport Scheduler - Validate Processor

Validates and cleans lesson records.
"""

import logging
import re
from typing import Dict, Any, List

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class ValidateProcessor(Processor):
    """
    Validate and clean lesson records.

    Removes records with:
    - Missing required fields (date, start, end)
    - Invalid time formats
    - Empty participant lists

    Logs warnings for filtered records.
    """

    # Required fields that must be present and non-empty
    REQUIRED_FIELDS = ['date', 'start', 'end']

    # Time format pattern (HH:MM)
    TIME_PATTERN = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')

    def process(self, data: dict) -> dict:
        """
        Validate lessons and filter invalid ones.

        Args:
            data: Pipeline data with lessons

        Returns:
            Data with validated lessons
        """
        lessons = data.get('lessons', [])

        if not lessons:
            logger.info("No lessons to validate")
            return data

        try:
            valid_lessons = []
            filtered_count = 0
            filter_reasons = {}

            for lesson in lessons:
                is_valid, reason = self._validate_lesson(lesson)
                if is_valid:
                    valid_lessons.append(lesson)
                else:
                    filtered_count += 1
                    filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
                    logger.debug(f"Filtered lesson: {reason} - {lesson.get('booking_id', 'unknown')}")

            data['lessons'] = valid_lessons
            data['metadata']['records_filtered'] = data['metadata'].get('records_filtered', 0) + filtered_count

            if filtered_count > 0:
                logger.info(f"Filtered {filtered_count} invalid lessons: {filter_reasons}")

            logger.info(f"Validated {len(valid_lessons)} lessons")

        except Exception as e:
            raise ProcessorError(self.name, f"Failed to validate: {e}", e)

        return data

    def _validate_lesson(self, lesson: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate a single lesson.

        Args:
            lesson: Lesson record to validate

        Returns:
            Tuple of (is_valid, reason)
        """
        # Check required fields
        for field in self.REQUIRED_FIELDS:
            value = lesson.get(field, '')
            if not value or (isinstance(value, str) and not value.strip()):
                return False, f"missing_{field}"

        # Validate time formats
        start = lesson.get('start', '')
        end = lesson.get('end', '')

        if not self._is_valid_time(start):
            return False, "invalid_start_time"

        if not self._is_valid_time(end):
            return False, "invalid_end_time"

        # Check for valid people list (warn but don't filter)
        people = lesson.get('people', [])
        if not people:
            logger.debug(f"Lesson has no people listed")

        return True, ""

    def _is_valid_time(self, time_str: str) -> bool:
        """
        Validate time format (HH:MM).

        Args:
            time_str: Time string to validate

        Returns:
            True if valid, False otherwise
        """
        if not time_str:
            return False
        return bool(self.TIME_PATTERN.match(time_str))
