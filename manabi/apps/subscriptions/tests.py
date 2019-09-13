from manabi.test_helpers import ManabiTestCase


class SubscriptionStatusTest(ManabiTestCase):
    def test_anonymous_user(self):
        self.assertFalse(self.api.subscription_status()['active'])
