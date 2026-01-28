"""
Tests for MergeDataProcessor.
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.merge_data import MergeDataProcessor


SAMPLE_ORDERS = [
    {
        'booking_id': '2405020a-b5a4-469e-81ab-18713fc5198a',
        'date_lesson': '28.12.2025',
        'timestamp_start': '2025-12-28T09:00:00+01:00',
        'timestamp_end': '2025-12-28T10:50:00+01:00',
        'level': 'dětská školka',
        'language': 'de',
        'location_meeting': 'Stone bar',
        'name_sponsor': 'Iryna Schröder',
        'participants': ['Vera'],
        'group_size': 1,
    },
    {
        'booking_id': 'no-instructor-booking',
        'date_lesson': '28.12.2025',
        'timestamp_start': '2025-12-28T11:00:00+01:00',
        'timestamp_end': '2025-12-28T12:50:00+01:00',
        'level': 'lyže začátečník',
        'language': 'cz',
        'location_meeting': 'Stone bar',
        'name_sponsor': 'Test Person',
        'participants': ['Child1', 'Child2'],
        'group_size': 2,
    },
]

SAMPLE_INSTRUCTORS = {
    'roster': {
        'date': '2026-01-28',
        'assignments': [
            {
                'instructor_id': 'jan-novak',
                'booking_ids': ['2405020a-b5a4-469e-81ab-18713fc5198a'],
            }
        ]
    },
    'profiles': {
        'jan-novak': {
            'name': 'Jan Novák',
            'photo': 'assets/instructors/jan-novak.jpg',
            'languages': ['cz', 'de']
        }
    }
}


class TestMergeDataProcessor(unittest.TestCase):
    """Tests for MergeDataProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = MergeDataProcessor()

    def test_merge_with_instructor(self):
        """Test merging order with instructor assignment."""
        data = {
            'raw': {
                'orders': SAMPLE_ORDERS,
                'instructors': SAMPLE_INSTRUCTORS,
            },
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Should have merged lessons
        self.assertEqual(len(result['lessons']), 2)

        # First lesson should have Jan Novák
        lesson1 = result['lessons'][0]
        self.assertEqual(lesson1['instructor']['name'], 'Jan Novák')
        self.assertEqual(lesson1['instructor']['id'], 'jan-novak')

    def test_merge_without_instructor(self):
        """Test merging order without instructor assignment uses default."""
        data = {
            'raw': {
                'orders': SAMPLE_ORDERS,
                'instructors': SAMPLE_INSTRUCTORS,
            },
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Second lesson should have default instructor
        lesson2 = result['lessons'][1]
        self.assertEqual(lesson2['instructor']['name'], 'GoldSport Team')
        self.assertIsNone(lesson2['instructor']['id'])

    def test_time_extraction(self):
        """Test that times are extracted correctly from timestamps."""
        data = {
            'raw': {
                'orders': SAMPLE_ORDERS,
                'instructors': {},
            },
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        lesson1 = result['lessons'][0]
        self.assertEqual(lesson1['start'], '09:00')
        self.assertEqual(lesson1['end'], '10:50')

    def test_lesson_fields(self):
        """Test that merged lessons have all required fields."""
        data = {
            'raw': {
                'orders': SAMPLE_ORDERS[:1],
                'instructors': SAMPLE_INSTRUCTORS,
            },
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)
        lesson = result['lessons'][0]

        required_fields = [
            'booking_id', 'date', 'start', 'end',
            'level_key', 'language_key', 'location_key',
            'sponsor', 'participants', 'participant_count',
            'instructor', 'notes'
        ]

        for field in required_fields:
            self.assertIn(field, lesson, f"Missing field: {field}")

    def test_empty_orders(self):
        """Test with empty orders."""
        data = {
            'raw': {
                'orders': [],
                'instructors': SAMPLE_INSTRUCTORS,
            },
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)
        self.assertEqual(result['lessons'], [])


if __name__ == '__main__':
    unittest.main()
