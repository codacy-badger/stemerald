from typing import Union

from nanohttp import json, RestController, context, HttpNotFound, HttpBadRequest

from restfulpy.authorization import authorize
from restfulpy.validation import validate_form

from stemerald import stexchange_client
from stemerald.models import Market
from stemerald.stexchange import StexchangeException, stexchange_http_exception_handler

BidId = Union[int, str]
TradeId = Union[int, str]


def order_to_dict(o):
    return {
        'id': o['id'],
        'ctime': o['ctime'],
        'mtime': o['mtime'],
        'market': o['market'],
        'user': o['user'],
        'type': 'limit' if o['type'] == 1 else 'market',
        'side': 'sell' if o['side'] == 1 else 'buy',
        'amount': o['amount'],
        'price': o['price'],
        'takerFee': o['taker_fee'],
        'makerFee': o['maker_fee'],
        'source': o['source'],
        'dealMoney': o['deal_money'],
        'dealStock': o['deal_stock'],
        'dealFee': o['deal_fee'],
    }


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
    def get(self, order_id: int = None):
        client_id = context.identity.id if context.identity.is_in_roles(['client']) \
            else context.query_string['clientId']

        try:
            if order_id is None:
                offset = context.query_string.get('offset', 0)
                limit = min(context.query_string.get('limit', 10), 10)

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

                return [order_to_dict(order) for order in orders['records']]

            else:
                if context.query_string['status'] == 'pending':
                    order = stexchange_client.order_pending_detail(
                        market=context.query_string['marketName'],
                        order_id=order_id,
                    )
                elif context.query_string['status'] == 'finished':
                    order = stexchange_client.order_finished_detail(
                        order_id=order_id,
                    )
                else:
                    raise HttpNotFound('Bad status.')

                return order_to_dict(order)

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

            return order_to_dict(order)

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
        exact=['marketName', 'type', 'price', 'amount', 'side'],
        types={'price': int, 'amount': int, 'marketName': int},
        pattern={'type': r'^(-)?(market|limit)$', 'side': r'^(-)?(buy|sell)$', }
    )
    def create(self):
        client_id = context.identity.id

        market = Market.query.filter(Market.name == context.form['marketName']).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        side = 1 if (context.form['side'] == 'sell') else 2

        price = context.form['price']
        amount = context.form['amount']
        market.validate_ranges(type_=context.form['side'], total_amount=amount, price=price)

        try:
            if context.form['type'] == 'market':
                order = stexchange_client.order_put_market(
                    user_id=client_id,
                    market=market.name,
                    side=side,
                    amount=str(amount),
                    taker_fee_rate=market.taker_commission_rate,
                    source="nothing",  # FIXME
                )
            elif context.form['status'] == 'limit':
                order = stexchange_client.order_put_limit(
                    user_id=client_id,
                    market=market.name,
                    side=side,
                    amount=str(amount),
                    price=str(price),
                    taker_fee_rate=market.taker_commission_rate,
                    maker_fee_rate=market.maker_commission_rate,
                    source="nothing",  # FIXME
                )
            else:
                raise HttpNotFound('Bad status.')

            return order_to_dict(order)

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @validate_form(whitelist=['take'], types={'take': int})
    def present(self, market_id: int, type_: str):
        # FIXME
        raise HttpBadRequest("Deprecated.")


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
