import json
import time

import requests
from nanohttp import settings

from restfulpy.logging_ import get_logger

logger = get_logger('STEXCHANGE_RPC_CLIENT')

# from logging import Logger
# logger = Logger('STEXCHANGE_RPC_CLIENT')


class StexchangeClient:
    def __init__(self, server_url=None, headers=None):
        self.server_url = server_url or settings.stexchange.rpc_url
        self.headers = {'content-type': 'application/json'}
        self.headers.update(headers or {})
        self.request_id = 0

    def _next_request_id(self):
        self.request_id += 1
        return self.request_id

    def _execute(self, method, params, error_mapper=None):
        _id = self._next_request_id()
        params = list(map(lambda x: x if x is not None else "null", params))
        payload = json.dumps({"method": method, "params": params, "id": _id})

        logger.debug(f"Requesting {method} with id:{_id} with parameters: {'.'.join(str(params))}")

        try:
            response = requests.post(self.server_url, data=payload, headers=self.headers).json()
        except Exception as e:
            raise StexchangeUnknownException(f"Request error: {str(e)}")

        if response["error"] is not None and len(response["error"]) > 0:
            error_mapper = error_mapper or {}
            error_mapper.update(STEXCHANEG_GENERAL_ERROR_CODE_MAP)
            error = response["error"]
            raise (
                error_mapper[error["code"]](response["id"]) if (error["code"] in error_mapper)
                else StexchangeUnknownException(f"id: {response['id']} Unknown error code: {error['code']}")
            )

        elif response["result"] is not None:
            logger.debug(f"Request {response['id']} respond")
            return response["result"]

        else:
            return StexchangeUnknownException("Neither error and result fields available")

    """
        Asset APIs:
    """

    def balance_query(self, user_id, *asset_name):
        """
        Asset inquiry:
        method: balance.query

        params: unfixed parameters, first parameter is user ID, followed by list of asset names.
        Return to user's overall asset if the list is blank.

        :param user_id: user ID，Integer
        :param asset_name: list

        :return: {"asset": {"available": "amount", "freeze": "amount"}}

        Example:
            "params": [1, "BTC"]
            "result": {"BTC": {"available": "1.10000000","freeze": "9.90000000"}}

        """
        return self._execute(
            "balance.query",
            [user_id, *asset_name]
        )

    def balance_update(self, user_id, asset, business, business_id, change, detail):
        """
        Asset change:
        method: balance.update

        :param user_id: user ID，Integer
        :param asset: asset name，String
        :param business: business type，String
        :param business_id: business ID，Integer, but it will only succeed once with multiple operations of the same user_id, asset, business or business_id
        :param change: balance change，String, negative numbers for deduction
        :param detail: Json object，attached information

        :return: "success"

        Example:
            "params": [1, "BTC", "deposit", 100, "1.2345"]
            "result": "success"


        :raise RepeatUpdateException: repeat update
        :raise BalanceNotEnough: balance not enough

        """
        return self._execute(
            "balance.update",
            [user_id, asset, business, business_id, change, detail],
            {10: RepeatUpdateException, 11: BalanceNotEnoughException}
        )

    def balance_history(self, user_id, asset=None, business=None, start_time=0, end_time=0, offset=0, limit=0):
        """
        Asset history:
        method: balance.history

        :param user_id: user ID, Integer
        :param asset: asset name，which can be null
        :param business: business，which can be null，use ',' to separate types
        :param start_time: start time，0 for unlimited，Integer
        :param end_time: end time，0 for unlimited, Integer
        :param offset: offset position，Integer
        :param limit: count limit，Integer

        :return: {
                "offset":
                "limit":
                "records": [
                    {
                        "time": timestamp,
                        "asset": asset,
                        "business": business,
                        "change": change,
                        "balance"：balance,
                        "detail": detail
                    }
                    ...
                ]
            }

        """
        return self._execute(
            "balance.history",
            [user_id, asset, business, start_time, end_time, offset, limit]
        )

    def asset_list(self):
        """
        Asset list:
        method: asset.list

        """
        return self._execute(
            "asset.list",
            []
        )

    def asset_summary(self):
        """
        Asset summary:
        method: asset.summary

        """
        return self._execute(
            "asset.summary",
            []
        )

    """
        Trade APIs:
    """

    def order_put_limit(self, user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source):
        """
        Place limit order:
        method: order.put_limit

        :param user_id: user ID，Integer
        :param market: market name，String
        :param side: 1: sell, 2: buy，Integer
        :param amount: count，String
        :param price: price，String
        :param taker_fee_rate: String, taker fee
        :param taker_fee_rate: String, taker fee
        :param maker_fee_rate: String, maker fee
        :param source: String, source，up to 30 bytes

        :return: order detail:

        Example:
            params: [1, "BTCCNY", 1, "10", "8000", "0.002", "0.001"]


        :raise BalanceNotEnough: balance not enough

        """
        return self._execute(
            "order.put_limit",
            [user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source],
            {10: BalanceNotEnoughException}
        )

    def order_put_market(self, user_id, market, side, amount, taker_fee_rate, source):
        """
        Place market order:
        method: order.put_market

        :param user_id: user ID，Integer
        :param market: market name，String
        :param side: 1: sell, 2: buy，Integer
        :param amount: count or amount，String
        :param taker_fee_rate: taker fee
        :param source: String, source，up to 30 bytes

        :return: order detail:

        Example:
            params: '[1, "BTCCNY", 1, "10","0.002"]'


        :raise BalanceNotEnough: balance not enough

        """
        return self._execute(
            "order.put_market",
            [user_id, market, side, amount, taker_fee_rate, source],
            {10: BalanceNotEnoughException}
        )

    def order_cancel(self, user_id, market, order_id):
        """
        Cancel order:
        method: order.cancel

        :param user_id: user ID，Integer
        :param market: market name，String
        :param order_id： order ID

        :return: order detail

        :raise OrderNotFoundException: order not found
        :raise UserNotMatchException: user not match

        """
        return self._execute(
            "order.cancel",
            [user_id, market, order_id],
            {10: OrderNotFoundException, 11: UserNotMatchException}
        )

    def order_deals(self, order_id, offset, limit):
        """
        Order details:
        method: order.deals

        :param order_id： order ID, Integer
        :param offset
        :param limit

        :return:
            "result": {
            "offset":
            "limit":
            "records": [
                {
                    "id": Executed ID
                    "time": timestamp
                    "user": user ID
                    "role": role，1：Maker, 2: Taker
                    "amount": count
                    "price": price
                    "deal": order amount
                    "fee": fee
                    "deal_order_id": Counterpart transaction ID
                }
            ...
            ]

        """
        return self._execute(
            "order.deals",
            [order_id, offset, limit]
        )

    def order_book(self, market, side, offset, limit):
        """
        Order list:
        method: order.book

        :param market:
        :param side: side，1：sell，2：buy
        :param offset
        :param limit

        :return:

        """
        return self._execute(
            "order.book",
            [market, side, offset, limit]
        )

    def order_depth(self, market, limit, interval):
        """
        Order depth:
        method: order.depth

        :param market：market name
        :param limit: count limit，Integer
        :param interval: interval，String, e.g. "1" for 1 unit interval, "0" for no interval

        :return:
            "result": {
                "asks": [
                    [
                        "8000.00",
                        "9.6250"
                    ]
                ],
                "bids": [
                    [
                        "7000.00",
                        "0.1000"
                    ]
                ]
            }

        """
        return self._execute(
            "order.depth",
            [market, limit, interval]
        )

    def order_pending(self, user_id, market, offset, limit):
        """
        Inquire unexecuted orders:
        method: order.pending

        :param user_id: user ID，Integer
        :param market: market name，String
        :param offset: offset，Integer
        :param limit: limit，Integer

        :return:
            "params": [1, "BTCCNY", 0, 100]"
            "result": {
                "offset": 0,
                "limit": 100,
                "total": 1,
                "records": [
                    {
                        "id": 2,
                        "ctime": 1492616173.355293,
                        "mtime": 1492697636.238869,
                        "market": "BTCCNY",
                        "user": 2,
                        "type": 1, // 1: limit order，2：market order
                        "side": 2, // 1：sell，2：buy
                        "amount": "1.0000".
                        "price": "7000.00",
                        "taker_fee": "0.0020",
                        "maker_fee": "0.0010",
                        "source": "web",
                        "deal_money": "6300.0000000000",
                        "deal_stock": "0.9000000000",
                        "deal_fee": "0.0009000000"
                    }
                ]
            }

        """
        return self._execute(
            "order.pending",
            [user_id, market, offset, limit]
        )

    def order_pending_detail(self, market, order_id):
        """
        Unexecuted order details:
        method: order.pending_detail

        :param market: market name，String
        :param order_id: order ID，Integer

        """
        return self._execute(
            "order.pending_detail",
            [market, order_id]
        )

    def order_finished(self, user_id, market, start_time, end_time, offset, limit, side):
        """
        Inquire executed orders:
        method: order.finished

        :param user_id: user ID，Integer
        :param market: market name，String
        :param start_time: start time，0 for unlimited，Integer
        :param end_time: end time，0 for unlimited, Integer
        :param offset: offset，Integer
        :param limit: limit，Integer
        :param side: side，0 for no limit，1 for sell，2 for buy

        """
        return self._execute(
            "order.finished",
            [user_id, market, start_time, end_time, offset, limit, side]
        )

    def order_finished_detail(self, order_id):
        """
        Executed order details:
        method: order.finished_detail

        :param order_id: order ID，Integer

        """
        return self._execute(
            "order.finished_detail",
            [order_id]
        )

    """
        Market APIs:
    """

    def market_last(self, market):
        """
        Market price:
        method: market.last

        :param market

        :return: "price"
        """
        return self._execute(
            "market.last",
            [market]
        )

    def market_deals(self, market, limit, last_id):
        """
        Executed history:
        method: market.deals

        :param market
        :param limit: count，no more than 10000
        :param last_id: count，no more than 10000

        :return: "result": [
                    {
                        "id": 5,
                        "time": 1492697636.238869,
                        "type": "sell",
                        "amount": "0.1000",
                        "price": "7000.00"
                    },
                    {
                        "id": 4,
                        "time": 1492697467.1411841,
                        "type": "sell",
                        "amount": "0.1000"
                        "price": "7000.00",
                    }
                ]
        """
        return self._execute(
            "market.deals",
            [market, limit, last_id]
        )

    def market_user_deals(self, user_id, market, offset, limit):
        """
        User Executed history:
        method: market.user_deals

        :param user_id: user ID，Integer
        :param market: market name，String
        :param offset: offset，Integer
        :param limit: limit，Integer

        :return: "result": [
                        "offset":
                        "limit":
                        "records": [
                            {
                                "id": Executed ID
                                "time": timestamp
                                "user": user ID
                                "side": side，1：sell，2：buy
                                "role": role，1：Maker, 2: Taker
                                "amount": count
                                "price": price
                                "deal": amount
                                "fee": fee
                                "deal_order_id": Counterpart Transaction ID
                            }
                        ...
                        ]
                    ]
        """
        return self._execute(
            "market.user_deals",
            [user_id, market, offset, limit]
        )

    def market_kline(self, market, start, end, interval):
        """
        KLine:
        method: market.kline

        :param market: market name，String
        :param start: start，Integer
        :param end: end，Integer
        :param interval: interval，Integer

        :return: "result": [
                        [
                            1492358400, time
                            "7000.00",  open
                            "8000.0",   close
                            "8100.00",  highest
                            "6800.00",  lowest
                            "1000.00"   volume
                            "123456.78" amount
                            "BTCCNY"    market name
                        ]
                    ]
        """
        return self._execute(
            "market.kline",
            [market, start, end, interval]
        )

    def market_status(self, market, period):
        """
        Market status:
        method: market.status

        :param market: market name，String
        :param period: cycle period，Integer, e.g. 86400 for last 24 hours

        :return: "result": {
                        "period": 86400,
                        "last": "7000.00",
                        "open": "0",
                        "close": "0",
                        "high": "0",
                        "low": "0",
                        "volume": "0"
                    }
        """
        return self._execute(
            "market.status",
            [market, period]
        )

    def market_status_today(self, market):
        """
        Market status today:
        method: market.status_today

        :param market: market name，String

        :return: {
                    "open": Open today
                    "last": Latest price
                    "high": Highest price
                    "low":  Lowest price
                    "deal": 24H amount
                    "volume": 24H volume
                }
        """
        return self._execute(
            "market.status_today",
            [market]
        )

    def market_list(self):
        """
        Market list:
        method: market.list

        :return:
        """
        return self._execute(
            "market.list",
            []
        )

    def market_summary(self, market):
        """
        Market summary:
        method: market.summary

        :param market: list, return to market if null

        :return:
        """
        return self._execute(
            "market.summary",
            [market]
        )


