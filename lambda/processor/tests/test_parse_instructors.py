"""
Tests for ParseInstructorsProcessor.
"""

import json
import unittest
from unittest.mock import MagicMock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.parse_instructors import ParseInstructorsProcessor, get_instructor_for_booking


SAMPLE_ROSTER = {
    "date": "2026-01-28",
    "assignments": [
        {
            "instructor_id": "jan-novak",
            "booking_ids": ["2405020a-b5a4-469e-81ab-18713fc5198a", "abc123"],
            "time_slots": [{"start": "09:00", "end": "12:00"}]
        },
        {
            "instructor_id": "petra-svoboda",
            "booking_ids": ["9ebabe94-626c-48d4-b585-531335c20e3f"],
            "time_slots": [{"start": "13:00", "end": "16:00"}]
        }
    ]
}

SAMPLE_PROFILES = {
    "jan-novak": {
        "name": "Jan Novák",
        "photo": "assets/instructors/jan-novak.jpg",
        "languages": ["cz", "de", "en"]
    },
    "petra-svoboda": {
        "name": "Petra Svobodová",
        "photo": "assets/instructors/petra-svoboda.jpg",
        "languages": ["cz", "en"]
    }
}


class TestParseInstructorsProcessor(unittest.TestCase):
    """Tests for ParseInstructorsProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_s3 = MagicMock()
        self.processor = ParseInstructorsProcessor(s3_client=self.mock_s3)

    def _mock_s3_json(self, content: dict):
        """Create mock S3 response with JSON content."""
        body = MagicMock()
        body.read.return_value = json.dumps(content).encode('utf-8')
        self.mock_s3.get_object.return_value = {'Body': body}

    def test_parse_roster_file(self):
        """Test parsing roster JSON."""
        self._mock_s3_json(SAMPLE_ROSTER)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'instructors/roster-2026-01-28.json'},
            'config': {'input_bucket': 'test-bucket'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)

        # Should have loaded roster
        self.assertIn('roster', result['raw']['instructors'])
        roster = result['raw']['instructors']['roster']
        self.assertEqual(roster['date'], '2026-01-28')
        self.assertEqual(len(roster['assignments']), 2)

    def test_parse_profiles_file(self):
        """Test parsing profiles JSON."""
        self._mock_s3_json(SAMPLE_PROFILES)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'instructors/profiles.json'},
            'config': {'input_bucket': 'test-bucket'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)

        # Should have loaded profiles
        self.assertIn('profiles', result['raw']['instructors'])
        profiles = result['raw']['instructors']['profiles']
        self.assertIn('jan-novak', profiles)
        self.assertEqual(profiles['jan-novak']['name'], 'Jan Novák')

    def test_get_instructor_for_booking(self):
        """Test helper function to find instructor."""
        instructors_data = {
            'roster': SAMPLE_ROSTER,
            'profiles': SAMPLE_PROFILES
        }

        # Test finding Jan Novák
        instructor = get_instructor_for_booking(
            instructors_data,
            '2405020a-b5a4-469e-81ab-18713fc5198a'
        )
        self.assertIsNotNone(instructor)
        self.assertEqual(instructor['name'], 'Jan Novák')
        self.assertEqual(instructor['id'], 'jan-novak')

        # Test finding Petra
        instructor = get_instructor_for_booking(
            instructors_data,
            '9ebabe94-626c-48d4-b585-531335c20e3f'
        )
        self.assertIsNotNone(instructor)
        self.assertEqual(instructor['name'], 'Petra Svobodová')

        # Test not found
        instructor = get_instructor_for_booking(
            instructors_data,
            'nonexistent-booking'
        )
        self.assertIsNone(instructor)

    def test_empty_instructors_data(self):
        """Test with empty instructor data."""
        instructor = get_instructor_for_booking({}, 'any-booking')
        self.assertIsNone(instructor)


if __name__ == '__main__':
    unittest.main()
