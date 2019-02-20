from stemerald.models import Client, Admin
from stemerald.tests.helpers import WebTestCase, As


class ClientActivationTestCase(WebTestCase):
    url = '/apiv2/clients'

    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        cls.session.commit()

        cls.client1_id = client1.id

    def test_client_activation(self):
        token = self.login('client1@test.com', '123456')

        # Deactivate a client
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'DEACTIVATE', f'{self.url}/{self.client1_id}')

        # She wouldn't be able to use the previous token
        self.wsgi_app.jwt_token = token
        self.request(As.client, 'GET', '/apiv2/clients/me', expected_status=401, doc=False)

        # Also she would't able to login
        self.logout()
        self.request(
            None, 'POST', '/apiv2/sessions',
            doc=False,
            params={'email': 'client1@test.com', 'password': '123456'},
            expected_status=400,
            expected_headers={'x-reason': 'account-deactivated'}
        )

        # Activate her
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'ACTIVATE', f'{self.url}/{self.client1_id}')

        # She would be able to login again
        self.login('client1@test.com', '123456')
