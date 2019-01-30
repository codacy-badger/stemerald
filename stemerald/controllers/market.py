from nanohttp import RestController, json, context
from restfulpy.validation import prevent_form, validate_form

from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class MarketController(RestController):

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
    @prevent_form
    def last(self, market: str):
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
