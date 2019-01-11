from typing import Union

from nanohttp import json
from nanohttp.exceptions import HttpNotFound

from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.orm import commit
from restfulpy.validation import validate_form, prevent_form

from staemerald.models.trading import Market

BidId = Union[int, str]
TradeId = Union[int, str]


class MarketController(ModelRestController):
    __model__ = Market

    @json
    @validate_form(
        whitelist=['sort', 'id', 'baseCurrencyId', 'quoteCurrencyId'],
        pattern={'sort': r'^(-)?(id|baseCurrencyId|quoteCurrencyId)$'}
    )
    @__model__.expose
    def get(self, market_id: int = None):
        if market_id is None:
            return Market.query

        else:
            market = Market.query.filter(Market.id == market_id).one_or_none()
            if market is None:
                raise HttpNotFound('Market not found', 'market-not-found')

            return market.to_dict()

    @json
    @authorize('admin')
    @validate_form(
        whitelist=['buyAmountMin', 'buyAmountMax', 'buyStaticCommission', 'buyStaticCommission',
                   'buyPermilleCommission', 'buyMaxCommission', 'sellAmountMin', 'sellAmountMax',
                   'sellStaticCommission', 'sellPermilleCommission', 'sellMaxCommission']
    )
    @__model__.expose
    @commit
    def edit(self, market_id: int):
        market = Market.query.filter(Market.id == market_id).one_or_none()

        if market is None:
            raise HttpNotFound()

        market.update_from_request()
        return market

    @json
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    def present(self, market_id: int, inner_resource: str):
        # TODO
        pass

    @json
    @authorize('admin', 'client')
    @validate_form(exact=['type', 'price', 'amount'], types={'price': int, 'amount': int, 'marketId': int})
    def calculate(self, market_id: int):
        # TODO
        pass


class OrderController(ModelRestController):
    __model__ = None

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(whitelist=['id', 'clientId', 'status', 'marketId'], client={'blacklist': ['clientId']})
    @__model__.expose
    def get(self):
        # TODO
        pass

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    @prevent_form
    @commit
    def cancel(self, order_id: int):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['price'], types={'price': int})
    @commit
    def edit(self, order_id: int):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['marketId', 'type', 'price', 'amount'], types={'price': int, 'amount': int, 'marketId': int})
    @commit
    def create(self):
        # TODO
        pass

    @json
    @validate_form(whitelist=['take'], types={'take': int})
    def present(self, market_id: int, type_: str):
        # TODO
        pass


class TradeController(ModelRestController):
    __model__ = None

    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['sort', 'take', 'skip'],
        admin={'whitelist': ['id', 'clientId', 'marketId', 'isDone', 'type', 'price', 'amount', 'createdAt']},
        pattern={'sort': r'^(-)?(id|clientId|marketId|doneAt|isDone|type|price|amount)$'}
    )
    @__model__.expose
    def get(self, trade_id: int = None):
        # TODO
        pass
