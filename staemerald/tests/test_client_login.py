from restfulpy.testing.documentation import FormParameter

from staemerald.models import Client
from staemerald.tests.helpers import WebTestCase, As


class ClientLoginTestCase(WebTestCase):
    url = '/apiv1/sessions'

    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        cls.session.commit()

    def test_client_login(self):
        # Bad
        self.request(
            As.anonymous, 'POST', self.url,
            params=[FormParameter('email', 'bad@test.com'), FormParameter('password', '123456')],
            expected_status=400
        )

        self.request(
            As.anonymous, 'POST', self.url,
            params=[FormParameter('email', 'client1@test.com'), FormParameter('password', 'bad')],
            expected_status=400
        )

        # Good
        response, ___ = self.request(
            As.anonymous, 'POST', self.url,
            params=[FormParameter('email', 'client1@test.com'), FormParameter('password', '123456')]
        )

        self.assertIn('token', response)

        # Testing the token
        self.wsgi_app.jwt_token = response['token']
        self.request(As.client, 'GET', '/apiv1/clients/me', doc=False)
