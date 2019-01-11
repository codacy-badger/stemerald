from restfulpy.testing import FormParameter

from staemerald.models import Client, Market, Fund
from staemerald.models.currencies import Fiat, Cryptocurrency
from staemerald.tests.helpers import WebTestCase, As


class OrderTestCase(WebTestCase):
    url = '/apiv1/orders'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_evidence_verified = True
        cls.session.add(client1)

        usd = Fiat(code='usd', name='USA Dollar')
        btc = Cryptocurrency(code='btc', name='Bitcoin')
        btc_usd = Market(
            base_currency=btc,
            quote_currency=usd,
            price_latest=1000,
            buy_amount_min=10,
            buy_amount_max=10000,
            buy_static_commission=1,
            buy_permille_commission=100,
            buy_max_commission=0,
            sell_amount_min=0,
            sell_amount_max=0,
            sell_static_commission=0,
            sell_permille_commission=0,
            sell_max_commission=0,
        )
        cls.session.add(btc_usd)

        btc_fund1 = Fund(client=client1, currency=btc)
        btc_fund1.total_balance = 0
        btc_fund1.blocked_balance = 0

        usd_fund1 = Fund(client=client1, currency=usd)
        usd_fund1.total_balance = 15500
        usd_fund1.blocked_balance = 0

        cls.session.add(btc_fund1)
        cls.session.add(usd_fund1)

        cls.session.commit()

        cls.market1_id = btc_usd.id

    def test_order(self):
        self.login('client1@test.com', '123456')

        # 1. Add buy (price not in range)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketId', self.market1_id, type_=int),
                FormParameter('type', 'buy'),
                FormParameter('price', 1200, type_=int),
                FormParameter('amount', 12, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'price-not-in-range'}
        )

        # 2. Add buy (amount not in range)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketId', self.market1_id, type_=int),
                FormParameter('type', 'buy'),
                FormParameter('price', 1000, type_=int),
                FormParameter('amount', 1, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'amount-not-in-range'}
        )

        # 3. Add buy (not enough balance)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketId', self.market1_id, type_=int),
                FormParameter('type', 'buy'),
                FormParameter('price', 1050, type_=int),
                FormParameter('amount', 120, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'not-enough-balance'}
        )

        # 4. Add buy
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketId', self.market1_id, type_=int),
                FormParameter('type', 'buy'),
                FormParameter('price', 1050, type_=int),
                FormParameter('amount', 11, type_=int),
            ],
        )

        # 5. Getting my orders
        response, ___ = self.request(As.client, 'GET', self.url)

        self.assertEqual(len(response), 1)
        self.assertIsNotNone(response[0]['id'])
        self.assertEqual(response[0]['type'], 'buy')
        self.assertEqual(response[0]['status'], 'active')
        self.assertEqual(response[0]['totalAmount'], 11)
        self.assertEqual(response[0]['filledAmount'], 0)
        self.assertEqual(response[0]['price'], 1050)
        self.assertEqual(response[0]['totalCommission'], 2)

        self.request(As.client, 'CREATE', self.url, params=[
            FormParameter('marketId', self.market1_id, type_=int),
            FormParameter('type', 'buy'),
            FormParameter('price', 82, type_=int),
            FormParameter('amount', 12, type_=int),
        ])
