from nanohttp import RestController, json, context
from restfulpy.authorization import authorize
from restfulpy.validation import prevent_form, validate_form

from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class MarketController(RestController):

    @authorize('client')
    def _peek_me(self, market):
        try:
            return stexchange_client.market_user_deals(
                context.identity.id, market, int(context.query_string['limit']), int(context.query_string['offset'])
            )
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @validate_form(whitelist=['limit', 'lastId', 'offset'])
    def peek(self, market: str, inner_resource: str, inner_resource2: str = None):
        if inner_resource == 'deals':
            if inner_resource2 == 'me':
                return self._peek_me(market)
            else:
                try:
                    response = stexchange_client.market_deals(
                        market, int(context.query_string['limit']), int(context.query_string['lastId'])
                    )
                except StexchangeException as e:
                    raise stexchange_http_exception_handler(e)

                return [
                    {
                        'id': deal['id'],
                        'time': deal['time'],
                        'price': deal['price'],
                        'amount': deal['amount'],
                        'type': deal['type'],
                    } for deal in response
                ]

    @json
    @prevent_form
    def list(self):
        try:
            response = stexchange_client.market_list()
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [
            {
                'name': market['name'],
                'stock': market['stock'],
                'stockPrec': market['stock_prec'],
                'money': market['money'],
                'feePrec': market['fee_prec'],
                'minAmount': market['min_amount'],
                'moneyPrec': market['money_prec'],
            } for market in response
        ]

    @json
    @prevent_form
    def last(self, market: str):
        try:
            return {
                'name': market,
                'price': stexchange_client.market_last(market),
            }
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @prevent_form
    def summary(self, market: str):
        try:
            response = stexchange_client.market_summary(market)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [
            {
                'name': market['name'],
                'bidAmount': market['bid_amount'],
                'bidCount': market['bid_count'],
                'askAmount': market['ask_amount'],
                'askCount': market['ask_count'],
            } for market in response
        ]

    @json
    @validate_form(exact=['period'])
    def status(self, market: str):
        period = context.query_string.get('period')

        try:
            if period == 'today':
                status = stexchange_client.market_status_today(market)
            else:
                status = stexchange_client.market_status(market, int(period))
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return {
            'open': status['open'],
            'high': status['high'],
            'low': status['low'],
            'close': status.get('close', None),
            'volume': status['volume'],
            'deal': status['deal'],
            'last': status['last'],
            'period': status.get('period', None),
        }
