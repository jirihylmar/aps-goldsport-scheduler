"""
Tests for ConfigLoader.
"""

import unittest
from unittest.mock import MagicMock, patch
import json
import io

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config_loader import ConfigLoader, translate, get_ui_text


class TestConfigLoader(unittest.TestCase):
    """Tests for ConfigLoader."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_s3 = MagicMock()
        self.loader = ConfigLoader(s3_client=self.mock_s3)

    def _mock_s3_response(self, content: dict):
        """Create a mock S3 get_object response."""
        body = MagicMock()
        body.read.return_value = json.dumps(content).encode('utf-8')
        return {'Body': body}

    def test_load_all_success(self):
        """Test loading all config files successfully."""
        self.mock_s3.get_object.side_effect = [
            self._mock_s3_response({'en': {'key': 'value'}}),
            self._mock_s3_response({'levels': {}}),
            self._mock_s3_response({'defaults': {}}),
        ]

        result = self.loader.load_all('test-bucket')

        self.assertIn('ui_translations', result)
        self.assertIn('dictionaries', result)
        self.assertIn('enrichment', result)
        self.assertEqual(self.mock_s3.get_object.call_count, 3)

    def test_load_one_success(self):
        """Test loading a single config file."""
        self.mock_s3.get_object.return_value = self._mock_s3_response(
            {'levels': {'test': {'en': 'Test'}}}
        )

        result = self.loader.load_one('test-bucket', 'dictionaries')

        self.assertIn('levels', result)
        self.mock_s3.get_object.assert_called_once_with(
            Bucket='test-bucket',
            Key='config/dictionaries.json'
        )

    def test_load_one_unknown_config(self):
        """Test error on unknown config name."""
        with self.assertRaises(ValueError) as ctx:
            self.loader.load_one('test-bucket', 'unknown')

        self.assertIn('Unknown config', str(ctx.exception))

    def test_missing_config_returns_default(self):
        """Test that missing config returns default values."""
        from botocore.exceptions import ClientError
        error = ClientError(
            {'Error': {'Code': 'NoSuchKey', 'Message': 'Not found'}},
            'GetObject'
        )
        self.mock_s3.get_object.side_effect = error

        result = self.loader.load_one('test-bucket', 'dictionaries')

        # Should return default
        self.assertIn('levels', result)
        self.assertIn('languages', result)
        self.assertIn('locations', result)


class TestTranslate(unittest.TestCase):
    """Tests for translate helper function."""

    def setUp(self):
        """Set up test dictionaries."""
        self.dictionaries = {
            'levels': {
                'dětská školka': {
                    'en': 'Kids Ski School',
                    'de': 'Kinderskischule',
                    'cz': 'Dětská školka',
                    'pl': 'Przedszkole narciarskie',
                }
            },
            'languages': {
                'de': {
                    'en': 'German',
                    'de': 'Deutsch',
                }
            },
        }

    def test_translate_level_to_english(self):
        """Test translating level to English."""
        result = translate('dětská školka', 'levels', 'en', self.dictionaries)
        self.assertEqual(result, 'Kids Ski School')

    def test_translate_level_to_german(self):
        """Test translating level to German."""
        result = translate('dětská školka', 'levels', 'de', self.dictionaries)
        self.assertEqual(result, 'Kinderskischule')

    def test_translate_unknown_value(self):
        """Test that unknown value returns original."""
        result = translate('unknown level', 'levels', 'en', self.dictionaries)
        self.assertEqual(result, 'unknown level')

    def test_translate_unknown_category(self):
        """Test that unknown category returns original."""
        result = translate('test', 'unknown', 'en', self.dictionaries)
        self.assertEqual(result, 'test')

    def test_translate_with_empty_dictionaries(self):
        """Test that empty dictionaries returns original."""
        result = translate('test', 'levels', 'en', {})
        self.assertEqual(result, 'test')

    def test_translate_with_none_dictionaries(self):
        """Test that None dictionaries returns original."""
        result = translate('test', 'levels', 'en', None)
        self.assertEqual(result, 'test')


class TestGetUiText(unittest.TestCase):
    """Tests for get_ui_text helper function."""

    def setUp(self):
        """Set up test UI translations."""
        self.ui = {
            'en': {
                'current_lessons': 'Current Lessons',
                'upcoming_lessons': 'Upcoming Lessons',
            },
            'de': {
                'current_lessons': 'Aktuelle Kurse',
                'upcoming_lessons': 'Kommende Kurse',
            },
        }

    def test_get_english_text(self):
        """Test getting English UI text."""
        result = get_ui_text('current_lessons', 'en', self.ui)
        self.assertEqual(result, 'Current Lessons')

    def test_get_german_text(self):
        """Test getting German UI text."""
        result = get_ui_text('current_lessons', 'de', self.ui)
        self.assertEqual(result, 'Aktuelle Kurse')

    def test_unknown_key_returns_key(self):
        """Test that unknown key returns the key itself."""
        result = get_ui_text('unknown_key', 'en', self.ui)
        self.assertEqual(result, 'unknown_key')

    def test_unknown_language_falls_back_to_english(self):
        """Test that unknown language falls back to English."""
        result = get_ui_text('current_lessons', 'fr', self.ui)
        self.assertEqual(result, 'Current Lessons')

    def test_empty_translations_returns_key(self):
        """Test that empty translations returns key."""
        result = get_ui_text('test', 'en', {})
        self.assertEqual(result, 'test')


if __name__ == '__main__':
    unittest.main()
