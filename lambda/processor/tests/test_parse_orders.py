"""
Tests for ParseOrdersProcessor.
"""

import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processors.parse_orders import ParseOrdersProcessor


SAMPLE_TSV = """id_order\tdate_order\tcontact_sales\tlocation_meeting\tseason\tlevel\tgroup_size\tparticipants\tlanguage\tname_sponsor\tname_participant\tage_participant\tdate_lesson\ttimestamp_start_lesson\ttimestamp_end_lesson\tprice_currency\tprice_discount_percent\tprice_without_vat\tprice_to_pay\tnote\tbooking_id
4151\t2025-12-27\tMartin Hrubý\tStone bar\t25/26\tdětská školka\t2\t2\tde\tIryna Schröder\tVera\t7\t28.12.2025\t2025-12-28T09:00:00+01:00\t2025-12-28T10:50:00+01:00\tCZK\t3\t5743.8\t6950.00\t+491745174831\t2405020a-b5a4-469e-81ab-18713fc5198a
4152\t2025-12-27\tMartin Hrubý\tStone bar\t25/26\tdětská školka\t2\t2\tde\tIryna Schröder\tEugen\t10\t28.12.2025\t2025-12-28T09:00:00+01:00\t2025-12-28T10:50:00+01:00\tCZK\t3\t5743.8\t6950.00\t+491745174831\t9ebabe94-626c-48d4-b585-531335c20e3f
4153\t2025-12-27\tMartin Hrubý\tStone bar\t25/26\tdětská školka\t1\t1\tde\tIryna Schröder\tGerda\t5\t28.12.2025\t2025-12-28T09:00:00+01:00\t2025-12-28T10:50:00+01:00\tCZK\t3\t5743.8\t6950.00\t+491745174831\t
4159\t2025-12-27\tTest\tStone bar\t25/26\tlyže začátečník\t0\t0\tcz\tbbbb\t\t\t01.01.1970\t1970-01-01T:00+01:00\t1970-01-01T:00+01:00\tCZK\t100\t1975.21\t2390.00\t444454451\t"""


class TestParseOrdersProcessor(unittest.TestCase):
    """Tests for ParseOrdersProcessor."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_s3 = MagicMock()
        self.processor = ParseOrdersProcessor(s3_client=self.mock_s3)

    def _mock_s3_response(self, content: str):
        """Create mock S3 response with given content."""
        body = MagicMock()
        body.read.return_value = content.encode('utf-8')
        self.mock_s3.get_object.return_value = {'Body': body}

    def test_parse_orders_basic(self):
        """Test basic TSV parsing."""
        self._mock_s3_response(SAMPLE_TSV)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'orders/test.tsv'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)

        # Should have parsed orders
        self.assertIn('orders', result['raw'])
        orders = result['raw']['orders']
        self.assertGreater(len(orders), 0)

    def test_filters_1970_dates(self):
        """Test that 1970 dates are filtered out."""
        self._mock_s3_response(SAMPLE_TSV)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'orders/test.tsv'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)
        orders = result['raw']['orders']

        # None of the orders should have 1970 dates
        for order in orders:
            self.assertNotIn('1970', order['date_lesson'])
            self.assertNotIn('1970', order['timestamp_start'])

    def test_groups_by_booking_id(self):
        """Test that records are grouped by booking_id."""
        self._mock_s3_response(SAMPLE_TSV)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'orders/test.tsv'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)
        orders = result['raw']['orders']

        # Find the order with booking_id 2405020a-...
        vera_booking = None
        for order in orders:
            if order.get('booking_id') == '2405020a-b5a4-469e-81ab-18713fc5198a':
                vera_booking = order
                break

        # Should exist and have Vera as participant
        self.assertIsNotNone(vera_booking)
        self.assertIn('Vera', vera_booking['participants'])

    def test_skips_non_orders_files(self):
        """Test that non-orders files are skipped."""
        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'instructors/roster.json'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)

        # Should not have called S3
        self.mock_s3.get_object.assert_not_called()
        # Orders should still be empty
        self.assertEqual(result['raw']['orders'], [])

    def test_required_fields_present(self):
        """Test that parsed orders have required fields."""
        self._mock_s3_response(SAMPLE_TSV)

        data = {
            'trigger': {'bucket': 'test-bucket', 'key': 'orders/test.tsv'},
            'raw': {'orders': [], 'instructors': {}, 'overrides': []},
            'metadata': {'data_sources': {}, 'processing_errors': []},
        }

        result = self.processor.process(data)
        orders = result['raw']['orders']

        required_fields = [
            'date_lesson', 'timestamp_start', 'timestamp_end',
            'level', 'language', 'location_meeting',
            'name_sponsor', 'participants'
        ]

        for order in orders:
            for field in required_fields:
                self.assertIn(field, order, f"Missing field: {field}")


if __name__ == '__main__':
    unittest.main()
