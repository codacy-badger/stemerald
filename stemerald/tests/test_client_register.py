from nanohttp import settings

from restfulpy.testing.documentation import FormParameter

from stemerald.tests.helpers import WebTestCase, As
from stemerald.models import ClientEvidence, Fiat, Cryptocurrency, Invitation


class ClientRegisterTestCase(WebTestCase):
    url = '/apiv2/clients'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        cls.session.add(Fiat(symbol='IRR', name='Iran Rial'))
        cls.session.add(Cryptocurrency(symbol='BTC', name='Bitcoin', wallet_id=1))
        cls.session.add(Fiat(symbol='USD', name='USA Dollar'))
        cls.session.add(Cryptocurrency(symbol='LTC', name='Litecoin', wallet_id=2))

        invitation1 = Invitation()
        invitation1.code = 'test-code-1'
        invitation1.total_sits = 2
        invitation1.filled_sits = 1
        invitation1.is_active = True
        cls.session.add(invitation1)

        invitation2 = Invitation()
        invitation2.code = 'test-code-2'
        invitation2.total_sits = 2
        invitation2.filled_sits = 1
        invitation2.is_active = False
        cls.session.add(invitation2)

        cls.session.commit()

    def test_client_register(self):
        settings.merge("""
            membership:
              invitation_code_required: false
        """)

        response, ___ = self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[FormParameter('email', 'client1@test.com'), FormParameter('password', '123456')]
        )

        self.assertIn('id', response)
        self.assertIn('email', response)
        self.assertIn('createdAt', response)
        self.assertIn('modifiedAt', response)

        self.assertTrue(response['isActive'])
        self.assertFalse(response['isEmailVerified'])
        self.assertFalse(response['isEvidenceVerified'])

        # Email already exists
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[FormParameter('email', 'client1@test.com'), FormParameter('password', '123456')],
            expected_status=409,
        )

        # Can I login?
        self.login('client1@test.com', '123456')

        # Check evidence automatic creation:
        self.assertTrue(self.session.query(ClientEvidence).filter(ClientEvidence.client_id == response['id']).count())

    def test_client_register_with_invitation_code(self):
        settings.merge("""
            membership:
              invitation_code_required: true
        """)

        # 1. Without invitation code
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[FormParameter('email', 'client2@test.com'), FormParameter('password', '123456')],
            expected_status=400,
            expected_headers={'x-reason': 'bad-invitation-code'}
        )

        # 2. With bad invitation code
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[
                FormParameter('email', 'client2@test.com'),
                FormParameter('password', '123456'),
                FormParameter('invitationCode', 'bad-invitation-code')
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-invitation-code'}
        )

        # 3. With deactivated invitation code
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[
                FormParameter('email', 'client2@test.com'),
                FormParameter('password', '123456'),
                FormParameter('invitationCode', 'test-code-2')
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-invitation-code'}
        )

        # Good invitation code
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[
                FormParameter('email', 'client2@test.com'),
                FormParameter('password', '123456'),
                FormParameter('invitationCode', 'test-code-1')
            ]
        )

        # 4. With fully-filled invitation code
        self.request(
            As.anonymous, 'REGISTER', self.url,
            params=[
                FormParameter('email', 'client3@test.com'),
                FormParameter('password', '123456'),
                FormParameter('invitationCode', 'test-code-1')
            ],
            expected_status=400,
            expected_headers={'x-reason': 'fully-filled-invitation-code'}
        )
