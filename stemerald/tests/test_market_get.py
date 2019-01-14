import ujson

from restfulpy.testing import FormParameter

from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As


class MarketGetTestCase(WebTestCase):
    url = '/apiv1/markets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)

            def market_list(self):
                return ujson.loads(
                    '[{"name": "TESTNET3RINKEBY", "stock": "RINKEBY", "stock_prec": 8, "money": "TESTNET3", '
                    '"fee_prec": 4, "min_amount": "0.00001", "money_prec": 8}] '
                )

            def market_summary(self, market):
                return ujson.loads(
                    '[{"name": "TESTNET3RINKEBY", "bid_amount": "0", "bid_count": 0, "ask_count": 0, "ask_amount":"0"}]'
                )

            def market_status(self, market, period):
                return ujson.loads(
                    '{"low": "2", "period": 86400, "deal": "1622", "high": "88", "last": "2", "open": "88", "close": '
                    '"2", "volume": "37"} '
                )

            def market_status_today(self, market):
                return ujson.loads(
                    '{"open": "88", "deal": "1622", "high": "88", "last": "2", "low": "2", "volume": "37"}'
                )

        stexchange_client._set_instance(MockStexchangeClient())

    def test_market_list(self):
        response, ___ = self.request(As.anonymous, 'LIST', self.url)

        self.assertEqual(len(response), 1)
        self.assertIn('name', response[0])
        self.assertIn('stock', response[0])
        self.assertIn('stockPrec', response[0])
        self.assertIn('money', response[0])
        self.assertIn('feePrec', response[0])
        self.assertIn('minAmount', response[0])
        self.assertIn('moneyPrec', response[0])

    def test_market_summary(self):
        response, ___ = self.request(As.anonymous, 'SUMMARY', f"{self.url}/TESTNET3RINKEBY")

        self.assertEqual(len(response), 1)
        self.assertIn('name', response[0])
        self.assertIn('bidAmount', response[0])
        self.assertIn('bidCount', response[0])
        self.assertIn('askAmount', response[0])
        self.assertIn('askCount', response[0])

    def test_market_status(self):
        response, ___ = self.request(
            As.anonymous, 'STATUS', f"{self.url}/TESTNET3RINKEBY",
            query_string={'period': 86400}
        )

        self.assertIn('open', response)
        self.assertIn('high', response)
        self.assertIn('low', response)
        self.assertIn('close', response)
        self.assertIn('last', response)
        self.assertIn('volume', response)
        self.assertIn('deal', response)
        self.assertIn('period', response)

        response, ___ = self.request(
            As.anonymous, 'STATUS', f"{self.url}/TESTNET3RINKEBY",
            query_string={'period': 'today'}
        )
        self.assertIn('open', response)
        self.assertIn('high', response)
        self.assertIn('low', response)
        self.assertIn('close', response)
        self.assertIn('last', response)
        self.assertIn('deal', response)
        self.assertIsNone(response['period'])
        self.assertIsNone(response['close'])
