"""
Tests for ValidateProcessor.
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.validate import ValidateProcessor


class TestValidateProcessor(unittest.TestCase):
    """Tests for ValidateProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = ValidateProcessor()

    def _make_lesson(self, **overrides):
        """Create a valid lesson with optional overrides."""
        base = {
            'booking_id': 'test-123',
            'date': '28.12.2025',
            'start': '09:00',
            'end': '10:50',
            'level_key': 'test',
            'language_key': 'cz',
            'location_key': 'Stone bar',
            'sponsor': 'Test Person',
            'participants': ['Child1'],
            'participant_count': 1,
            'instructor': {'name': 'Test'},
            'notes': None,
        }
        base.update(overrides)
        return base

    def test_valid_lesson_passes(self):
        """Test that valid lessons pass validation."""
        data = {
            'lessons': [self._make_lesson()],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 1)

    def test_missing_date_filtered(self):
        """Test that lessons with missing date are filtered."""
        data = {
            'lessons': [
                self._make_lesson(date=''),
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 0)
        self.assertEqual(result['metadata']['records_filtered'], 1)

    def test_missing_start_filtered(self):
        """Test that lessons with missing start time are filtered."""
        data = {
            'lessons': [
                self._make_lesson(start=''),
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 0)

    def test_missing_end_filtered(self):
        """Test that lessons with missing end time are filtered."""
        data = {
            'lessons': [
                self._make_lesson(end=None),
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 0)

    def test_invalid_time_format_filtered(self):
        """Test that lessons with invalid time format are filtered."""
        data = {
            'lessons': [
                self._make_lesson(start='9:00'),  # Missing leading zero
                self._make_lesson(start='25:00'),  # Invalid hour
                self._make_lesson(end='10:60'),    # Invalid minute
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 0)
        self.assertEqual(result['metadata']['records_filtered'], 3)

    def test_valid_edge_times(self):
        """Test edge cases for valid times."""
        data = {
            'lessons': [
                self._make_lesson(start='00:00', end='23:59'),
                self._make_lesson(start='12:30', end='14:00'),
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 2)

    def test_empty_lessons(self):
        """Test with empty lessons list."""
        data = {
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 0)

    def test_mixed_valid_invalid(self):
        """Test with mix of valid and invalid lessons."""
        data = {
            'lessons': [
                self._make_lesson(booking_id='valid1'),
                self._make_lesson(booking_id='invalid1', date=''),
                self._make_lesson(booking_id='valid2'),
                self._make_lesson(booking_id='invalid2', start='bad'),
            ],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(len(result['lessons']), 2)
        self.assertEqual(result['metadata']['records_filtered'], 2)
        booking_ids = [l['booking_id'] for l in result['lessons']]
        self.assertIn('valid1', booking_ids)
        self.assertIn('valid2', booking_ids)


if __name__ == '__main__':
    unittest.main()
