from restfulpy.testing.documentation import FormParameter

from stemerald.models import Client, Admin, Fiat
from stemerald.tests.helpers import WebTestCase, As


class BankAddressTestCase(WebTestCase):
    bank_cards_url = '/apiv2/banking/cards'
    bank_accounts_url = '/apiv2/banking/accounts'

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

        usd = Fiat(symbol='usd', name='USA Dollar')

        cls.session.add(usd)

        cls.session.commit()

        cls.client1_id = client1.id

    def test_bank_cards(self):
        # 1. Submit a card
        self.login('client1@test.com', '123456')

        response, ___ = self.request(
            As.trusted_client, 'ADD', self.bank_cards_url,
            params=[
                FormParameter('fiatSymbol', 'usd'),
                FormParameter('holder', 'Test Test'),
                FormParameter('pan', '1111-2222-3333-4444'),
            ]
        )
        bank_card_id = response['id']

        # 2. Reject by admin
        self.login('admin1@test.com', '123456')
        self.request(
            As.admin, 'REJECT', f'{self.bank_cards_url}/{bank_card_id}',
            params=[
                FormParameter('error', 'some-error'),
            ]
        )

        # 3. Submit another
        self.login('client1@test.com', '123456')
        self.request(
            As.trusted_client, 'ADD', self.bank_cards_url,
            params=[
                FormParameter('fiatSymbol', 'usd'),
                FormParameter('holder', 'Another Test'),
                FormParameter('pan', '2222-3333-4444-5555'),
            ]
        )
        bank_card_id = response['id']

        # 4. Accept by admin
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'ACCEPT', f'{self.bank_cards_url}/{bank_card_id}')

        # 5. Can not accept or reject the card which already is accepted
        self.login('admin1@test.com', '123456')

        self.request(
            As.admin, 'REJECT', f'{self.bank_cards_url}/{bank_card_id}',
            params=[
                FormParameter('error', 'some-error'),
            ],
            expected_status=409
        )
        self.request(As.admin, 'ACCEPT', f'{self.bank_cards_url}/{bank_card_id}', expected_status=409)

        # 6. Get cards by admin
        self.login('admin1@test.com', '123456')
        response, ___ = self.request(As.admin, 'GET', self.bank_cards_url, query_string={
            'clientId': self.client1_id
        })
        self.assertEqual(len(response), 2)
        self.assertIn('fiatSymbol', response[0])
        self.assertIn('holder', response[0])
        self.assertIn('pan', response[0])
        self.assertIn('isVerified', response[0])

        # 7. Get cards by client
        self.login('client1@test.com', '123456')
        self.request(As.client, 'GET', self.bank_cards_url, query_string={
            'clientId': self.client1_id
        }, expected_status=400)
        response, ___ = self.request(As.client, 'GET', self.bank_cards_url)
        self.assertEqual(len(response), 2)
        self.assertIn('fiatSymbol', response[0])
        self.assertIn('holder', response[0])
        self.assertIn('pan', response[0])
        self.assertIn('isVerified', response[0])

    def test_bank_accounts(self):
        # 1. Submit an account
        self.login('client1@test.com', '123456')

        response, ___ = self.request(
            As.trusted_client, 'ADD', self.bank_accounts_url,
            params=[
                FormParameter('fiatSymbol', 'usd'),
                FormParameter('iban', 'IR123456789012345678901234'),
                FormParameter('owner', 'Test Test'),
            ]
        )
        bank_account_id = response['id']

        # 2. Reject by admin
        self.login('admin1@test.com', '123456')
        self.request(
            As.admin, 'REJECT', f'{self.bank_accounts_url}/{bank_account_id}',
            params=[
                FormParameter('error', 'some-error'),
            ]
        )

        # 3. Submit another
        self.login('client1@test.com', '123456')
        self.request(
            As.trusted_client, 'ADD', self.bank_accounts_url,
            params=[
                FormParameter('fiatSymbol', 'usd'),
                FormParameter('iban', 'IR012345678901234567890123'),
                FormParameter('owner', 'Another Test'),
            ]
        )
        bank_account_id = response['id']

        # 4. Accept by admin
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'ACCEPT', f'{self.bank_accounts_url}/{bank_account_id}')

        # 5. Can not accept or reject the account which already is accepted
        self.login('admin1@test.com', '123456')

        self.request(
            As.admin, 'REJECT', f'{self.bank_accounts_url}/{bank_account_id}',
            params=[
                FormParameter('error', 'some-error'),
            ],
            expected_status=409
        )
        self.request(As.admin, 'ACCEPT', f'{self.bank_accounts_url}/{bank_account_id}', expected_status=409)

        # 6. Get accounts by admin
        self.login('admin1@test.com', '123456')
        response, ___ = self.request(As.admin, 'GET', self.bank_accounts_url, query_string={
            'clientId': self.client1_id
        })
        self.assertEqual(len(response), 2)
        self.assertIn('iban', response[0])
        self.assertIn('bic', response[0])
        self.assertIn('fiatSymbol', response[0])
        self.assertIn('owner', response[0])
        self.assertIn('isVerified', response[0])

        # 7. Get accounts by client
        self.login('client1@test.com', '123456')
        self.request(As.client, 'GET', self.bank_accounts_url, query_string={
            'clientId': self.client1_id
        }, expected_status=400)
        response, ___ = self.request(As.client, 'GET', self.bank_accounts_url)
        self.assertEqual(len(response), 2)
        self.assertIn('fiatSymbol', response[0])
        self.assertIn('iban', response[0])
        self.assertIn('bic', response[0])
        self.assertIn('owner', response[0])
        self.assertIn('isVerified', response[0])
