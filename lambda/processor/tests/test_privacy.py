"""
Tests for PrivacyProcessor.
"""

import unittest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.privacy import PrivacyProcessor


class TestPrivacyProcessor(unittest.TestCase):
    """Tests for PrivacyProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = PrivacyProcessor()

    def _make_lesson(self, sponsor='Test Person', participants=None):
        """Create a lesson with given sponsor and participants."""
        if participants is None:
            participants = ['Child1']
        return {
            'booking_id': 'test-123',
            'date': '28.12.2025',
            'start': '09:00',
            'end': '10:50',
            'level_key': 'test',
            'language_key': 'cz',
            'location_key': 'Stone bar',
            'sponsor': sponsor,
            'participants': participants,
            'participant_count': len(participants),
            'instructor': {'name': 'Test'},
            'notes': None,
        }

    def test_sponsor_name_filtered(self):
        """Test that sponsor name is filtered correctly."""
        data = {
            'lessons': [self._make_lesson(sponsor='Iryna Schröder')],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(result['lessons'][0]['sponsor'], 'Iryna Sc')

    def test_sponsor_multiple_names(self):
        """Test sponsor with multiple name parts."""
        data = {
            'lessons': [self._make_lesson(sponsor='Maria Anna Schmidt')],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Should use first and last parts
        self.assertEqual(result['lessons'][0]['sponsor'], 'Maria Sc')

    def test_sponsor_single_name(self):
        """Test sponsor with single name (no surname)."""
        data = {
            'lessons': [self._make_lesson(sponsor='Madonna')],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Single name returned as-is
        self.assertEqual(result['lessons'][0]['sponsor'], 'Madonna')

    def test_sponsor_short_surname(self):
        """Test sponsor with very short surname."""
        data = {
            'lessons': [self._make_lesson(sponsor='Jan Li')],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(result['lessons'][0]['sponsor'], 'Jan Li')

    def test_sponsor_empty(self):
        """Test with empty sponsor name."""
        data = {
            'lessons': [self._make_lesson(sponsor='')],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(result['lessons'][0]['sponsor'], '')

    def test_participants_unchanged(self):
        """Test that participant names are unchanged (already given names)."""
        data = {
            'lessons': [self._make_lesson(participants=['Vera', 'Eugen', 'Gerda'])],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(
            result['lessons'][0]['participants'],
            ['Vera', 'Eugen', 'Gerda']
        )

    def test_participants_whitespace_stripped(self):
        """Test that participant names have whitespace stripped."""
        data = {
            'lessons': [self._make_lesson(participants=['  Vera  ', ' Eugen'])],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(
            result['lessons'][0]['participants'],
            ['Vera', 'Eugen']
        )

    def test_empty_lessons(self):
        """Test with empty lessons list."""
        data = {
            'lessons': [],
            'metadata': {},
        }

        result = self.processor.process(data)

        self.assertEqual(result['lessons'], [])


if __name__ == '__main__':
    unittest.main()