class StexchangeException(BaseException):
    def __init__(self, message):
        """
        :param message: error message
        """
        logger.error(f"Stexchange RPC Error: {message}")


class StexchangeUnknownException(StexchangeException):
    def __init__(self, message=""):
        super(StexchangeUnknownException, self).__init__(f"unknown exception: {message}")


class InvalidArgumentException(StexchangeException):
    def __init__(self, _id):
        super(InvalidArgumentException, self).__init__(f"id: ${_id} invalid argument")


class InternalErrorException(StexchangeException):
    def __init__(self, _id):
        super(InternalErrorException, self).__init__(f"id: ${_id} internal error")


class ServiceUnavailableException(StexchangeException):
    def __init__(self, _id):
        super(ServiceUnavailableException, self).__init__(f"id: ${_id} service unavailable")


class MethodNotFoundException(StexchangeException):
    def __init__(self, _id):
        super(MethodNotFoundException, self).__init__(f"id: ${_id} method not found")


class ServiceTimoutException(StexchangeException):
    def __init__(self, _id):
        super(ServiceTimoutException, self).__init__(f"id: ${_id} service timeout")


class OrderNotFoundException(StexchangeException):
    def __init__(self, _id):
        super(OrderNotFoundException, self).__init__(f"id: ${_id} order not found")


