from stemerald.models import Client
from stemerald.tests.helpers import WebTestCase, As


class SessionsGetTestCase(WebTestCase):
    url = '/apiv2/sessions'

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
        cls.session.add(client2)

        cls.session.commit()

    def test_sessions_get(self):
        self.login('client1@test.com', '123456')

        response1, ___ = self.request(As.member, 'GET', self.url)

        self.login('client1@test.com', '123456')  # Client 1
        self.login('client2@test.com', '123456')  # Client 2
        self.login('client2@test.com', '123456')  # Client 2
        self.login('client1@test.com', '123456')  # Client 1

        response2, ___ = self.request(As.member, 'GET', self.url, doc=False)

        self.assertEqual(len(response2) - len(response1), 2)
