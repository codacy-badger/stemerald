from restfulpy.testing import FormParameter
from restfulpy.testing.helpers import UnsafePrincipal

from stemerald.models import Client, ResetPasswordEmail
from stemerald.tests.helpers import WebTestCase, As


class ClientActivationTestCase(WebTestCase):
    url = '/apiv1/clients/passwords'

    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        cls.session.commit()

        cls.client1_id = client1.id

    def test_client_activation(self):
        self.login('client1@test.com', '123456')

        # 1. change the password
        self.request(As.client, 'CHANGE', self.url, params=[
            FormParameter('currentPassword', '123456'),
            FormParameter('newPassword', '654321'),
        ])

        # Should not be  authorized
        self.request(None, 'GET', '/apiv1/clients', doc=False, expected_status=401)

        # Should not be able to login
        self.logout()
        self.request(None, 'POST', '/apiv1/sessions', doc=False, params={
            'email': 'client1@test.com',
            'password': '123456'
        }, expected_status=400)

        # Can login with new password
        self.request(None, 'POST', '/apiv1/sessions', doc=False, params={
            'email': 'client1@test.com',
            'password': '654321'
        })

        # 2. Schedule a reset password token
        self.logout()
        self.request(As.anonymous, 'SCHEDULE', self.url, params=[
            FormParameter('email', 'client1@test.com')
        ])

        email = ResetPasswordEmail.pop()
        self.assertEqual(email.to, 'client1@test.com')
        self.assertIn('token', email.body)
        token = email.body['token']
        # FIXME: This is not good:
        principal = UnsafePrincipal.load(token.replace(token.split('.')[1], '%s=' % token.split('.')[1]))
        self.assertEqual(principal.email, 'client1@test.com')

        # 3. Reset password using token
        self.request(As.anonymous, 'RESET', self.url, params=[
            FormParameter('token', token),
            FormParameter('password', '654456'),
        ])

        # Should not be able to login
        self.logout()
        self.request(None, 'POST', '/apiv1/sessions', doc=False, params={
            'email': 'client1@test.com',
            'password': '654321'
        }, expected_status=400)

        # Can login with new password
        self.request(None, 'POST', '/apiv1/sessions', doc=False, params={
            'email': 'client1@test.com',
            'password': '654456'
        })
