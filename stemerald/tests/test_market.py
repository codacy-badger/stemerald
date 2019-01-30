import ujson

from stemerald.models import Client
from stemerald.stexchange import StexchangeClient, stexchange_client, StexchangeUnknownException
from stemerald.tests.helpers import WebTestCase, As


class MarketGetTestCase(WebTestCase):
    url = '/apiv1/markets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        cls.session.commit()

        cls.mock_client1 = client1

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)

            def market_last(self, market):
                return '2.00000000'

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

            def market_deals(self, market, limit, last_id):
                if market == 'TESTNET3RINKEBY' and limit == 10 and last_id < 18:
                    return ujson.loads(
                        '[{"id": 27, "time": 1547419172.446089, "price": "2", "amount": "3", "type": "sell"},{"id": 26,'
                        '"time": 1547419117.217958, "price": "2", "amount": "3", "type": "sell"}, {"id": 25, '
                        '"time": 1547419093.255915, "price": "2", "amount": "3", "type": "sell"}, {"id": 24, '
                        '"time": 1547419090.164703, "price": "2", "amount": "3", "type": "sell"}, {"id": 23, '
                        '"time": 1547419079.117212, "price": "2", "amount": "3", "type": "sell"}, {"id": 22, '
                        '"time": 1547419050.312692, "price": "2", "amount": "1", "type": "sell"}, {"id": 21, '
                        '"time": 1547419045.695404, "price": "2", "amount": "1", "type": "sell"}, {"id": 20, '
                        '"time": 1547419044.574597, "price": "2", "amount": "1", "type": "sell"}, {"id": 19, '
                        '"time": 1547419043.018591, "price": "2", "amount": "1", "type": "sell"}, {"id": 18, '
                        '"time": 1547419014.44956, "price": "88", "amount": "1", "type": "sell"}]'
                    )
                raise StexchangeUnknownException()

            def market_user_deals(self, user_id, market, offset, limit):
                if user_id == cls.mock_client1.id and market == 'TESTNET3RINKEBY' and offset == 0 and limit == 10:
                    return ujson.loads(
                        '{"offset": 0, "limit": 10, "records": [{"time": 1547419172.446089, "id": 27, "side": 2, '
                        '"price": "2", "user": 1, "fee": "0.3", "role": 1, "amount": "3", "deal": "6", '
                        '"deal_order_id": 61}, {"time": 1547419172.446089, "id": 27, "side": 1, "price": "2", '
                        '"user": 1, "fee": "0.6", "role": 2, "amount": "3", "deal": "6", "deal_order_id": 60}, '
                        '{"time": 1547419117.217958, "id": 26, "side": 2, "price": "2", "user": 1, "fee": "0.3", '
                        '"role": 1, "amount": "3", "deal": "6", "deal_order_id": 59}, {"time": 1547419117.217958, '
                        '"id": 26, "side": 1, "price": "2", "user": 1, "fee": "0.6", "role": 2, "amount": "3", '
                        '"deal": "6", "deal_order_id": 58}, {"time": 1547419093.255915, "id": 25, "side": 2, '
                        '"price": "2", "user": 1, "fee": "0.3", "role": 1, "amount": "3", "deal": "6", '
                        '"deal_order_id": 57}, {"time": 1547419093.255915, "id": 25, "side": 1, "price": "2", '
                        '"user": 1, "fee": "0.6", "role": 2, "amount": "3", "deal": "6", "deal_order_id": 56}, '
                        '{"time": 1547419090.164703, "id": 24, "side": 2, "price": "2", "user": 1, "fee": "0.3", '
                        '"role": 1, "amount": "3", "deal": "6", "deal_order_id": 55}, {"time": 1547419090.164703, '
                        '"id": 24, "side": 1, "price": "2", "user": 1, "fee": "0.6", "role": 2, "amount": "3", '
                        '"deal": "6", "deal_order_id": 54}, {"time": 1547419079.117212, "id": 23, "side": 2, '
                        '"price": "2", "user": 1, "fee": "0.3", "role": 1, "amount": "3", "deal": "6", '
                        '"deal_order_id": 53}, {"time": 1547419079.117212, "id": 23, "side": 1, "price": "2", '
                        '"user": 1, "fee": "0.6", "role": 2, "amount": "3", "deal": "6", "deal_order_id": 52}]} '
                    )
                raise StexchangeUnknownException()

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

    def test_market_last(self):
        response, ___ = self.request(As.anonymous, 'LAST', f"{self.url}/TESTNET3RINKEBY")

        self.assertIn('name', response)
        self.assertIn('price', response)

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

    def test_market_deals(self):
        response, ___ = self.request(
            As.anonymous, 'PEEK', f"{self.url}/TESTNET3RINKEBY/marketdeals",
            query_string={'limit': 10, 'lastId': 10}
        )

        self.assertEqual(len(response), 10)
        self.assertIn('id', response[0])
        self.assertIn('time', response[0])
        self.assertIn('price', response[0])
        self.assertIn('amount', response[0])
        self.assertIn('type', response[0])

    def test_my_deals(self):
        self.login('client1@test.com', '123456')

        response, ___ = self.request(
            As.client, 'PEEK', f"{self.url}/TESTNET3RINKEBY/mydeals",
            query_string={'limit': 10, 'offset': 0}
        )

        self.assertEqual(len(response), 10)
        self.assertIn('id', response[0])
        self.assertIn('time', response[0])
        self.assertIn('side', response[0])
        self.assertIn('price', response[0])
        self.assertIn('user', response[0])
        self.assertIn('amount', response[0])
        self.assertIn('fee', response[0])
        self.assertIn('deal', response[0])
        self.assertIn('dealOrderId', response[0])
        self.assertIn('role', response[0])
