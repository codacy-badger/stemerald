from restfulpy.testing import FormParameter

from stemerald.models import Market, Cryptocurrency, Fiat, Client
from stemerald.tests.helpers import WebTestCase, As


class MarketEditTestCase(WebTestCase):
    url = '/apiv1/markets'

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
            sell_permille_commission=50,
            sell_max_commission=0,
        )
        cls.session.add(btc_usd)

        cls.session.commit()

        cls.btc_usd_id = btc_usd.id

    def test_currency_edit(self):
        self.login('client1@test.com', '123456')

        self.request(
            As.member, 'CALCULATE', f'{self.url}/{self.btc_usd_id}',
            params=[
                FormParameter('type', 'sell'),
                FormParameter('price', 100, type_=int),
                FormParameter('amount', 100, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'price-not-in-range'}
        )

        response, ___ = self.request(
            As.member, 'CALCULATE', f'{self.url}/{self.btc_usd_id}',
            params=[
                FormParameter('type', 'buy'),
                FormParameter('price', 100, type_=int),
                FormParameter('amount', 100, type_=int),
            ]
        )

        self.assertEqual(response['commission'], 11)

        response, ___ = self.request(
            As.member, 'CALCULATE', f'{self.url}/{self.btc_usd_id}',
            params=[
                FormParameter('type', 'sell'),
                FormParameter('price', 4444, type_=int),
                FormParameter('amount', 685, type_=int),
            ]
        )

        self.assertEqual(response['commission'], 34)
