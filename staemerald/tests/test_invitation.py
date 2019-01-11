from stemerald.models import Admin, Invitation
from stemerald.tests.helpers import WebTestCase, As
from restfulpy.testing import FormParameter


class ClientActivationTestCase(WebTestCase):
    url = '/apiv1/clients/invitations'

    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        invitation1 = Invitation()
        invitation1.code = 'test-code-1'
        invitation1.total_sits = 100
        invitation1.filled_sits = 50
        cls.session.add(invitation1)

        cls.session.commit()

    def test_invitation(self):
        self.login('admin1@test.com', '123456')

        # 1. Create an invitation
        self.request(
            As.admin, 'CREATE', self.url,
            params=[
                FormParameter('code', 'test-code-2'),
                FormParameter('totalSits', 101)
            ]
        )

        # 2. Get a list of invitations
        result, ___ = self.request(As.admin, 'GET', self.url)
        self.assertEqual(len(result), 2)

        # 3. Get a specific invitation
        result, ___ = self.request(As.admin, 'GET', f'{self.url}/test-code-2')
        self.assertTrue(result['isActive'])
        self.assertEqual(result['code'], 'test-code-2')
        self.assertEqual(result['totalSits'], 101)
        self.assertEqual(result['filledSits'], 0)

        # 4. Edit an invitation
        self.request(
            As.admin, 'EDIT', f'{self.url}/test-code-1',
            params=[
                FormParameter('code', 'test-code-3'),
                FormParameter('totalSits', 1)
            ],
            expected_status=400,
            expected_headers={'x-reason': 'filled-sits-grater-than-total'}
        )

        result, ___ = self.request(
            As.admin, 'EDIT', f'{self.url}/test-code-1',
            params=[
                FormParameter('code', 'test-code-3'),
                FormParameter('totalSits', 550)
            ]
        )

        self.assertEqual(result['code'], 'test-code-3')
        self.assertEqual(result['totalSits'], 550)

        # 5. Deactivate an invitation
        result, ___ = self.request(As.admin, 'DEACTIVATE', f'{self.url}/test-code-3')
        self.assertFalse(result['isActive'])

        # 6. Activate an invitation
        result, ___ = self.request(As.admin, 'ACTIVATE', f'{self.url}/test-code-3')
        self.assertTrue(result['isActive'])
