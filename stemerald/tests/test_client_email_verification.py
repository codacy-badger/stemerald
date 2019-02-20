from freezegun import freeze_time
from restfulpy.testing.documentation import FormParameter
from restfulpy.testing.helpers import UnsafePrincipal

from stemerald.models import Client, VerificationEmail
from stemerald.tests.helpers import WebTestCase, As


class ClientEmailVerificationTestCase(WebTestCase):
    url = '/apiv2/clients/email-verifications'

    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        client2 = Client()
        client2.email = 'client2@test.com'
        client2.password = '123456'
        client2.is_active = True
        client2.is_email_verified = True
        cls.session.add(client2)

        client3 = Client()
        client3.email = 'client3@test.com'
        client3.password = '123456'
        client3.is_active = True
        cls.session.add(client3)

        cls.session.commit()

        cls.client1_id = client1.id

    def test_client_email_verification(self):
        self.login('client1@test.com', '123456')

        self.request(As.distrusted_client, 'SCHEDULE', self.url)

        email = VerificationEmail.pop()

        self.assertEqual(email.to, 'client1@test.com')
        self.assertIn('token', email.body)

        token = email.body['token']
        principal = UnsafePrincipal.load(token)
        self.assertEqual(principal.id, self.client1_id)

        # Shouldn't work for her
        self.login('client2@test.com', '123456')
        self.request(As.semitrusted_client, 'SCHEDULE', self.url, expected_status=403)

        # It's time to verify
        # Bad token
        self.login('client1@test.com', '123456')
        self.request(
            As.distrusted_client, 'VERIFY', self.url,
            params=[FormParameter('token', 'bad')],
            expected_status=400
        )

        # Token of others
        self.login('client3@test.com', '123456')
        self.request(
            As.distrusted_client, 'VERIFY', self.url,
            params=[FormParameter('token', token)],
            expected_status=400
        )

        # Expired token
        with freeze_time("2099-01-01"):
            self.login('client1@test.com', '123456')
            self.request(
                As.distrusted_client, 'VERIFY', self.url,
                params=[FormParameter('token', token)],
                expected_status=400
            )

        # Successful verification
        self.request(As.distrusted_client, 'VERIFY', self.url, params=[FormParameter('token', token)])

        # Check
        self.login('client1@test.com', '123456')
        response, ___ = self.request(As.client, 'GET', '/apiv2/clients/me', doc=False)

        self.assertTrue(response['isEmailVerified'])
        self.assertFalse(response['isEvidenceVerified'])
