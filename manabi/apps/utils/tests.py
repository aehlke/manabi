import pytz

from manabi.test_helpers import (
    ManabiTestCase,
    create_user,
)
from manabi.apps.utils.time_utils import start_and_end_of_day


class TimeUtilsTest(ManabiTestCase):
    def test_start_and_end_of_day(self):
        user = create_user()
        timezone = pytz.timezone('Etc/GMT-2')
        start, end = start_and_end_of_day(user, timezone)
        self.assertNotEqual(start, end)
