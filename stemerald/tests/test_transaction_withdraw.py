from restfulpy.testing import FormParameter

from stemerald.models import Client, Cryptocurrency, Fund
from stemerald.tests.helpers import WebTestCase, As

current_balance = 3001

withdraw_min = 1000
withdraw_max = 599000
withdraw_static_commission = 129
withdraw_permille_commission = 23
withdraw_max_commission = 746


class TransactionWithdrawTestCase(WebTestCase):
    url = '/apiv2/transactions/withdraws'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        cls.session.add(client1)

        cls.session.flush()

        btc = Cryptocurrency(
            code='btc',
            name='Bitcoin',
            withdraw_min=withdraw_min,
            withdraw_max=withdraw_max,
            withdraw_static_commission=withdraw_static_commission,
            withdraw_permille_commission=withdraw_permille_commission,
            withdraw_max_commission=withdraw_max_commission,
        )
        cls.session.add(btc)

        cls.session.add(Fund(client=client1, currency=btc, total_balance=current_balance))

        cls.session.commit()

        cls.mockup_client_1_id = client1.id

    def test_transaction_withdraw(self):
        self.login('client1@test.com', '123456')

        # 1. Schedule a withdraw (not enough credit)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.url,
            params=[
                FormParameter('cryptocurrencyCode', 'btc'),
                FormParameter('amount', 599000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
            ],
            expected_status=400
        )

        # 2. Schedule a withdraw (bad address)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.url,
            params=[
                FormParameter('cryptocurrencyCode', 'btc'),
                FormParameter('amount', 2000),
                FormParameter('address', 'bad-address'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-address'}
        )

        # 3. Schedule a withdraw
        result, ___ = self.request(
            As.semitrusted_client, 'SCHEDULE', self.url,
            params=[
                FormParameter('cryptocurrencyCode', 'btc'),
                FormParameter('amount', 2000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
            ],
        )

        self.assertIn('id', result)

        self.assertEqual(result['amount'], 2000)
        self.assertEqual(result['commission'], 175)
        self.assertEqual(result['address'], '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV')

        self.assertIsNone(result['cryptotxId'])
        self.assertIsNone(result['error'])

        # Check balance
        fund = self.session.query(Fund) \
            .filter(Fund.client_id == self.mockup_client_1_id) \
            .filter(Fund.currency_code == 'btc') \
            .one_or_none()
        self.assertEqual(fund.total_balance, 826)
        self.assertEqual(fund.blocked_balance, 0)