class UserNotMatchException(StexchangeException):
    def __init__(self, _id):
        super(UserNotMatchException, self).__init__(f"id: ${_id} user not match")


class RepeatUpdateException(StexchangeException):
    def __init__(self, _id):
        super(RepeatUpdateException, self).__init__(f"id: ${_id} repeat update")


class BalanceNotEnoughException(StexchangeException):
    def __init__(self, _id):
        super(BalanceNotEnoughException, self).__init__(f"id: ${_id} balance not enough")


class MockStexchangeClient(StexchangeClient):

    def balance_query(self, user_id, *asset_name):
        return super().balance_query(user_id, *asset_name)

    def balance_update(self, user_id, asset, business, business_id, change, detail):
        return super().balance_update(user_id, asset, business, business_id, change, detail)

    def balance_history(self, user_id, asset=None, business=None, start_time=0, end_time=0, offset=0, limit=0):
        return super().balance_history(user_id, asset, business, start_time, end_time, offset, limit)

    def asset_list(self):
        return super().asset_list()

    def asset_summary(self):
        return super().asset_summary()

    def order_put_limit(self, user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source):
        return super().order_put_limit(user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source)

    def order_put_market(self, user_id, market, side, amount, taker_fee_rate, source):
        return super().order_put_market(user_id, market, side, amount, taker_fee_rate, source)

    def order_cancel(self, user_id, market, order_id):
        return super().order_cancel(user_id, market, order_id)

    def order_deals(self, order_id, offset, limit):
        return super().order_deals(order_id, offset, limit)

    def order_book(self, market, side, offset, limit):
        return super().order_book(market, side, offset, limit)

    def order_depth(self, market, limit, interval):
        return super().order_depth(market, limit, interval)

    def order_pending(self, user_id, market, offset, limit):
        return super().order_pending(user_id, market, offset, limit)

    def order_pending_detail(self, market, order_id):
        return super().order_pending_detail(market, order_id)

    def order_finished(self, user_id, market, start_time, end_time, offset, limit, side):
        return super().order_finished(user_id, market, start_time, end_time, offset, limit, side)

    def order_finished_detail(self, order_id):
        return super().order_finished_detail(order_id)

    def market_last(self, market):
        return super().market_last(market)

    def market_deals(self, market, limit, last_id):
        return super().market_deals(market, limit, last_id)

    def market_user_deals(self, user_id, market, offset, limit):
        return super().market_user_deals(user_id, market, offset, limit)

    def market_kline(self, market, start, end, interval):
        return super().market_kline(market, start, end, interval)

    def market_status(self, market, period):
        return super().market_status(market, period)

    def market_status_today(self, market):
        return super().market_status_today(market)

    def market_list(self):
        return super().market_list()

    def market_summary(self, market):
        return super().market_summary(market)


