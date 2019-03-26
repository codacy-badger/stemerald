import ujson
from decimal import Decimal

from restfulpy.testing import FormParameter

from stemerald.models import Client, BankAccount, Admin, Fiat, PaymentGateway
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As

cashout_min = '1000'
cashout_max = '599000'
cashout_static_commission = '129'
cashout_commission_rate = '0.023'
cashout_max_commission = '746'

mockup_transaction_id = '4738'
mockup_amount = '4576'


class TransactionShaparakInTestCase(WebTestCase):
    url = '/apiv2/transactions/shaparak-outs'

    # noinspection PyArgumentList
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
        client1.is_email_verified = True
        client1.is_evidence_verified = True
        cls.session.add(client1)

        client2 = Client()
        client2.email = 'client2@test.com'
        client2.password = '123456'
        client2.is_active = True
        client2.is_email_verified = True
        client2.is_evidence_verified = True
        cls.session.add(client2)

        irr = Fiat(
            symbol='IRR',
            name='Iran Rial',
        )
        cls.session.add(irr)

        # Adding a payment gateway
        shaparak = PaymentGateway()
        shaparak.name = "shaparak"
        shaparak.fiat_symbol = "IRR"
        shaparak.cashout_min = cashout_min
        shaparak.cashout_max = cashout_max
        shaparak.cashout_static_commission = cashout_static_commission
        shaparak.cashout_commission_rate = cashout_commission_rate
        shaparak.cashout_max_commission = cashout_max_commission
        cls.session.add(shaparak)

        # Mine, verified:
        sheba_address_1 = BankAccount()
        sheba_address_1.iban = 'IR123456789123456789123456'
        sheba_address_1.owner = "Client One"
        sheba_address_1.client = client1
        sheba_address_1.fiat_symbol = "IRR"
        sheba_address_1.is_verified = True

        # Mine, unverified:
        sheba_address_2 = BankAccount()
        sheba_address_2.iban = 'IR837498056254698443242343'
        sheba_address_2.owner = "Client One"
        sheba_address_2.client = client1
        sheba_address_2.fiat_symbol = "IRR"
        sheba_address_2.is_verified = False

        # Other's, verified:
        sheba_address_3 = BankAccount()
        sheba_address_3.iban = 'IR837498056254698443242343'
        sheba_address_3.owner = "Client Two"
        sheba_address_3.client = client2
        sheba_address_3.fiat_symbol = "IRR"
        sheba_address_3.is_verified = True

        for address in [sheba_address_1, sheba_address_2, sheba_address_3]:
            cls.session.add(address)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id

        cls.mockup_sheba_address_verified_id = sheba_address_1.id
        cls.mockup_sheba_address_unverified_id = sheba_address_2.id
        cls.mockup_sheba_address_others_id = sheba_address_3.id
        cls.mockup_payment_gateway_name = shaparak.name

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)
                self.mock_balance = ["3001", "0"]

            def asset_list(self):
                return ujson.loads('[{"name": "IRR", "prec": 2}]')

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if user_id == cls.mockup_client_1_id and business in ['cashout', 'cashback'] and asset == 'IRR':
                    self.mock_balance[0] = '{:.8f}'.format(Decimal(change) + Decimal(self.mock_balance[0]))
                return ujson.loads(
                    '{"IRR": {"available": "' +
                    self.mock_balance[0] +
                    '", "freeze": "' +
                    self.mock_balance[1] +
                    '"}}'
                )

            def balance_query(self, *args, **kwargs):
                return ujson.loads(
                    '{"IRR": {"available": "' +
                    self.mock_balance[0] +
                    '", "freeze": "' +
                    self.mock_balance[1] +
                    '"}}'
                )

        stexchange_client._set_instance(MockStexchangeClient())

    def test_transaction_deposit_create(self):
        self.login('client1@test.com', '123456')

        # 1. Schedule an Shaparak-Out transaction (another's sheba address)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '2000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_others_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=400)

        # 2. Schedule an Shaparak-Out transaction (unverified sheba address)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '2000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_unverified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=409)

        # 3. Schedule an Shaparak-Out transaction (less than minimum or more than max)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '1', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=400)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '99999999999', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=400)

        # 4. Schedule an Shaparak-Out transaction (more than balance)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '599000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=400)

        # 4. Schedule an Shaparak-Out transaction (amount < balance < amount + commission)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '3000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ], expected_status=400)

        # 5. Schedule an Shaparak-Out transaction (everything is good)
        result, ___ = self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '2000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ])

        transaction_id = result['id']

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']), Decimal(826))
        self.assertEqual(Decimal(balance['freeze']), Decimal(0))

        # 6. Reject the Shaparak-Out request
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ])

        # Already rejected
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ], expected_status=400)
        self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '6786543'),
        ], expected_status=400)

        self.assertIsNone(result['referenceId'])

        # Check balance (cash back without commission)
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']), Decimal(2826))
        self.assertEqual(Decimal(balance['freeze']), Decimal(0))

        # 7. Accept the Shaparak-Out request ()
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', '2000', type_=str),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ])
        transaction_id = result['id']
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '3874948957'),
        ])

        # Already accepted
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ], expected_status=400)
        self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '45598'),
        ], expected_status=400)

        self.assertIsNotNone(result['referenceId'])

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']), Decimal(651))
        self.assertEqual(Decimal(balance['freeze']), Decimal(0))
