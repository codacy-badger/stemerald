from stemerald.models.currencies import Cryptocurrency, Fiat
from stemerald.tests.helpers import WebTestCase, As


class CurrencyGetTestCase(WebTestCase):
    url = '/apiv2/currencies'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        cls.session.add(Fiat(symbol='usd', name='USA Dollar'))
        cls.session.add(Cryptocurrency(symbol='btc', name='Bitcoin', wallet_id=1))

        cls.session.commit()

    def test_currency_get(self):
        response, ___ = self.request(As.anonymous, 'GET', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('symbol', response[0])
        self.assertIn('name', response[0])
        self.assertIn('type', response[0])
