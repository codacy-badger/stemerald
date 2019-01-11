from restfulpy.testing.documentation import FormParameter

from staemerald.models import Client, Admin
from staemerald.tests.helpers import WebTestCase, As


class BankAddressTestCase(WebTestCase):
    shetab_address_url = '/apiv1/shetab-addresses'
    sheba_address_url = '/apiv1/sheba-addresses'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True

        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        client1.is_evidence_verified = True

        cls.session.add(admin1)
        cls.session.add(client1)

        cls.session.commit()

        cls.client1_id = client1.id

    def test_shetab_address(self):
        # 1. Submit an address
        self.login('client1@test.com', '123456')

        response, ___ = self.request(
            As.trusted_client, 'ADD', self.shetab_address_url,
            params=[
                FormParameter('address', '1111-2222-3333-4444'),
            ]
        )
        shetab_id = response['id']

        # 2. Reject by admin
        self.login('admin1@test.com', '123456')
        self.request(
            As.admin, 'REJECT', f'{self.shetab_address_url}/{shetab_id}',
            params=[
                FormParameter('error', 'some-error'),
            ]
        )

        # 3. Submit another
        self.login('client1@test.com', '123456')
        self.request(
            As.trusted_client, 'ADD', self.shetab_address_url,
            params=[
                FormParameter('address', '2222-3333-4444-5555'),
            ]
        )
        shetab_id = response['id']

        # 4. Accept by admin
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'ACCEPT', f'{self.shetab_address_url}/{shetab_id}')

        # 5. Can not accept or reject the address which already is accepted
        self.login('admin1@test.com', '123456')

        self.request(
            As.admin, 'REJECT', f'{self.shetab_address_url}/{shetab_id}',
            params=[
                FormParameter('error', 'some-error'),
            ],
            expected_status=409
        )
        self.request(As.admin, 'ACCEPT', f'{self.shetab_address_url}/{shetab_id}', expected_status=409)

        # 6. Get addresses by admin
        self.login('admin1@test.com', '123456')
        response, ___ = self.request(As.admin, 'GET', self.shetab_address_url, query_string={
            'clientId': self.client1_id
        })
        self.assertEqual(len(response), 2)
        self.assertIn('address', response[0])
        self.assertIn('isVerified', response[0])

        # 7. Get addresses by client
        self.login('client1@test.com', '123456')
        self.request(As.client, 'GET', self.shetab_address_url, query_string={
            'clientId': self.client1_id
        }, expected_status=400)
        response, ___ = self.request(As.client, 'GET', self.shetab_address_url)
        self.assertEqual(len(response), 2)
        self.assertIn('address', response[0])
        self.assertIn('isVerified', response[0])

    def test_sheba_address(self):
        # 1. Submit an address
        self.login('client1@test.com', '123456')

        response, ___ = self.request(
            As.trusted_client, 'ADD', self.sheba_address_url,
            params=[
                FormParameter('address', 'IR123456789012345678901234'),
            ]
        )
        sheba_id = response['id']

        # 2. Reject by admin
        self.login('admin1@test.com', '123456')
        self.request(
            As.admin, 'REJECT', f'{self.sheba_address_url}/{sheba_id}',
            params=[
                FormParameter('error', 'some-error'),
            ]
        )

        # 3. Submit another
        self.login('client1@test.com', '123456')
        self.request(
            As.trusted_client, 'ADD', self.sheba_address_url,
            params=[
                FormParameter('address', 'IR012345678901234567890123'),
            ]
        )
        sheba_id = response['id']

        # 4. Accept by admin
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'ACCEPT', f'{self.sheba_address_url}/{sheba_id}')

        # 5. Can not accept or reject the address which already is accepted
        self.login('admin1@test.com', '123456')

        self.request(
            As.admin, 'REJECT', f'{self.sheba_address_url}/{sheba_id}',
            params=[
                FormParameter('error', 'some-error'),
            ],
            expected_status=409
        )
        self.request(As.admin, 'ACCEPT', f'{self.sheba_address_url}/{sheba_id}', expected_status=409)

        # 6. Get addresses by admin
        self.login('admin1@test.com', '123456')
        response, ___ = self.request(As.admin, 'GET', self.sheba_address_url, query_string={
            'clientId': self.client1_id
        })
        self.assertEqual(len(response), 2)
        self.assertIn('address', response[0])
        self.assertIn('isVerified', response[0])

        # 7. Get addresses by client
        self.login('client1@test.com', '123456')
        self.request(As.client, 'GET', self.sheba_address_url, query_string={
            'clientId': self.client1_id
        }, expected_status=400)
        response, ___ = self.request(As.client, 'GET', self.sheba_address_url)
        self.assertEqual(len(response), 2)
        self.assertIn('address', response[0])
        self.assertIn('isVerified', response[0])
