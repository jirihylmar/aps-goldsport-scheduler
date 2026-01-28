"""
Tests for OutputProcessor.
"""

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.output import OutputProcessor


class TestOutputProcessor(unittest.TestCase):
    """Tests for OutputProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_s3 = MagicMock()
        self.processor = OutputProcessor(s3_client=self.mock_s3)

    def _make_lesson(self, **overrides):
        """Create a lesson with optional overrides."""
        base = {
            'booking_id': 'test-123',
            'date': '28.01.2026',  # Today in test context
            'start': '10:00',
            'end': '11:50',
            'level_key': 'dětská školka',
            'language_key': 'de',
            'location_key': 'Stone bar',
            'sponsor': 'Test Pe',
            'participants': ['Child1'],
            'participant_count': 1,
            'instructor': {
                'id': 'jan-novak',
                'name': 'Jan Novák',
                'photo': 'assets/instructors/jan-novak.jpg'
            },
            'notes': None,
        }
        base.update(overrides)
        return base

    @patch('processors.output.datetime')
    def test_generates_schedule_json(self, mock_datetime):
        """Test that schedule.json is generated and uploaded."""
        # Mock current time
        mock_now = datetime(2026, 1, 28, 10, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-web-bucket'},
            'lessons': [self._make_lesson()],
            'metadata': {'data_sources': {'orders': 'test.tsv'}},
        }

        result = self.processor.process(data)

        # Should have uploaded to S3
        self.mock_s3.put_object.assert_called_once()
        call_kwargs = self.mock_s3.put_object.call_args[1]

        self.assertEqual(call_kwargs['Bucket'], 'test-web-bucket')
        self.assertEqual(call_kwargs['Key'], 'data/schedule.json')
        self.assertEqual(call_kwargs['ContentType'], 'application/json')

    @patch('processors.output.datetime')
    def test_current_lesson_detection(self, mock_datetime):
        """Test that current lessons are correctly identified."""
        # Time is 10:30, lesson 10:00-11:50 should be current
        mock_now = datetime(2026, 1, 28, 10, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-bucket'},
            'lessons': [
                self._make_lesson(start='10:00', end='11:50'),  # Current
            ],
            'metadata': {'data_sources': {}},
        }

        result = self.processor.process(data)

        self.assertEqual(result['metadata']['output']['current_lessons'], 1)
        self.assertEqual(result['metadata']['output']['upcoming_lessons'], 0)

    @patch('processors.output.datetime')
    def test_upcoming_lesson_detection(self, mock_datetime):
        """Test that upcoming lessons are correctly identified."""
        # Time is 09:00, lesson 10:00-11:50 should be upcoming
        mock_now = datetime(2026, 1, 28, 9, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-bucket'},
            'lessons': [
                self._make_lesson(start='10:00', end='11:50'),  # Upcoming
            ],
            'metadata': {'data_sources': {}},
        }

        result = self.processor.process(data)

        self.assertEqual(result['metadata']['output']['current_lessons'], 0)
        self.assertEqual(result['metadata']['output']['upcoming_lessons'], 1)

    @patch('processors.output.datetime')
    def test_past_lesson_excluded(self, mock_datetime):
        """Test that past lessons are excluded."""
        # Time is 15:00, lesson 10:00-11:50 is past
        mock_now = datetime(2026, 1, 28, 15, 0, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-bucket'},
            'lessons': [
                self._make_lesson(start='10:00', end='11:50'),  # Past
            ],
            'metadata': {'data_sources': {}},
        }

        result = self.processor.process(data)

        # Past lessons are neither current nor upcoming
        self.assertEqual(result['metadata']['output']['current_lessons'], 0)
        self.assertEqual(result['metadata']['output']['upcoming_lessons'], 0)

    @patch('processors.output.datetime')
    def test_other_date_excluded(self, mock_datetime):
        """Test that lessons from other dates are excluded."""
        mock_now = datetime(2026, 1, 28, 10, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-bucket'},
            'lessons': [
                self._make_lesson(date='29.01.2026'),  # Tomorrow
            ],
            'metadata': {'data_sources': {}},
        }

        result = self.processor.process(data)

        self.assertEqual(result['metadata']['output']['current_lessons'], 0)
        self.assertEqual(result['metadata']['output']['upcoming_lessons'], 0)

    def test_no_bucket_configured(self):
        """Test error when no bucket is configured."""
        data = {
            'config': {},
            'lessons': [self._make_lesson()],
            'metadata': {},
        }

        with self.assertRaises(Exception) as ctx:
            self.processor.process(data)

        self.assertIn('No website_bucket configured', str(ctx.exception))

    @patch('processors.output.datetime')
    def test_output_format(self, mock_datetime):
        """Test that output has correct format."""
        mock_now = datetime(2026, 1, 28, 10, 30, tzinfo=timezone.utc)
        mock_datetime.now.return_value = mock_now
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        data = {
            'config': {'website_bucket': 'test-bucket'},
            'lessons': [self._make_lesson()],
            'metadata': {'data_sources': {'orders': 'test.tsv'}},
        }

        self.processor.process(data)

        # Parse uploaded JSON
        call_kwargs = self.mock_s3.put_object.call_args[1]
        schedule = json.loads(call_kwargs['Body'])

        # Check structure
        self.assertIn('generated_at', schedule)
        self.assertIn('date', schedule)
        self.assertIn('data_sources', schedule)
        self.assertIn('current_lessons', schedule)
        self.assertIn('upcoming_lessons', schedule)

        # Check lesson format
        lesson = schedule['current_lessons'][0]
        self.assertIn('start', lesson)
        self.assertIn('end', lesson)
        self.assertIn('level_key', lesson)
        self.assertIn('instructor', lesson)
        self.assertEqual(lesson['instructor']['name'], 'Jan Novák')


if __name__ == '__main__':
    unittest.main()
