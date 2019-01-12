import json

import requests
from nanohttp import settings


class StexchangeClient:

    def __init__(self, server_url=None, headers=None):
        self.server_url = server_url or settings.stexchange.rpc_url
        self.headers = {'content-type': 'application/json'}
        self.headers.update(headers or {})
        self.request_id = 0

    def next_request_id(self):
        self.request_id += 1
        return self.request_id

    def payload(self, method, params):
        return json.dumps({"method": method, "params": params, "id": self.next_request_id()})

    """
        Market APIs:
    """

    def get_market_last(self, market):
        """
        Market price:
        method: market.last
        :param market
        :return: "price"
        """
        params = [market]
        return requests.post(self, data=self.payload("market.last", params), headers=self.headers).json()

    def get_market_deals(self, market, limit, last_id):
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

    def get_market_user_deals(self, user_id, market, offset, limit):
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

    def get_market_kline(self, market, start, end, interval):
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

    def get_market_status(self, market, period):
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

    def get_market_status_today(self, market):
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

    def get_market_list(self):
        """
        Market list:
        method: market.list

        :return:
        """
        params = []
        return requests.post(self, data=self.payload("market.list", params), headers=self.headers).json()

    def get_market_summary(self, market):
        """
        Market summary:
        method: market.summary

        :param market: list, return to market if null

        :return:
        """
        params = [market]
        return requests.post(self, data=self.payload("market.summary", params), headers=self.headers).json()
