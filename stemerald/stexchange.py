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

    def payload(self, method, params):
        return json.dumps({"method": method, "params": params, "id": self._next_request_id()})

    def _execute(self, method, params):
        return requests.post(self, data=self.payload(method, params), headers=self.headers).json()

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
            [user_id, asset, business, business_id, change, detail]
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
            [1, "BTCCNY", 1, "10", "8000", "0.002", "0.001"]

        :raise BalanceNotEnough: balance not enough

        """
        return self._execute(
            "order.put_limit",
            [user_id, market, side, amount, price, taker_fee_rate, maker_fee_rate, source]
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
            [1, "BTCCNY", 1, "10","0.002"]

        :raise BalanceNotEnough: balance not enough

        """
        return self._execute(
            "market.put_limit",
            [user_id, market, side, amount, taker_fee_rate, source]
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
            "market.put_limit",
            [user_id, market, order_id]
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
        params = [market]
        return requests.post(self, data=self.payload("market.last", params), headers=self.headers).json()

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
        params = [market, limit, last_id]
        return requests.post(self, data=self.payload("market.deals", params), headers=self.headers).json()

    def market_user_deals(self, user_id, market, offset, limit):
        """
        Executed history:
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
        params = [user_id, market, offset, limit]
        return requests.post(self,
                             data=self.payload("market.user_deals", params), headers=self.headers).json()

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
        params = [market, start, end, interval]
        return requests.post(self, data=self.payload("market.kline", params), headers=self.headers).json()

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
        params = [market, period]
        return requests.post(self,
                             data=self.payload("market.status_today", params), headers=self.headers).json()

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
        params = [market]
        return requests.post(self,
                             data=self.payload("market.status_today", params), headers=self.headers).json()

    def market_list(self):
        """
        Market list:
        method: market.list

        :return:
        """
        params = []
        return requests.post(self, data=self.payload("market.list", params), headers=self.headers).json()

    def market_summary(self, market):
        """
        Market summary:
        method: market.summary

        :param market: list, return to market if null

        :return:
        """
        params = [market]
        return requests.post(self, data=self.payload("market.summary", params), headers=self.headers).json()


class StexchangeException(Exception):
    def __init__(self, title):
        logger.error(f"Stexchange RPC Error: {title}")


class InvalidArgumentException(StexchangeException):
    pass


class InternalErrorException(StexchangeException):
    pass


class ServiceNotAvailableException(StexchangeException):
    pass


class MethodNotFoundException(StexchangeException):
    pass


class ServiceTimoutException(StexchangeException):
    pass


class OrderNotFoundException(StexchangeException):
    pass


class UserNotMatchException(StexchangeException):
    pass


class RepeatUpdateException(StexchangeException):
    pass


class BalanceNotEnoughException(StexchangeException):
    pass
