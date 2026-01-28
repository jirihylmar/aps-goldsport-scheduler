"""
GoldSport Scheduler - Configuration Loader

Loads configuration files from S3 website bucket.
"""

import json
import logging
from typing import Dict, Any, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

# Configuration file paths (relative to website bucket)
CONFIG_FILES = {
    'ui_translations': 'config/ui-translations.json',
    'dictionaries': 'config/dictionaries.json',
    'enrichment': 'config/enrichment.json',
}


class ConfigLoader:
    """
    Load configuration files from S3.

    Configuration files are stored in the website bucket under config/.
    """

    def __init__(self, s3_client=None):
        """
        Initialize the config loader.

        Args:
            s3_client: Optional boto3 S3 client (for testing)
        """
        self.s3 = s3_client or boto3.client('s3')
        self._cache = {}

    def load_all(self, bucket: str) -> Dict[str, Any]:
        """
        Load all configuration files.

        Args:
            bucket: S3 bucket name (website bucket)

        Returns:
            Dictionary with all configurations:
            {
                'ui_translations': {...},
                'dictionaries': {...},
                'enrichment': {...}
            }
        """
        config = {}

        for name, path in CONFIG_FILES.items():
            try:
                config[name] = self._load_json(bucket, path)
                logger.info(f"Loaded config: {path}")
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.warning(f"Config file not found: {path}")
                    config[name] = self._get_default(name)
                else:
                    logger.error(f"Error loading {path}: {e}")
                    raise
            except Exception as e:
                logger.error(f"Error parsing {path}: {e}")
                config[name] = self._get_default(name)

        return config

    def load_one(self, bucket: str, config_name: str) -> Dict[str, Any]:
        """
        Load a single configuration file.

        Args:
            bucket: S3 bucket name
            config_name: One of 'ui_translations', 'dictionaries', 'enrichment'

        Returns:
            Configuration dictionary
        """
        if config_name not in CONFIG_FILES:
            raise ValueError(f"Unknown config: {config_name}")

        path = CONFIG_FILES[config_name]

        try:
            return self._load_json(bucket, path)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.warning(f"Config file not found: {path}")
                return self._get_default(config_name)
            raise

    def _load_json(self, bucket: str, key: str) -> Dict:
        """Load and parse JSON from S3."""
        response = self.s3.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        return json.loads(content)

    def _get_default(self, name: str) -> Dict:
        """Get default values for missing config."""
        defaults = {
            'ui_translations': {
                'en': {
                    'current_lessons': 'Current Lessons',
                    'upcoming_lessons': 'Upcoming Lessons',
                    'no_lessons': 'No lessons scheduled',
                }
            },
            'dictionaries': {
                'levels': {},
                'languages': {},
                'locations': {},
            },
            'enrichment': {
                'defaults': {
                    'instructor': {
                        'id': 'goldsport-team',
                        'name': 'GoldSport Team',
                        'photo': 'assets/logo.png',
                    }
                },
                'display': {
                    'refresh_interval_seconds': 60,
                },
            },
        }
        return defaults.get(name, {})


def translate(value: str, category: str, lang: str, dictionaries: Dict) -> str:
    """
    Translate a value using dictionaries.

    Args:
        value: Raw value from data (e.g., 'dětská školka')
        category: Dictionary category ('levels', 'languages', 'locations')
        lang: Target language code ('en', 'de', 'cz', 'pl')
        dictionaries: Loaded dictionaries config

    Returns:
        Translated value, or original if not found
    """
    if not dictionaries:
        return value

    category_dict = dictionaries.get(category, {})
    value_translations = category_dict.get(value, {})

    return value_translations.get(lang, value)


def get_ui_text(key: str, lang: str, ui_translations: Dict) -> str:
    """
    Get UI text for a given key and language.

    Args:
        key: Translation key (e.g., 'current_lessons')
        lang: Language code ('en', 'de', 'cz', 'pl')
        ui_translations: Loaded UI translations config

    Returns:
        Translated text, or key if not found
    """
    if not ui_translations:
        return key

    lang_dict = ui_translations.get(lang, ui_translations.get('en', {}))
    return lang_dict.get(key, key)
