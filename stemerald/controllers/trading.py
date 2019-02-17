from typing import Union

from nanohttp import json, RestController

from restfulpy.authorization import authorize
from restfulpy.validation import validate_form, prevent_form

BidId = Union[int, str]
TradeId = Union[int, str]


class OrderController(RestController):

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(whitelist=['id', 'clientId', 'status', 'marketId'], client={'blacklist': ['clientId']})
    def get(self):
        # TODO
        pass

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    @prevent_form
    def cancel(self, order_id: int):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['price'], types={'price': int})
    def edit(self, order_id: int):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(
        exact=['marketId', 'type', 'price', 'amount'],
        types={'price': int, 'amount': int, 'marketId': int}
    )
    def create(self):

        pass

    @json
    @validate_form(whitelist=['take'], types={'take': int})
    def present(self, market_id: int, type_: str):
        # TODO
        pass


class TradeController(RestController):

    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['sort', 'take', 'skip'],
        admin={'whitelist': ['id', 'clientId', 'marketId', 'isDone', 'type', 'price', 'amount', 'createdAt']},
        pattern={'sort': r'^(-)?(id|clientId|marketId|doneAt|isDone|type|price|amount)$'}
    )
    def get(self, trade_id: int = None):
        # TODO
        pass
