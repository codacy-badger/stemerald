import ujson
from decimal import Decimal

from nanohttp import settings

from stemerald import stexchange_client
from stemerald.models import Client, Fiat, BankCard, PaymentGateway
from stemerald.shaparak import ShaparakProvider, ShaparakError
from stemerald.stexchange import StexchangeClient
from stemerald.tests.helpers import WebTestCase, As
from restfulpy.testing import FormParameter

cashin_min = Decimal('200').scaleb(5)
cashin_max = Decimal('0').scaleb(5)
cashin_static_commission = Decimal('43').scaleb(5)
cashin_commission_rate = '0.123'
cashin_max_commission = Decimal('897').scaleb(5)

mockup_transaction_id = '4738'
mockup_amount = '4576.000'
mockup_card_address = '6473-7563-8264-1092'
is_transaction_verified = [False, True, True]


class MockupShaparakProvider(ShaparakProvider):
    def create_transaction(self, batch_id, amount):
        return mockup_transaction_id

    def verify_transaction(self, transaction_id):
        if is_transaction_verified.pop(0):
            return mockup_amount, None, None
        raise ShaparakError(None)


class TransactionShaparakInTestCase(WebTestCase):
    url = '/apiv2/transactions/shaparak-ins'

    is_shaparak_transaction_verified = False

    @classmethod
    def configure_app(cls):
        super().configure_app()
        settings.merge("""
        
        shaparak:
          provider: stemerald.tests.test_transaction_shaparak_in.MockupShaparakProvider
          
          pay_ir:
            post_redirect_url: http://stacrypt.io/apiv2/transactions/shaparak-ins/pay-irs
            result_redirect_url: http://stacrypt.io/payment_redirect

          
        """)

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        client1.is_evidence_verified = True
        cls.session.add(client1)

        irr = Fiat(
            symbol='IRR',
            name='Iran Rial',
            normalization_scale=-5,
            smallest_unit_scale=-3,
        )
        cls.session.add(irr)

        # Adding a payment gateway
        shaparak = PaymentGateway()
        shaparak.name = "shaparak"
        shaparak.fiat_symbol = "IRR"
        shaparak.cashin_min = cashin_min
        shaparak.cashin_max = cashin_max
        shaparak.cashin_static_commission = cashin_static_commission
        shaparak.cashin_commission_rate = cashin_commission_rate
        shaparak.cashin_max_commission = cashin_max_commission
        cls.session.add(shaparak)

        shetab_address_1 = BankCard()
        shetab_address_1.pan = mockup_card_address
        shetab_address_1.holder = "Test Tester"
        shetab_address_1.client = client1
        shetab_address_1.fiat_symbol = "IRR"
        shetab_address_1.is_verified = True

        cls.session.add(shetab_address_1)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id
        cls.mockup_shetab_address_1_id = shetab_address_1.id
        cls.mockup_payment_gateway_name = shaparak.name

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)
                self.mock_balance = ["0", "0"]

            def asset_list(self):
                return ujson.loads('[{"name": "IRR", "prec": 2}]')

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if user_id == cls.mockup_client_1_id and business == 'cashin' and asset == 'IRR':
                    self.mock_balance[0] = '{:.8f}'.format(Decimal(self.mock_balance[0]) + Decimal(change))
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

    def test_shaparak_in_create(self):
        self.login('client1@test.com', '123456')

        # 1. Create an Shaparak-In transaction
        result, ___ = self.request(As.trusted_client, 'CREATE', self.url, params=[
            FormParameter('amount', mockup_amount, type_=str),
            FormParameter('shetabAddressId', self.mockup_shetab_address_1_id),
            FormParameter('paymentGatewayName', self.mockup_payment_gateway_name),
        ])

        self.assertIn('id', result)
        self.assertIn('transactionId', result)
        self.assertIn('paymentGateway', result)
        self.assertIn('bankingId', result)
        self.assertIn('referenceId', result)

        transaction_id = result['id']

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']).scaleb(-5), Decimal(0))
        self.assertEqual(Decimal(balance['freeze']).scaleb(-5), Decimal(0))

        self.logout()

        # 2. Verify the transaction (Not completed yet)
        self.request(
            As.anonymous, 'POST', f'{self.url}/pay-irs',
            params=[
                FormParameter('status', 1),
                FormParameter('transId', mockup_transaction_id),
                FormParameter('factorNumber', transaction_id),
                FormParameter('mobile', ''),
                FormParameter('description', 0),
                FormParameter('cardNumber', '647375******1092'),
                FormParameter('traceNumber', '123456'),
                FormParameter('message', 0),
            ],
            expected_status=302,
            expected_headers={
                'Location': 'http://stacrypt.io/payment_redirect?result=not-verified'
            }
        )

        # 3. Verify the transaction (Bad card)
        self.logout()
        self.request(
            As.anonymous, 'POST', f'{self.url}/pay-irs',
            params=[
                FormParameter('status', 1),
                FormParameter('transId', mockup_transaction_id),
                FormParameter('factorNumber', transaction_id),
                FormParameter('mobile', ''),
                FormParameter('description', 0),
                FormParameter('cardNumber', '000000******0000'),
                FormParameter('traceNumber', '123456'),
                FormParameter('message', 0),
            ],
            expected_status=302,
            expected_headers={
                'Location': 'http://stacrypt.io/payment_redirect?result=bad-card'
            }
        )

        # 4. Verify the transaction (Should be verified)
        self.request(
            As.anonymous, 'POST', f'{self.url}/pay-irs',
            params=[
                FormParameter('status', 1),
                FormParameter('transId', mockup_transaction_id),
                FormParameter('factorNumber', transaction_id),
                FormParameter('mobile', ''),
                FormParameter('description', 0),
                FormParameter('cardNumber', '647375******1092'),
                FormParameter('traceNumber', '123456'),
                FormParameter('message', 0),
            ],
            expected_status=302,
            expected_headers={
                'Location': 'http://stacrypt.io/payment_redirect?result=successful'
            }
        )

        # TODO: Check reference id

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']).scaleb(-5), Decimal('3970.152'))
        self.assertEqual(Decimal(balance['freeze']).scaleb(-5), Decimal(0))

        # 5. Verify the transaction (Double spent)
        self.request(
            As.anonymous, 'POST', f'{self.url}/pay-irs',
            params=[
                FormParameter('status', 1),
                FormParameter('transId', mockup_transaction_id),
                FormParameter('factorNumber', transaction_id),
                FormParameter('mobile', ''),
                FormParameter('description', 0),
                FormParameter('cardNumber', '647375******1092'),
                FormParameter('traceNumber', '123456'),
                FormParameter('message', 0),
            ],
            expected_status=302,
            expected_headers={
                'Location': 'http://stacrypt.io/payment_redirect?result=bad-transaction'
            }
        )

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'IRR').get('IRR')
        self.assertEqual(Decimal(balance['available']).scaleb(-5), Decimal('3970.152'))
        self.assertEqual(Decimal(balance['freeze']).scaleb(-5), Decimal(0))

        # TODO: Make test to create the situation: http://stacrypt.io/payment_redirect?result=internal-error
