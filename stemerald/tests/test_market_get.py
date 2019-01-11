from stemerald.models import Market, Cryptocurrency, Fiat
from stemerald.tests.helpers import WebTestCase, As


class MarketGetTestCase(WebTestCase):
    url = '/apiv1/markets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        usd = Fiat(code='usd', name='USA Dollar')
        btc = Cryptocurrency(code='btc', name='Bitcoin')
        ltc = Cryptocurrency(code='ltc', name='Litecoin')

        btc_usd = Market(base_currency=btc, quote_currency=usd, price_latest=10)
        ltc_btc = Market(base_currency=ltc, quote_currency=btc, price_latest=10)

        cls.session.add(usd)
        cls.session.add(btc)
        cls.session.add(ltc)
        cls.session.add(btc_usd)
        cls.session.add(ltc_btc)

        cls.session.commit()

        cls.market_id1 = btc_usd.id

    def test_market_get(self):
        response, ___ = self.request(As.anonymous, 'GET', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('id', response[0])
        self.assertIn('baseCurrency', response[0])
        self.assertIn('quoteCurrency', response[0])

        self.assertIn('name', response[0]['baseCurrency'])
        self.assertIn('code', response[0]['baseCurrency'])

        # By id
        response, ___ = self.request(As.anonymous, 'GET', f'{self.url}/{self.market_id1}')

        self.assertIn('id', response)
        self.assertIn('baseCurrency', response)
        self.assertIn('quoteCurrency', response)
        self.assertIn('priceLatest', response)
        self.assertIn('price24', response)
        self.assertIn('priceLowest24', response)
        self.assertIn('priceHighest24', response)
        self.assertIn('capTotal', response)
        self.assertIn('cap24', response)

        self.assertIn('name', response['baseCurrency'])
        self.assertIn('code', response['baseCurrency'])
