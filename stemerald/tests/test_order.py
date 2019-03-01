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

        usd = Fiat(symbol='usd', name='USA Dollar')
        btc = Cryptocurrency(symbol='btc', name='Bitcoin', wallet_id=1)
        btc_usd = Market(
            name="btc/usd",
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
                return ujson.loads('[{"name": "btc", "prec": 8}, {"name": "usd", "prec": 2}]')

            def market_last(self, market):
                if market == 'btc/usd':
                    return '1000.00000000'

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if user_id == cls.mockup_client_1_id and business in ['deposit', 'withdraw']:
                    (self.mock_balance_btc if asset == 'btc' else self.mock_balance_usd)[0] += int(change)
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

                return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "TESTNET3RINKEBY", "taker_fee": "0.1",
                "type": 1, "deal_fee": "0", "deal_stock": "0", "maker_fee": "0.1", "source": "abc", "user": 1,
                "left": "100", "ctime": 1547419213.026914, "mtime": 1547419213.026914, "amount": "100", "deal_money":
                "0"} """)

            def order_put_market(self, user_id, market, side, amount, taker_fee_rate, source):
                if int(amount) == 120:
                    raise BalanceNotEnoughException(0)
                return ujson.loads("""{"price": "0", "id": 63, "side": 1, "market": "TESTNET3RINKEBY", "taker_fee":
                "0.1", "type": 2, "deal_fee": "0.6", "deal_stock": "3", "maker_fee": "0", "source": "cbd", "user": 1,
                "left": "0e-8", "ctime": 1547419213.029479, "mtime": 1547419213.029483, "amount": "3", "deal_money":
                "6"}""")

            def order_book(self, market, side, offset, limit):
                return ujson.loads("""{"offset": 0, "orders": [], "limit": 10, "total": 0}""")

            def order_pending(self, user_id, market, offset, limit):
                return ujson.loads("""{"limit": 10, "offset": 0, "total": 1, "records": [{"price": "2", "id": 62,
                "side": 2, "market": "TESTNET3RINKEBY", "taker_fee": "0.1", "type": 1, "deal_fee": "0.3",
                "deal_stock": "3", "maker_fee": "0.1", "source": "abc", "user": 1, "left": "97",
                "ctime": 1547419213.026914, "mtime": 1547419213.029483, "amount": "100", "deal_money": "6"}]}""")

            def order_pending_detail(self, market, order_id):
                return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "TESTNET3RINKEBY", "taker_fee":
                "0.1", "type": 1, "deal_fee": "0.3", "deal_stock": "3", "maker_fee": "0.1", "source": "abc",
                "user": 1, "left": "97", "ctime": 1547419213.026914, "mtime": 1547419213.029483, "amount": "100",
                "deal_money": "6"}""")

            def order_finished(self, user_id, market, start_time, end_time, offset, limit, side):
                if market == 'btc/usd' and user_id == cls.mockup_client_1_id and limit == 10 and start_time == 10 \
                        and end_time == 10 and side < 18 and offset < 18:
                    return ujson.loads("""{"offset": 0, "limit": 20, "records": [{"id": 61, "source": "cbd", "side":
                    1, "type": 2, "deal_money": "6", "ctime": 1547419172.446086, "ftime": 1547419172.446089,
                    "user": 1, "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1",
                    "maker_fee": "0", "deal_stock": "3", "deal_fee": "0.6"}, {"id": 59, "source": "cbd", "side": 1,
                    "type": 2, "deal_money": "6", "ctime": 1547419117.217955, "ftime": 1547419117.217958, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 57, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419093.255911, "ftime": 1547419093.255915, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 55, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419090.1647, "ftime": 1547419090.164703, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 53, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "6", "ctime": 1547419079.117208, "ftime": 1547419079.117212, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "0.6"}, {"id": 51, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419050.312686, "ftime": 1547419050.312692, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 49, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419045.695398, "ftime": 1547419045.695404, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 47, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419044.574593, "ftime": 1547419044.574597, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 45, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "2", "ctime": 1547419043.018587, "ftime": 1547419043.018591, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "0.2"}, {"id": 43, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547419014.449556, "ftime": 1547419014.44956, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 41, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547419005.914382, "ftime": 1547419005.914387, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 39, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547418994.681865, "ftime": 1547418994.681873, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 37, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "88", "ctime": 1547418971.478641, "ftime": 1547418971.478644, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "1", "deal_fee": "8.8"}, {"id": 35, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "176", "ctime": 1547418955.745287, "ftime": 1547418955.745518, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "2", "deal_fee": "17.6"}, {"id": 33, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418943.696649, "ftime": 1547418943.697126, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 31, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418864.639109, "ftime": 1547418864.639465, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 29, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418683.910061, "ftime": 1547418683.910436, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}, {"id": 27, "source": "cbd", "side": 1, "type": 2,
                    "deal_money": "264", "ctime": 1547418339.31098, "ftime": 1547418339.311348, "user": 1,
                    "market": "TESTNET3RINKEBY", "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0",
                    "deal_stock": "3", "deal_fee": "26.4"}]}""")
                raise StexchangeUnknownException()

            def order_finished_detail(self, order_id):
                if order_id == 1:
                    return ujson.loads("""{"id": 57, "source": "cbd", "side": 1, "type": 2, "deal_money": "6",
                    "ctime": 1547419093.255911, "ftime": 1547419093.255915, "user": 1, "market": "TESTNET3RINKEBY",
                    "price": "0", "amount": "3", "taker_fee": "0.1", "maker_fee": "0", "deal_stock": "3", "deal_fee":
                    "0.6"}""")
                raise StexchangeUnknownException()

            def order_deals(self, order_id, offset, limit):
                if order_id == 1 and offset == 0:
                    return ujson.loads("""{"offset": 0, "limit": 10, "records": []}""")
                raise StexchangeUnknownException()

            def order_depth(self, market, limit, interval):
                if market == 'btc/usd' and interval == 0 and limit == 10:
                    return ujson.loads("""{"asks": [], "bids": [["2", "97"]]}""")
                raise StexchangeUnknownException()

            def order_cancel(self, user_id, market, order_id):
                if user_id == cls.mockup_client_1_id and market == 'btc/usd' and order_id == 1:
                    return ujson.loads("""{"price": "2", "id": 62, "side": 2, "market": "TESTNET3RINKEBY",
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
            query_string={'marketName': 'btc/usd'},
        )

    def test_order_deals(self):
        self.login('client1@test.com', '123456')

        self.request(
            As.client, 'DEAL', f'{self.url}/1',
            query_string={'marketName': 'btc/usd'},
        )

    def test_order_get(self):
        # 1. Getting my orders (pending)
        response, ___ = self.request(As.client, 'GET', self.url)

        self.assertEqual(len(response), 1)
        self.assertIsNotNone(response[0]['id'])
        self.assertEqual(response[0]['type'], 'buy')
        self.assertEqual(response[0]['status'], 'active')
        self.assertEqual(response[0]['totalAmount'], 11)
        self.assertEqual(response[0]['filledAmount'], 0)
        self.assertEqual(response[0]['price'], 1050)
        self.assertEqual(response[0]['totalCommission'], 2)
        # 2. Getting my orders (finished)

        # 3. Getting order detail (pending)

        # 4. Getting order detail (finished)

        # 1. Getting my orders
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
            FormParameter('marketId', self.market1_name, type_=int),
            FormParameter('type', 'buy'),
            FormParameter('price', 82, type_=int),
            FormParameter('amount', 12, type_=int),
        ])
