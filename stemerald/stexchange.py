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
        return {"method": method, "params": params, "id": self.next_request_id()}

    def get_market_last(self, market):
        """
        Market price
        method: market.last
        :param market
        :return: "price"
        """
        return requests.post(self, data=json.dumps(self.payload("market.last", [market]), headers=self.headers)).json()

    def get_market_deals(self, market, limit, last_id):
        """
        Market price
        method: market.last
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
        return requests.post(self, data=json.dumps(self.payload("market.last", [market, limit, last_id]),
                                                   headers=self.headers)).json()

    def get_market_deals(self, market):
        return requests.post(self, data=json.dumps(self.payload("market.list", [market]), headers=self.headers)).json()

    def get_market_list(self, market):
        return requests.post(self, data=json.dumps(self.payload("market.list", [market]), headers=self.headers)).json()

    def get_market_list(self, market):
        return requests.post(self, data=json.dumps(self.payload("market.list", [market]), headers=self.headers)).json()
