import unittest
from datetime import datetime, timezone, timedelta

from logging_helpers import get_colored_logger
from time_replacement import get_tzinfo, get_datetime_from_string

logger = get_colored_logger()


class MeetupSyncTest(unittest.TestCase):
    def test_get_tzinfo(self):
        self.assertEqual(get_tzinfo("+11").utcoffset(datetime.now()).total_seconds(), 11*60*60)
        self.assertEqual(get_tzinfo("+1100").utcoffset(datetime.now()).total_seconds(), 11 * 60 * 60)
        self.assertEqual(get_tzinfo("+5:30").utcoffset(datetime.now()).total_seconds(), 5.5 * 60 * 60)
        self.assertEqual(get_tzinfo("-4").utcoffset(datetime.now()).total_seconds(), -4 * 60 * 60)
        logger.info("Offsets have been successfully asserted")

    def test_get_datetime_from_string(self):
        time_string = "Sat, Nov 11, 2023, 4:00 PM UTC+11"
        expected = datetime(2023,11,11,16,0, tzinfo=timezone(timedelta(hours=11, minutes=0)))
        result = get_datetime_from_string(time_string)
        self.assertEqual(expected, result)
        logger.info("Successfully parsed: %s", time_string)
