from restfulpy.testing.helpers import UnsafePrincipal

from staemerald.models import Client, Admin
from staemerald.tests.helpers import WebTestCase, As


class SessionsTerminateTestCase(WebTestCase):
    url = '/apiv1/sessions'

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

        client2 = Client()
        client2.email = 'client2@test.com'
        client2.password = '123456'
        client2.is_active = True
        cls.session.add(client2)

        cls.session.commit()

    def test_sessions_terminate(self):
        token1 = self.login('client1@test.com', '123456')  # Client 1
        token2 = self.login('client2@test.com', '123456')  # Client 2
        self.login('client1@test.com', '123456')

        session1_id = UnsafePrincipal.load(token1).session_id
        session2_id = UnsafePrincipal.load(token2).session_id

        # Good
        self.request(As.client, 'TERMINATE', f'{self.url}/{session1_id}')

        # Has really deleted?
        self.request(As.client, 'TERMINATE', f'{self.url}/{session1_id}', expected_status=404)

        # I won't access to client2's session
        self.request(As.client, 'TERMINATE', f'{self.url}/{session2_id}', expected_status=404)

        # And I shouldn't be authorized by `token1`
        self.wsgi_app.jwt_token = token1
        self.request(As.client, 'GET', '/apiv1/clients/me', expected_status=401, doc=False)

        # Admin is able to terminate all sessions
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'TERMINATE', f'{self.url}/{session2_id}')
