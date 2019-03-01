from typing import Union

from nanohttp import json, RestController, context, HttpNotFound, HttpBadRequest

from restfulpy.authorization import authorize
from restfulpy.validation import validate_form, prevent_form

from stemerald import stexchange_client
from stemerald.stexchange import StexchangeException, stexchange_http_exception_handler

BidId = Union[int, str]
TradeId = Union[int, str]


class OrderController(RestController):

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        requires=['marketName', 'status'],
        whitelist=['clientId', 'status', 'marketName', 'offset', 'limit'],
        client={'blacklist': ['clientId']},
        admin={'requires': ['clientId']},
        pattern={'status': r'^(-)?(pending|finished)$'}
    )
    def get(self):
        client_id = context.identity.id if context.identity.is_in_roles(['client']) \
            else context.query_string['clientId']

        offset = context.query_string.get('offset', 0)
        limit = min(context.query_string.get('limit', 10), 10)

        try:
            if context.query_string['status'] == 'pending':
                orders = stexchange_client.order_pending(
                    user_id=client_id,
                    market=context.query_string['marketName'],
                    offset=offset,
                    limit=limit,
                )
            elif context.query_string['status'] == 'finished':
                orders = stexchange_client.order_finished(
                    user_id=client_id,
                    market=context.query_string['marketName'],
                    offset=offset,
                    limit=limit,
                    side=0,
                    start_time=0,
                    end_time=0,
                )
            else:
                raise HttpNotFound('Bad status.')

            return [
                {
                    'id': order['id'],
                    'ctime': order['ctime'],
                    'mtime': order['mtime'],
                    'market': order['market'],
                    'user': order['user'],
                    'type': 'limit' if order['type'] == 1 else 'market',
                    'side': 'sell' if order['side'] == 1 else 'buy',
                    'amount': order['amount'],
                    'price': order['price'],
                    'takerFee': order['taker_fee'],
                    'makerFee': order['maker_fee'],
                    'source': order['source'],
                    'dealMoney': order['deal_money'],
                    'dealStock': order['deal_stock'],
                    'dealFee': order['deal_fee'],
                } for order in orders['records']
            ]

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @authorize('admin', 'semitrusted_client', 'trusted_client')
    @validate_form(
        requires=['marketName'],
        whitelist=['clientId', 'marketName'],
        client={'blacklist': ['clientId']},
        admin={'requires': ['clientId']},
    )
    def cancel(self, order_id: int):
        client_id = context.identity.id if context.identity.is_in_roles(['client']) \
            else context.query_string['clientId']

        try:
            order = stexchange_client.order_cancel(
                user_id=client_id,
                market=context.query_string['marketName'],
                order_id=order_id,
            )

            return {
                'id': order['id'],
                'ctime': order['ctime'],
                'mtime': order['mtime'],
                'market': order['market'],
                'user': order['user'],
                'type': 'limit' if order['type'] == 1 else 'market',
                'side': 'sell' if order['side'] == 1 else 'buy',
                'amount': order['amount'],
                'price': order['price'],
                'takerFee': order['taker_fee'],
                'makerFee': order['maker_fee'],
                'source': order['source'],
                'dealMoney': order['deal_money'],
                'dealStock': order['deal_stock'],
                'dealFee': order['deal_fee'],
            }

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['price'], types={'price': int})
    def edit(self, order_id: int):
        # TODO
        raise HttpBadRequest('Not implemented yet.')

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(
        exact=['marketName', 'type', 'price', 'amount'],
        types={'price': int, 'amount': int, 'marketName': int}
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
        admin={'whitelist': ['id', 'clientId', 'marketName', 'isDone', 'type', 'price', 'amount', 'createdAt']},
        pattern={'sort': r'^(-)?(id|clientId|marketName|doneAt|isDone|type|price|amount)$'}
    )
    def get(self, trade_id: int = None):
        # TODO
        pass
