import ujson

from restfulpy.testing import FormParameter

from stemerald.models import Client, Market
from stemerald.models.currencies import Fiat, Cryptocurrency
from stemerald.stexchange import StexchangeClient, stexchange_client, StexchangeUnknownException, \
    BalanceNotEnoughException
from stemerald.tests.helpers import WebTestCase, As


class OrderTestCase(WebTestCase):
    url = '/apiv2/orders'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_evidence_verified = True
        cls.session.add(client1)

        usd = Fiat(symbol='USD', name='USA Dollar')
        btc = Cryptocurrency(symbol='BTC', name='Bitcoin', wallet_id='BTC')
        btc_usd = Market(
            name="BTC_USD",
            base_currency=btc,
            quote_currency=usd,
            buy_amount_min=10,
            buy_amount_max=10000,
            sell_amount_min=0,
            sell_amount_max=0,
            taker_commission_rate="0.4",
            maker_commission_rate="0.1",
        )
        cls.session.add(btc_usd)

        cls.session.commit()

        cls.market1_name = btc_usd.name
        cls.mockup_client_1_id = client1.id

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)
                self.mock_balance_btc = [0, 0]
                self.mock_balance_usd = [15500, 0]

            def asset_list(self):
                return ujson.loads('[{"name": "BTC", "prec": 8}, {"name": "USD", "prec": 2}]')

            def market_last(self, market):
                if market == 'BTC_USD':
                    return '1000.00000000'

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if user_id == cls.mockup_client_1_id and business in ['deposit', 'withdraw']:
                    (self.mock_balance_btc if asset == 'BTC' else self.mock_balance_usd)[0] += int(change)
                return ujson.loads(
                    '{"btc": {"available": "' +
                    str(self.mock_balance_btc[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance_btc[1]) +
                    '"}, {usd": {"available": "' +
                    str(self.mock_balance_usd[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance_usd[1]) +
                    '"}}'
                )

            def balance_query(self, *args, **kwargs):
                return ujson.loads(
                    '{"btc": {"available": "' +
                    str(self.mock_balance_btc[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance_btc[1]) +
                    '"}, {usd": {"available": "' +
                    str(self.mock_balance_usd[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance_usd[1]) +
                    '"}}'
                )

            def order_put_limit(self, user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source):
                if int(amount) == 120:
                    raise BalanceNotEnoughException(0)

                return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "BTC_USD", "taker_fee": "0.1",
                "type": 1, "deal_fee": "0", "deal_stock": "0", "maker_fee": "0.1", "source": "abc", "user": 1,
                "left": "100", "ctime": 1547419213.026914, "mtime": 1547419213.026914, "amount": "100", "deal_money":
                "0"} """)

            def order_put_market(self, user_id, market, side, amount, taker_fee_rate, source):
                if int(amount) == 120:
                    raise BalanceNotEnoughException(0)
                return ujson.loads("""{"price": "0", "id": 63, "side": 1, "market": "BTC_USD", "taker_fee":
                "0.1", "type": 2, "deal_fee": "0.6", "deal_stock": "3", "maker_fee": "0", "source": "cbd", "user": 1,
                "left": "0e-8", "ctime": 1547419213.029479, "mtime": 1547419213.029483, "amount": "3", "deal_money":
                "6"}""")

            def order_pending(self, user_id, market, offset, limit):
                return ujson.loads("""{"limit": 10, "offset": 0, "total": 1, "records": [{"price": "2", "id": 62,
                "side": 2, "market": "BTC_USD", "taker_fee": "0.1", "type": 1, "deal_fee": "0.3",
                "deal_stock": "3", "maker_fee": "0.1", "source": "abc", "user": 1, "left": "97",
                "ctime": 1547419213.026914, "mtime": 1547419213.029483, "amount": "100", "deal_money": "6"}]}""")

            def order_pending_detail(self, market, order_id):
                return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "BTC_USD", "taker_fee":
                "0.1", "type": 1, "deal_fee": "0.3", "deal_stock": "3", "maker_fee": "0.1", "source": "abc",
                "user": 1, "left": "97", "ctime": 1547419213.026914, "mtime": 1547419213.029483, "amount": "100",
                "deal_money": "6"}""")

            def order_finished(self, user_id, market, start_time, end_time, offset, limit, side):
                if market == 'BTC_USD' and user_id == cls.mockup_client_1_id and offset < 18:
                    return ujson.loads("""{"offset": 0, "limit": 20, "records": [{"id": 61, "source": "cbd", "side":
                    1, "type": 2, "deal_money": "6", "ctime": 1547419172.446086, "ftime": 1547419172.446089,
                    "user": 1, "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1",
                    "maker_fee": "0", "deal_stock": "3", "deal_fee": "0.6"}, {"id": 59, "source": "cbd", "side": 1,
                    "type": 2, "deal_money": "6", "ctime": 1547419117.217955, "ftime": 1547419117.217958, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 57, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419093.255911, "ftime": 1547419093.255915, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 55, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419090.1647, "ftime": 1547419090.164703, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 53, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419079.117208, "ftime": 1547419079.117212, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 51, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419050.312686, "ftime": 1547419050.312692, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 49, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419045.695398, "ftime": 1547419045.695404, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 47, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419044.574593, "ftime": 1547419044.574597, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 45, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419043.018587, "ftime": 1547419043.018591, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 43, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547419014.449556, "ftime": 1547419014.44956, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 41, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547419005.914382, "ftime": 1547419005.914387, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 39, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547418994.681865, "ftime": 1547418994.681873, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 37, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547418971.478641, "ftime": 1547418971.478644, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 35, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "176", "ctime": 1547418955.745287, "ftime": 1547418955.745518, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "2", "deal_fee": "17.6"}, {"id": 33, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418943.696649, "ftime": 1547418943.697126, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 31, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418864.639109, "ftime": 1547418864.639465, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 29, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418683.910061, "ftime": 1547418683.910436, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 27, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418339.31098, "ftime": 1547418339.311348, "user": 1,
                    "market": "BTC_USD", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}]}""")
                raise StexchangeUnknownException()

            def order_finished_detail(self, order_id):
                if order_id == 57:
                    return ujson.loads("""{"id": 57, "source": "cbd", "side": 1, "type": 2, "deal_money": "6",
                    "ctime": 1547419093.255911, "ftime": 1547419093.255915, "user": 1, "market": "BTC_USD",
                    "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0", "deal_stock": "3", "deal_fee":
                    "0.6"}""")
                raise StexchangeUnknownException()

            def order_deals(self, order_id, offset, limit):
                if order_id == 1 and offset == 0:
                    return ujson.loads("""{"offset": 0, "limit": 10, "records": []}""")
                raise StexchangeUnknownException()

            def order_cancel(self, user_id, market, order_id):
                if user_id == cls.mockup_client_1_id and market == 'BTC_USD' and order_id == 1:
                    return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "BTC_USD",
                    "taker_fee": "0.1", "type": 1, "deal_fee": "0.3", "deal_stock": "3", "maker_fee": "0.1",
                    "source": "abc", "user": 1, "left": "97", "ctime": 1547419213.026914, "mtime": 1547419213.029483,
                    "amount": "100", "deal_money": "6"}""")
                raise StexchangeUnknownException()

        stexchange_client._set_instance(MockStexchangeClient())

    def test_market_order(self):
        self.login('client1@test.com', '123456')

        # 1. Add buy (amount not in range)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'market'),
                FormParameter('side', 'buy'),
                FormParameter('amount', 1, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'amount-not-in-range'}
        )

        # 2. Add buy (not enough balance)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'market'),
                FormParameter('side', 'buy'),
                FormParameter('amount', 120, type_=int),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'not-enough-balance'}
        )

        # 3. Add buy
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'market'),
                FormParameter('side', 'buy'),
                FormParameter('amount', 11, type_=int),
            ],
        )

    def test_limit_order(self):
        self.login('client1@test.com', '123456')

        # 1. Add buy (price not in range)
        self.request(
            As.client, 'CREATE', self.url,
            params=[
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'limit'),
                FormParameter('side', 'buy'),
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
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'limit'),
                FormParameter('side', 'buy'),
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
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'limit'),
                FormParameter('side', 'buy'),
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
                FormParameter('marketName', self.market1_name, type_=str),
                FormParameter('type', 'limit'),
                FormParameter('side', 'buy'),
                FormParameter('price', 1050, type_=int),
                FormParameter('amount', 11, type_=int),
            ],
        )

    def test_cancel_order(self):
        self.login('client1@test.com', '123456')

        self.request(
            As.client, 'CANCEL', f'{self.url}/1',
            query_string={'marketName': 'BTC_USD'},
        )

    def test_order_deals(self):
        self.login('client1@test.com', '123456')

        self.request(
            As.client, 'DEAL', f'{self.url}/1',
            query_string={'marketName': 'BTC_USD'},
        )
        # TODO: Add mock data and add result assertion

    def test_order_get(self):
        self.login('client1@test.com', '123456')

        # 1. Getting my orders (pending)
        response, ___ = self.request(
            As.client, 'GET', self.url,
            query_string={'marketName': self.market1_name, 'status': 'pending'},
        )

        self.assertEqual(len(response), 1)
        self.assertIsNotNone(response[0]['id'])
        self.assertEqual(response[0]['createdAt'], '2019-01-14T01:40:13Z')
        self.assertEqual(response[0]['modifiedAt'], '2019-01-14T01:40:13Z')
        self.assertIsNone(response[0]['finishedAt'])
        self.assertEqual(response[0]['market'], self.market1_name)
        self.assertEqual(response[0]['user'], 1)
        self.assertEqual(response[0]['type'], 'limit')
        self.assertEqual(response[0]['side'], 'buy')
        self.assertEqual(response[0]['amount'], '100')
        self.assertEqual(response[0]['price'], '2')
        self.assertEqual(response[0]['takerFeeRate'], '0.1')
        self.assertEqual(response[0]['makerFeeRate'], '0.1')
        self.assertEqual(response[0]['source'], 'abc')
        self.assertEqual(response[0]['filledMoney'], '6')
        self.assertEqual(response[0]['filledStock'], '3')
        self.assertEqual(response[0]['filledFee'], '0.3')

        # 2. Getting my orders (finished)
        response, ___ = self.request(
            As.client, 'GET', self.url,
            query_string={'marketName': self.market1_name, 'status': 'finished'},
        )

        self.assertEqual(len(response), 18)
        self.assertIsNotNone(response[0]['id'])
        self.assertEqual(response[0]['createdAt'], '2019-01-14T01:39:32Z')
        self.assertIsNone(response[0]['modifiedAt'])
        self.assertEqual(response[0]['finishedAt'], '2019-01-14T01:39:32Z')
        self.assertEqual(response[0]['market'], self.market1_name)
        self.assertEqual(response[0]['user'], 1)
        self.assertEqual(response[0]['type'], 'market')
        self.assertEqual(response[0]['side'], 'sell')
        self.assertEqual(response[0]['amount'], '3')
        self.assertEqual(response[0]['price'], '0')  # FIXME: Why 0???
        self.assertEqual(response[0]['takerFeeRate'], '0.1')
        self.assertEqual(response[0]['makerFeeRate'], '0')
        self.assertEqual(response[0]['source'], 'cbd')
        self.assertEqual(response[0]['filledMoney'], '6')
        self.assertEqual(response[0]['filledStock'], '3')
        self.assertEqual(response[0]['filledFee'], '0.6')

        # 3. Getting order detail (pending)
        response, ___ = self.request(
            As.client, 'GET', f'{self.url}/62',
            query_string={'marketName': self.market1_name, 'status': 'pending'},
        )
        self.assertIsNotNone(response['id'])
        self.assertEqual(response['createdAt'], '2019-01-14T01:40:13Z')
        self.assertEqual(response['modifiedAt'], '2019-01-14T01:40:13Z')
        self.assertIsNone(response['finishedAt'])
        self.assertEqual(response['market'], self.market1_name)
        self.assertEqual(response['user'], 1)
        self.assertEqual(response['type'], 'limit')
        self.assertEqual(response['side'], 'buy')
        self.assertEqual(response['amount'], '100')
        self.assertEqual(response['price'], '2')
        self.assertEqual(response['takerFeeRate'], '0.1')
        self.assertEqual(response['makerFeeRate'], '0.1')
        self.assertEqual(response['source'], 'abc')
        self.assertEqual(response['filledMoney'], '6')
        self.assertEqual(response['filledStock'], '3')
        self.assertEqual(response['filledFee'], '0.3')

        # 4. Getting order detail (finished)
        response, ___ = self.request(
            As.client, 'GET', f'{self.url}/57',
            query_string={'marketName': self.market1_name, 'status': 'finished'},
        )

        self.assertIsNotNone(response['id'])
        self.assertEqual(response['createdAt'], '2019-01-14T01:38:13Z')
        self.assertIsNone(response['modifiedAt'])
        self.assertEqual(response['finishedAt'], '2019-01-14T01:38:13Z')
        self.assertEqual(response['market'], self.market1_name)
        self.assertEqual(response['user'], 1)
        self.assertEqual(response['type'], 'market')
        self.assertEqual(response['side'], 'sell')
        self.assertEqual(response['amount'], '3')
        self.assertEqual(response['price'], '0')  # FIXME: Why 0???
        self.assertEqual(response['takerFeeRate'], '0.1')
        self.assertEqual(response['makerFeeRate'], '0')
        self.assertEqual(response['source'], 'cbd')
        self.assertEqual(response['filledMoney'], '6')
        self.assertEqual(response['filledStock'], '3')
        self.assertEqual(response['filledFee'], '0.6')
