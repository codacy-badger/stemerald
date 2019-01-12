import json

import requests
from nanohttp import settings
from restfulpy.logging_ import get_logger

logger = get_logger('STEXCHANGE_RPC_CLIENT')


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
        payload = json.dumps({"method": method, "params": params, "id": self._next_request_id()})

        logger.debug(f"Requesting {method} with id:{params['id']} with parameters: {'.'.join(params)}")

        try:
            response = requests.post(self, data=payload, headers=self.headers).json()
        except Exception as e:
            raise StexchangeUnknownException(f"Request error: {str(e)}")

        if response["error"] is not None and len(response["error"] > 0):
            error_mapper = error_mapper or {}
            error_mapper.update(STEXCHANEG_GENERAL_ERROR_CODE_MAP)
            raise (
                error_mapper[response["code"]](response["id"]) if (response["code"] in error_mapper)
                else StexchangeUnknownException(f"id: {response['id']} Unknown error code: {response['code']}")
            )

        elif response["result"] is not None and len(response["result"] > 0):
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
            {10: RepeatUpdateException.__class__, 11: BalanceNotEnoughException}
        )

    def balance_history(self, user_id, asset, business, start_time, end_time, offset, limit):
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
            "market.put_limit",
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
            {10: OrderNotFoundException.__class__, 11: UserNotMatchException}
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


class StexchangeException(Exception):
    def __init__(self, message):
        """
        :param message: error message
        """
        logger.error(f"Stexchange RPC Error: {message}")


class StexchangeUnknownException(Exception):
    def __init__(self, message=""):
        super(f"unknown exception: {message}")


class InvalidArgumentException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} invalid argument")


class InternalErrorException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} internal error")


class ServiceUnavailableException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} service unavailable")


class MethodNotFoundException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} method not found")


class ServiceTimoutException(StexchangeException):
    def __init__(self, _id):
        super(5, "service timeout")


class OrderNotFoundException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} order not found")


class UserNotMatchException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} user not match")


class RepeatUpdateException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} repeat update")


class BalanceNotEnoughException(StexchangeException):
    def __init__(self, _id):
        super(f"id: ${_id} balance not enough")


STEXCHANEG_GENERAL_ERROR_CODE_MAP = {
    1: InvalidArgumentException.__class__,
    2: InternalErrorException.__class__,
    3: ServiceUnavailableException.__class__,
    4: MethodNotFoundException.__class__,
    5: ServiceTimoutException.__class__,
}
