from restfulpy.testing.documentation import FormParameter

from staemerald.models import Client
from staemerald.tests.helpers import WebTestCase, As
from freezegun import freeze_time


class ClientLoginTestCase(WebTestCase):
    url = '/apiv1/clients/secondfactors'

    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.has_second_factor = False
        cls.session.add(client1)

        cls.session.commit()

    @freeze_time('2019-01-01')
    def test_client_login(self):
        self.login('client1@test.com', '123456')

        client = self.session.query(Client).filter(Client.email == 'client1@test.com').one()
        client.has_second_factor = True
        self.session.commit()

        # 1. Disable
        self.request(As.client, 'DISABLE', self.url)

        self.session.refresh(client)
        self.assertFalse(client.has_second_factor)

        self.request(
            None, 'POST', '/apiv1/sessions',
            params={'email': 'client1@test.com', 'password': '123456'},
            doc=False
        )

        # 2. Enable
        self.request(As.client, 'ENABLE', self.url)

        self.session.refresh(client)
        self.assertTrue(client.has_second_factor)

        self.logout()

        self.request(
            As.anonymous, 'POST', '/apiv1/sessions',
            params=[
                FormParameter('email', 'client1@test.com'),
                FormParameter('password', '123456'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-otp'},
        )

        # 3. Login with invalid otp
        self.request(
            As.anonymous, 'POST', '/apiv1/sessions',
            params=[
                FormParameter('email', 'client1@test.com'),
                FormParameter('password', '123456'),
                FormParameter('otp', '111111')
            ],
            expected_status=400,
            expected_headers={'x-reason': 'invalid-otp'},
        )

        # 4. Login with valid otp
        result, ___ = self.request(
            As.anonymous, 'POST', '/apiv1/sessions',
            params=[
                FormParameter('email', 'client1@test.com'),
                FormParameter('password', '123456'),
                FormParameter('otp', '195646')
            ],
        )
        self.wsgi_app.jwt_token = result['token']

        # It should be invalid on another time
        with freeze_time('2019-01-02'):
            self.request(
                None, 'POST', '/apiv1/sessions',
                params={'email': 'client1@test.com', 'password': '123456', 'otp': '111111'},
                expected_status=400,
                expected_headers={'x-reason': 'invalid-otp'},
                doc=False
            )

        # 5. Provision
        result, ___ = self.request(
            As.client, 'PROVISION', self.url,
            expected_headers={'content-type': 'images/png; charset=utf-8'}
        )

        self.assertIsNotNone(result)
