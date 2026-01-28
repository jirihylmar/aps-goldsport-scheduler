"""
GoldSport Scheduler - Privacy Processor

Applies privacy rules to names for public display.
"""

import logging
from typing import Dict, Any

from processors import Processor, ProcessorError

logger = logging.getLogger(__name__)


class PrivacyProcessor(Processor):
    """
    Apply privacy rules to names.

    Rules:
    - Sponsor name: given name + first 2 letters of surname
      Example: "Iryna Schröder" -> "Iryna Sc"
    - Participant name: use as-is (already given name only in source data)
    """

    def process(self, data: dict) -> dict:
        """
        Apply privacy transformations to lesson records.

        Args:
            data: Pipeline data with lessons

        Returns:
            Data with privacy-filtered names
        """
        lessons = data.get('lessons', [])

        if not lessons:
            logger.info("No lessons to process for privacy")
            return data

        try:
            for lesson in lessons:
                # Transform sponsor name
                original_sponsor = lesson.get('sponsor', '')
                lesson['sponsor'] = self._filter_sponsor_name(original_sponsor)

                # Participants: each has {name, language, sponsor}
                # Names are already given names only - no transformation needed
                # Sponsor names need privacy filtering
                participants = lesson.get('participants', [])
                filtered_participants = []
                for p in participants:
                    if isinstance(p, dict):
                        # New format with language and sponsor
                        sponsor_filtered = self._filter_sponsor_name(p.get('sponsor', ''))
                        filtered_participants.append({
                            'name': str(p.get('name', '')).strip(),
                            'language': str(p.get('language', '')).strip(),
                            'sponsor': sponsor_filtered,
                        })
                    elif p:
                        # Legacy string format
                        filtered_participants.append({
                            'name': str(p).strip(),
                            'language': '',
                            'sponsor': '',
                        })
                lesson['participants'] = filtered_participants

            logger.info(f"Applied privacy rules to {len(lessons)} lessons")

        except Exception as e:
            raise ProcessorError(self.name, f"Failed to apply privacy rules: {e}", e)

        return data

    def _filter_sponsor_name(self, name: str) -> str:
        """
        Filter sponsor name for privacy.

        Keeps: given name + first 2 letters of surname
        Example: "Iryna Schröder" -> "Iryna Sc"

        Args:
            name: Full sponsor name

        Returns:
            Privacy-filtered name
        """
        if not name:
            return ''

        name = name.strip()
        parts = name.split()

        if len(parts) == 0:
            return ''

        if len(parts) == 1:
            # Only one name part - return as-is
            return parts[0]

        # Given name (first part) + first 2 letters of surname (last part)
        given_name = parts[0]
        surname = parts[-1]

        # Handle short surnames
        surname_abbrev = surname[:2] if len(surname) >= 2 else surname

        return f"{given_name} {surname_abbrev}"