STEXCHANEG_GENERAL_ERROR_CODE_MAP = {
    1: InvalidArgumentException,
    2: InternalErrorException,
    3: ServiceUnavailableException,
    4: MethodNotFoundException,
    5: ServiceTimoutException,
}

if __name__ == '__main__':
    sx = StexchangeClient(server_url="http://localhost:8080")

    print(sx.balance_update(1, "TESTNET3", None, int(time.time()), "100", {}))
    print(sx.balance_update(1, "RINKEBY", None, int(time.time()), "100", {}))
    print(sx.balance_query(1, "TESTNET3"))
    print(sx.balance_history(1, "TESTNET3", None, 0, 0, 0, 10))

    print(sx.asset_summary())
    print(sx.asset_list())

    print(sx.market_list())
    print(sx.market_deals("TESTNET3RINKEBY", 10, 3))
    print(sx.market_user_deals(1, "TESTNET3RINKEBY", 0, 10))
    print(sx.market_last("TESTNET3RINKEBY"))
    print(sx.market_kline("TESTNET3RINKEBY", int(time.time()) - 1000, int(time.time()), 86400))
    print(sx.market_status("TESTNET3RINKEBY", 86400))
    print(sx.market_status_today("TESTNET3RINKEBY"))
    print(sx.market_summary("TESTNET3RINKEBY"))

    order = sx.order_put_limit(1, "TESTNET3RINKEBY", 2, "100", "2", "0.1", "0.1", "abc")

    print(order)
    print(sx.order_put_market(1, "TESTNET3RINKEBY", 1, "3", "0.1", "cbd"))
    print(sx.order_book("TESTNET3RINKEBY", 1, 0, 10))
    print(sx.order_pending(1, "TESTNET3RINKEBY", 0, 10))
    print(sx.order_pending_detail("TESTNET3RINKEBY", order["id"]))
    print(sx.order_finished(1, "TESTNET3RINKEBY", 0, 0, 0, 20, 1))
    print(sx.order_finished_detail(57))
    print(sx.order_deals(order["id"], 0, 10))
    print(sx.order_depth("TESTNET3RINKEBY", 100, "1"))
    print(sx.order_cancel(1, "TESTNET3RINKEBY", order["id"]))

    """
    Sample results:
    
    * {'status': 'success'}
    * {'status': 'success'}
    * {'TESTNET3': {'available': '9137.8', 'freeze': '0'}}
    * {'offset': 0, 'limit': 10, 'records': [{'time': 1547419212.987738, 'asset': 'TESTNET3', 'balance': '9137.8', 'change': '100', 'business': 'null', 'detail': {'id': 1547419212}}, {'time': 1547419172.410369, 'asset': 'TESTNET3', 'balance': '9038.4', 'change': '100', 'business': 'null', 'detail': {'id': 1547419172}}, {'time': 1547419117.182499, 'asset': 'TESTNET3', 'balance': '8939', 'change': '100', 'business': 'null', 'detail': {'id': 1547419117}}, {'time': 1547419093.216783, 'asset': 'TESTNET3', 'balance': '8839.6', 'change': '100', 'business': 'null', 'detail': {'id': 1547419093}}, {'time': 1547419090.127026, 'asset': 'TESTNET3', 'balance': '8740.2', 'change': '100', 'business': 'null', 'detail': {'id': 1547419090}}, {'time': 1547419079.001812, 'asset': 'TESTNET3', 'balance': '8640.8', 'change': '100', 'business': 'null', 'detail': {'id': 1547419078}}, {'time': 1547419050.210154, 'asset': 'TESTNET3', 'balance': '8541', 'change': '100', 'business': 'null', 'detail': {'id': 1547419050}}, {'time': 1547419045.657284, 'asset': 'TESTNET3', 'balance': '8441.2', 'change': '100', 'business': 'null', 'detail': {'id': 1547419045}}, {'time': 1547419044.539546, 'asset': 'TESTNET3', 'balance': '8341.4', 'change': '100', 'business': 'null', 'detail': {'id': 1547419044}}, {'time': 1547419042.979995, 'asset': 'TESTNET3', 'balance': '8241.6', 'change': '100', 'business': 'null', 'detail': {'id': 1547419042}}]}
    * [{'freeze_count': 0, 'name': 'RINKEBY', 'total_balance': '1996.3', 'available_count': 1, 'freeze_balance': '0', 'available_balance': '1996.3'}, {'freeze_count': 0, 'name': 'TESTNET3', 'total_balance': '9137.8', 'available_count': 1, 'freeze_balance': '0', 'available_balance': '9137.8'}]
    * [{'name': 'RINKEBY', 'prec': 8}, {'name': 'TESTNET3', 'prec': 8}]

    * [{'name': 'TESTNET3RINKEBY', 'stock': 'RINKEBY', 'stock_prec': 8, 'money': 'TESTNET3', 'fee_prec': 4, 'min_amount': '0.00001', 'money_prec': 8}]
    * [{'id': 27, 'time': 1547419172.446089, 'price': '2', 'amount': '3', 'type': 'sell'}, {'id': 26, 'time': 1547419117.217958, 'price': '2', 'amount': '3', 'type': 'sell'}, {'id': 25, 'time': 1547419093.255915, 'price': '2', 'amount': '3', 'type': 'sell'}, {'id': 24, 'time': 1547419090.164703, 'price': '2', 'amount': '3', 'type': 'sell'}, {'id': 23, 'time': 1547419079.117212, 'price': '2', 'amount': '3', 'type': 'sell'}, {'id': 22, 'time': 1547419050.312692, 'price': '2', 'amount': '1', 'type': 'sell'}, {'id': 21, 'time': 1547419045.695404, 'price': '2', 'amount': '1', 'type': 'sell'}, {'id': 20, 'time': 1547419044.574597, 'price': '2', 'amount': '1', 'type': 'sell'}, {'id': 19, 'time': 1547419043.018591, 'price': '2', 'amount': '1', 'type': 'sell'}, {'id': 18, 'time': 1547419014.44956, 'price': '88', 'amount': '1', 'type': 'sell'}]
    * {'offset': 0, 'limit': 10, 'records': [{'time': 1547419172.446089, 'id': 27, 'side': 2, 'price': '2', 'user': 1, 'fee': '0.3', 'role': 1, 'amount': '3', 'deal': '6', 'deal_order_id': 61}, {'time': 1547419172.446089, 'id': 27, 'side': 1, 'price': '2', 'user': 1, 'fee': '0.6', 'role': 2, 'amount': '3', 'deal': '6', 'deal_order_id': 60}, {'time': 1547419117.217958, 'id': 26, 'side': 2, 'price': '2', 'user': 1, 'fee': '0.3', 'role': 1, 'amount': '3', 'deal': '6', 'deal_order_id': 59}, {'time': 1547419117.217958, 'id': 26, 'side': 1, 'price': '2', 'user': 1, 'fee': '0.6', 'role': 2, 'amount': '3', 'deal': '6', 'deal_order_id': 58}, {'time': 1547419093.255915, 'id': 25, 'side': 2, 'price': '2', 'user': 1, 'fee': '0.3', 'role': 1, 'amount': '3', 'deal': '6', 'deal_order_id': 57}, {'time': 1547419093.255915, 'id': 25, 'side': 1, 'price': '2', 'user': 1, 'fee': '0.6', 'role': 2, 'amount': '3', 'deal': '6', 'deal_order_id': 56}, {'time': 1547419090.164703, 'id': 24, 'side': 2, 'price': '2', 'user': 1, 'fee': '0.3', 'role': 1, 'amount': '3', 'deal': '6', 'deal_order_id': 55}, {'time': 1547419090.164703, 'id': 24, 'side': 1, 'price': '2', 'user': 1, 'fee': '0.6', 'role': 2, 'amount': '3', 'deal': '6', 'deal_order_id': 54}, {'time': 1547419079.117212, 'id': 23, 'side': 2, 'price': '2', 'user': 1, 'fee': '0.3', 'role': 1, 'amount': '3', 'deal': '6', 'deal_order_id': 53}, {'time': 1547419079.117212, 'id': 23, 'side': 1, 'price': '2', 'user': 1, 'fee': '0.6', 'role': 2, 'amount': '3', 'deal': '6', 'deal_order_id': 52}]}
    * 2.00000000
    * [[1547337600, '88', '2', '88', '2', '37', '1622', 'TESTNET3RINKEBY']]
    * {'low': '2', 'period': 86400, 'deal': '1622', 'high': '88', 'last': '2', 'open': '88', 'close': '2', 'volume': '37'}
    * {'open': '88', 'deal': '1622', 'high': '88', 'last': '2', 'low': '2', 'volume': '37'}
    * [{'name': 'TESTNET3RINKEBY', 'bid_amount': '0', 'bid_count': 0, 'ask_count': 0, 'ask_amount': '0'}]

    * {'price': '2', 'id': 62, 'side': 2, 'market': 'TESTNET3RINKEBY', 'taker_fee': '0.1', 'type': 1, 'deal_fee': '0', 'deal_stock': '0', 'maker_fee': '0.1', 'source': 'abc', 'user': 1, 'left': '100', 'ctime': 1547419213.026914, 'mtime': 1547419213.026914, 'amount': '100', 'deal_money': '0'}
    * {'price': '0', 'id': 63, 'side': 1, 'market': 'TESTNET3RINKEBY', 'taker_fee': '0.1', 'type': 2, 'deal_fee': '0.6', 'deal_stock': '3', 'maker_fee': '0', 'source': 'cbd', 'user': 1, 'left': '0e-8', 'ctime': 1547419213.029479, 'mtime': 1547419213.029483, 'amount': '3', 'deal_money': '6'}
    * {'offset': 0, 'orders': [], 'limit': 10, 'total': 0}
    * {'limit': 10, 'offset': 0, 'total': 1, 'records': [{'price': '2', 'id': 62, 'side': 2, 'market': 'TESTNET3RINKEBY', 'taker_fee': '0.1', 'type': 1, 'deal_fee': '0.3', 'deal_stock': '3', 'maker_fee': '0.1', 'source': 'abc', 'user': 1, 'left': '97', 'ctime': 1547419213.026914, 'mtime': 1547419213.029483, 'amount': '100', 'deal_money': '6'}]}
    * {'price': '2', 'id': 62, 'side': 2, 'market': 'TESTNET3RINKEBY', 'taker_fee': '0.1', 'type': 1, 'deal_fee': '0.3', 'deal_stock': '3', 'maker_fee': '0.1', 'source': 'abc', 'user': 1, 'left': '97', 'ctime': 1547419213.026914, 'mtime': 1547419213.029483, 'amount': '100', 'deal_money': '6'}
    * {'offset': 0, 'limit': 20, 'records': [{'id': 61, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419172.446086, 'ftime': 1547419172.446089, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}, {'id': 59, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419117.217955, 'ftime': 1547419117.217958, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}, {'id': 57, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419093.255911, 'ftime': 1547419093.255915, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}, {'id': 55, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419090.1647, 'ftime': 1547419090.164703, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}, {'id': 53, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419079.117208, 'ftime': 1547419079.117212, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}, {'id': 51, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '2', 'ctime': 1547419050.312686, 'ftime': 1547419050.312692, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '0.2'}, {'id': 49, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '2', 'ctime': 1547419045.695398, 'ftime': 1547419045.695404, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '0.2'}, {'id': 47, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '2', 'ctime': 1547419044.574593, 'ftime': 1547419044.574597, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '0.2'}, {'id': 45, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '2', 'ctime': 1547419043.018587, 'ftime': 1547419043.018591, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '0.2'}, {'id': 43, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '88', 'ctime': 1547419014.449556, 'ftime': 1547419014.44956, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '8.8'}, {'id': 41, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '88', 'ctime': 1547419005.914382, 'ftime': 1547419005.914387, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '8.8'}, {'id': 39, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '88', 'ctime': 1547418994.681865, 'ftime': 1547418994.681873, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '8.8'}, {'id': 37, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '88', 'ctime': 1547418971.478641, 'ftime': 1547418971.478644, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '1', 'deal_fee': '8.8'}, {'id': 35, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '176', 'ctime': 1547418955.745287, 'ftime': 1547418955.745518, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '2', 'deal_fee': '17.6'}, {'id': 33, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '264', 'ctime': 1547418943.696649, 'ftime': 1547418943.697126, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '26.4'}, {'id': 31, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '264', 'ctime': 1547418864.639109, 'ftime': 1547418864.639465, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '26.4'}, {'id': 29, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '264', 'ctime': 1547418683.910061, 'ftime': 1547418683.910436, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '26.4'}, {'id': 27, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '264', 'ctime': 1547418339.31098, 'ftime': 1547418339.311348, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '26.4'}]}
    * {'id': 57, 'source': 'cbd', 'side': 1, 'type': 2, 'deal_money': '6', 'ctime': 1547419093.255911, 'ftime': 1547419093.255915, 'user': 1, 'market': 'TESTNET3RINKEBY', 'price': '0', 'amount': '3', 'taker_fee': '0.1', 'maker_fee': '0', 'deal_stock': '3', 'deal_fee': '0.6'}
    * {'offset': 0, 'limit': 10, 'records': []}
    * {'asks': [], 'bids': [['2', '97']]}
    * {'price': '2', 'id': 62, 'side': 2, 'market': 'TESTNET3RINKEBY', 'taker_fee': '0.1', 'type': 1, 'deal_fee': '0.3', 'deal_stock': '3', 'maker_fee': '0.1', 'source': 'abc', 'user': 1, 'left': '97', 'ctime': 1547419213.026914, 'mtime': 1547419213.029483, 'amount': '100', 'deal_money': '6'}
    """
