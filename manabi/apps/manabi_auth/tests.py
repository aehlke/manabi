from manabi.test_helpers import ManabiTestCase


class RegistrationAPITest(ManabiTestCase):
    def test_successful_registration_returns_a_token(self):
        resp = self.api.register('myname', 'mypassword')
        token = resp['auth_token']
        self.assertTrue(token)
