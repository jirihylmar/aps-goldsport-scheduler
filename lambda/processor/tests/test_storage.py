"""
Tests for StorageProcessor.
"""

import unittest
from unittest.mock import MagicMock, patch, call

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.storage import StorageProcessor


class TestStorageProcessor(unittest.TestCase):
    """Tests for StorageProcessor."""

    # Fixed timestamp for predictable test results
    TEST_TIMESTAMP = '2026-01-29T10:00:00Z'

    def setUp(self):
        """Set up test fixtures."""
        self.mock_dynamodb = MagicMock()
        self.mock_table = MagicMock()
        self.mock_dynamodb.Table.return_value = self.mock_table

        # Mock batch writer context manager
        self.mock_batch = MagicMock()
        self.mock_table.batch_writer.return_value.__enter__ = MagicMock(return_value=self.mock_batch)
        self.mock_table.batch_writer.return_value.__exit__ = MagicMock(return_value=False)

        # Use fixed timestamp for predictable SK values
        self.processor = StorageProcessor(
            dynamodb_resource=self.mock_dynamodb,
            timestamp_override=self.TEST_TIMESTAMP
        )

    def _make_lesson(self, **overrides):
        """Create a lesson with optional overrides."""
        base = {
            'booking_id': 'test-booking-123',
            'date': '28.12.2025',
            'start': '09:00',
            'end': '10:50',
            'level_key': 'dětská školka',
            'group_type_key': 'privát',
            'location_key': 'Stone bar',
            'people': [
                {'name': 'Child1', 'language': 'de', 'sponsor': 'Te.Pe.'},
                {'name': 'Child2', 'language': 'de', 'sponsor': 'Te.Pe.'},
            ],
            'people_count': 2,
            'instructor': {
                'id': 'jan-novak',
                'name': 'Jan Novák',
                'photo': 'assets/instructors/jan-novak.jpg'
            },
            'notes': None,
        }
        base.update(overrides)
        return base

    def test_stores_lessons(self):
        """Test that lessons are stored in DynamoDB with versioning."""
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [self._make_lesson()],
            'metadata': {'data_sources': {'orders': 'test.tsv'}},
        }

        result = self.processor.process(data)

        # Should have called Table
        self.mock_dynamodb.Table.assert_called_once_with('test-table')

        # Should have stored metadata with versioned SK
        self.mock_table.put_item.assert_called_once()
        meta_call = self.mock_table.put_item.call_args
        self.assertEqual(meta_call[1]['Item']['PK'], 'SCHEDULE#28.12.2025')
        self.assertEqual(meta_call[1]['Item']['SK'], f'META#{self.TEST_TIMESTAMP}')

        # Should have stored lesson via batch writer
        self.mock_batch.put_item.assert_called_once()

    def test_groups_by_date(self):
        """Test that lessons are grouped by date."""
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [
                self._make_lesson(date='28.12.2025', booking_id='a1'),
                self._make_lesson(date='28.12.2025', booking_id='a2'),
                self._make_lesson(date='29.12.2025', booking_id='b1'),
            ],
            'metadata': {'data_sources': {}},
        }

        result = self.processor.process(data)

        # Should have stored 2 metadata items (one per date)
        self.assertEqual(self.mock_table.put_item.call_count, 2)

    def test_metadata_stored(self):
        """Test that correct metadata is stored."""
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [self._make_lesson()],
            'metadata': {
                'data_sources': {'orders': 'orders-2026.tsv'},
                'records_filtered': 5,
            },
        }

        self.processor.process(data)

        meta_call = self.mock_table.put_item.call_args
        item = meta_call[1]['Item']

        self.assertEqual(item['lesson_count'], 1)
        self.assertEqual(item['data_sources'], {'orders': 'orders-2026.tsv'})
        self.assertEqual(item['records_filtered'], 5)

    def test_lesson_item_structure(self):
        """Test that lesson items have correct structure."""
        lesson = self._make_lesson()
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [lesson],
            'metadata': {'data_sources': {}},
        }

        self.processor.process(data)

        batch_call = self.mock_batch.put_item.call_args
        item = batch_call[1]['Item']

        self.assertEqual(item['PK'], 'SCHEDULE#28.12.2025')
        self.assertTrue(item['SK'].startswith('LESSON#'))
        self.assertEqual(item['start'], '09:00')
        self.assertEqual(item['instructor_id'], 'jan-novak')
        self.assertEqual(item['instructor_name'], 'Jan Novák')

    def test_no_table_configured(self):
        """Test error when no table is configured."""
        data = {
            'config': {},
            'lessons': [self._make_lesson()],
            'metadata': {},
        }

        with self.assertRaises(Exception) as ctx:
            self.processor.process(data)

        self.assertIn('No data_table configured', str(ctx.exception))

    def test_empty_lessons(self):
        """Test with empty lessons list."""
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Should not call DynamoDB
        self.mock_dynamodb.Table.assert_not_called()

    def test_lesson_without_booking_id(self):
        """Test that lessons without booking_id get generated ID."""
        lesson = self._make_lesson(booking_id=None)
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [lesson],
            'metadata': {'data_sources': {}},
        }

        self.processor.process(data)

        batch_call = self.mock_batch.put_item.call_args
        item = batch_call[1]['Item']

        # Should have versioned SK: LESSON#{timestamp}#{hash}
        self.assertTrue(item['SK'].startswith(f'LESSON#{self.TEST_TIMESTAMP}#'))
        # Extract just the hash part (after timestamp#)
        parts = item['SK'].split('#')
        lesson_id = parts[-1]  # Last part is the hash
        self.assertEqual(len(lesson_id), 16)  # MD5 truncated

    def test_lesson_id_is_hash(self):
        """Test that lesson ID includes timestamp and 16-char hash."""
        lesson = self._make_lesson(booking_id='same-booking', start='09:00')
        data = {
            'config': {'data_table': 'test-table'},
            'lessons': [lesson],
            'metadata': {'data_sources': {}},
        }

        self.processor.process(data)

        batch_call = self.mock_batch.put_item.call_args
        item = batch_call[1]['Item']

        # Should have versioned SK: LESSON#{timestamp}#{hash}
        self.assertTrue(item['SK'].startswith(f'LESSON#{self.TEST_TIMESTAMP}#'))
        # Extract just the hash part (after timestamp#)
        parts = item['SK'].split('#')
        lesson_id = parts[-1]  # Last part is the hash
        self.assertEqual(len(lesson_id), 16)  # MD5 truncated to 16 chars


if __name__ == '__main__':
    unittest.main()
