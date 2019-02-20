from nanohttp import settings

from stemerald.models import Client, Pan, Fiat, Fund
from stemerald.shaparak import ShaparakProvider, ShaparakError
from stemerald.tests.helpers import WebTestCase, As
from restfulpy.testing import FormParameter

deposit_min = 200
deposit_max = 0
deposit_static_commission = 43
deposit_permille_commission = 123
deposit_max_commission = 897

mockup_transaction_id = '4738'
mockup_amount = 4576
mockup_card_address = '6473-7563-8264-1092'
is_transaction_verified = False


class MockupShaparakProvider(ShaparakProvider):
    def create_transaction(self, batch_id, amount):
        return mockup_transaction_id

    def verify_transaction(self, transaction_id):
        if is_transaction_verified:
            return mockup_amount, None, None
        raise ShaparakError(None)


class TransactionShaparakInTestCase(WebTestCase):
    url = '/apiv2/transactions/shaparak-ins'

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
            code='irr',
            name='Iran Rial',
            deposit_min=deposit_min,
            deposit_max=deposit_max,
            deposit_static_commission=deposit_static_commission,
            deposit_permille_commission=deposit_permille_commission,
            deposit_max_commission=deposit_max_commission,
        )
        cls.session.add(irr)

        cls.session.add(Fund(client=client1, currency=irr))

        shetab_address_1 = Pan(client=client1, address=mockup_card_address, is_verified=True)
        cls.session.add(shetab_address_1)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id
        cls.mockup_shetab_address_1_id = shetab_address_1.id

    def test_transaction_deposit_create(self):
        self.login('client1@test.com', '123456')

        # 1. Create an Shaparak-In transaction
        result, ___ = self.request(As.trusted_client, 'CREATE', self.url, params=[
            FormParameter('amount', mockup_amount, type_=int),
            FormParameter('shetabAddressId', self.mockup_shetab_address_1_id),
        ])

        self.assertIn('id', result)
        self.assertIn('transactionId', result)
        self.assertIn('shetabAddress', result)
        self.assertIn('referenceId', result)

        transaction_id = result['id']

        # Check balance
        fund = self.session.query(Fund) \
            .filter(Fund.client_id == self.mockup_client_1_id) \
            .filter(Fund.currency_code == 'irr') \
            .one_or_none()
        self.assertEqual(fund.total_balance, 0)
        self.assertEqual(fund.blocked_balance, 0)

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
        global is_transaction_verified
        is_transaction_verified = True
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
        self.session.refresh(fund)
        self.assertEqual(fund.total_balance, 3971)
        self.assertEqual(fund.blocked_balance, 0)

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
        self.session.refresh(fund)
        self.assertEqual(fund.total_balance, 3971)
        self.assertEqual(fund.blocked_balance, 0)
