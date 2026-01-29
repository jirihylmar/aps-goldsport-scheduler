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

    def _make_lesson(self, sponsor='Test Person', people=None):
        """Create a lesson with given sponsor and people."""
        if people is None:
            people = [{'name': 'Child1', 'language': 'cz', 'sponsor': sponsor}]
        return {
            'booking_id': 'test-123',
            'date': '28.12.2025',
            'start': '09:00',
            'end': '10:50',
            'level_key': 'test',
            'group_type_key': 'privát',
            'location_key': 'Stone bar',
            'sponsor': sponsor,  # Legacy field, may still be used
            'people': people,
            'people_count': len(people),
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

        # Privacy filter abbreviates: "Iryna Schröder" -> "Ir.Sc."
        self.assertEqual(result['lessons'][0]['sponsor'], 'Ir.Sc.')
        # Also verify people array has filtered sponsor
        self.assertEqual(result['lessons'][0]['people'][0]['sponsor'], 'Ir.Sc.')

    def test_sponsor_multiple_names(self):
        """Test sponsor with multiple name parts."""
        data = {
            'lessons': [self._make_lesson(sponsor='Maria Anna Schmidt')],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Should use first and last parts: "Ma.Sc."
        self.assertEqual(result['lessons'][0]['sponsor'], 'Ma.Sc.')

    def test_sponsor_single_name(self):
        """Test sponsor with single name (no surname)."""
        data = {
            'lessons': [self._make_lesson(sponsor='Madonna')],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Single name gets abbreviated: "Madonna" -> "Ma."
        self.assertEqual(result['lessons'][0]['sponsor'], 'Ma.')

    def test_sponsor_short_surname(self):
        """Test sponsor with very short surname."""
        data = {
            'lessons': [self._make_lesson(sponsor='Jan Li')],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Short surname still gets abbreviated: "Jan Li" -> "Ja.Li."
        self.assertEqual(result['lessons'][0]['sponsor'], 'Ja.Li.')

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
        people = [
            {'name': 'Vera', 'language': 'de', 'sponsor': 'Test'},
            {'name': 'Eugen', 'language': 'de', 'sponsor': 'Test'},
            {'name': 'Gerda', 'language': 'de', 'sponsor': 'Test'},
        ]
        data = {
            'lessons': [self._make_lesson(people=people)],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Names should be unchanged, sponsors abbreviated
        names = [p['name'] for p in result['lessons'][0]['people']]
        self.assertEqual(names, ['Vera', 'Eugen', 'Gerda'])

    def test_participants_whitespace_stripped(self):
        """Test that participant names have whitespace stripped."""
        people = [
            {'name': '  Vera  ', 'language': 'de', 'sponsor': 'Test'},
            {'name': ' Eugen', 'language': 'de', 'sponsor': 'Test'},
        ]
        data = {
            'lessons': [self._make_lesson(people=people)],
            'metadata': {},
        }

        result = self.processor.process(data)

        # Names should have whitespace stripped
        names = [p['name'] for p in result['lessons'][0]['people']]
        self.assertEqual(names, ['Vera', 'Eugen'])

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
