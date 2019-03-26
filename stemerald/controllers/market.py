from nanohttp import RestController, json, context, HttpBadRequest, HttpNotFound
from restfulpy.authorization import authorize
from restfulpy.validation import prevent_form, validate_form

from stemerald.math import format_number_to_pretty
from stemerald.models import Market
from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class MarketController(RestController):

    @authorize('client')
    def _peek_me(self, market):
        try:
            response = stexchange_client.market_user_deals(
                user_id=context.identity.id,
                market=market,
                offset=int(context.query_string['offset']),
                limit=int(context.query_string['limit'])
            )
            return [
                {
                    'id': deal['id'],
                    'time': deal['time'],
                    'side': deal['side'],
                    'user': deal['user'],
                    'price': format_number_to_pretty(deal['price']),
                    'amount': format_number_to_pretty(deal['amount']),
                    'fee': format_number_to_pretty(deal['fee']),
                    'deal': format_number_to_pretty(deal['deal']),
                    'dealOrderId': deal['deal_order_id'],
                    'role': deal['role'],
                } for deal in response['records']
            ]
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @validate_form(whitelist=['limit', 'lastId', 'offset'])
    def peek(self, market: str, inner_resource: str):
        if inner_resource == 'mydeals':
            return self._peek_me(market)
        elif inner_resource == 'marketdeals':
            try:
                response = stexchange_client.market_deals(
                    market=market,
                    limit=int(context.query_string['limit']),
                    last_id=int(context.query_string['lastId'])
                )
            except StexchangeException as e:
                raise stexchange_http_exception_handler(e)

            return [
                {
                    'id': deal['id'],
                    'time': deal['time'],
                    'price': format_number_to_pretty(deal['price']),
                    'amount': format_number_to_pretty(deal['amount']),
                    'type': deal['type'],
                } for deal in response
            ]

    @json
    @prevent_form
    def list(self):
        try:
            response = stexchange_client.market_list()
            supporting_markets = Market.query.all()
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [
            {
                'name': market['name'],
                'stock': market['stock'],
                'stockPrec': market['stock_prec'],
                'money': market['money'],
                'feePrec': market['fee_prec'],
                'minAmount': format_number_to_pretty(market['min_amount']),
                'moneyPrec': market['money_prec'],
            } for market in response if any(market['name'] == sm.name for sm in supporting_markets)
        ]

    @json
    @prevent_form
    def last(self, market_name: str):

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            return {
                'name': market.name,
                'price': format_number_to_pretty(stexchange_client.market_last(market.name)),
            }
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @prevent_form
    def summary(self, market_name: str):

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            response = stexchange_client.market_summary(market_name)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [
            {
                'name': market['name'],
                'bidAmount': format_number_to_pretty(market['bid_amount']),
                'bidCount': market['bid_count'],
                'askAmount': format_number_to_pretty(market['ask_amount']),
                'askCount': market['ask_count'],
            } for market in response
        ]

    @json
    @validate_form(exact=['period'])
    def status(self, market_name: str):
        period = context.query_string.get('period')

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            if period == 'today':
                status = stexchange_client.market_status_today(market.name)
            else:
                status = stexchange_client.market_status(market.name, int(period))
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return {
            'open': format_number_to_pretty(status['open']),
            'high': format_number_to_pretty(status['high']),
            'low': format_number_to_pretty(status['low']),
            'close': format_number_to_pretty(status.get('close', None)),
            'volume': format_number_to_pretty(status['volume']),
            'deal': format_number_to_pretty(status['deal']),
            'last': format_number_to_pretty(status['last']),
            'period': status.get('period', None),
        }

    @json
    @validate_form(
        requires=['side'],
        whitelist=['side', 'offset', 'limit'],
        pattern={'side': r'^(-)?(buy|sell)$'}
    )
    def book(self, market_name: str):
        offset = context.query_string.get('offset', 0)
        limit = min(context.query_string.get('limit', 10), 10)
        side = 1 if (context.query_string['side'] == 'sell') else 2

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            result = stexchange_client.order_book(market.name, side, offset, limit)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [{
            'ctime': order.get('ctime', None),
            'mtime': order.get('mtime', None),
            'market': order.get('market', None),
            'type': 'limit' if order.get('type', None) == 1 else 'market',
            'side': 'sell' if order.get('side', None) == 1 else 'buy',
            'amount': format_number_to_pretty(order.get('amount', None)),
            'price': format_number_to_pretty(order.get('price', None)),
        } for order in result['orders']]

    @json
    @validate_form(
        whitelist=['interval', 'limit'], types={'interval': int, 'limit': int}
    )
    def depth(self, market_name: str):
        limit = min(context.query_string.get('limit', 10), 10)
        interval = context.query_string.get('interval', 0)

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            depth = stexchange_client.order_depth(market.name, limit, interval)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return {
            'asks': [{'price': format_number_to_pretty(ask[0]), 'amount': format_number_to_pretty(ask[1])} for ask in
                     depth['asks']],
            'bids': [{'price': format_number_to_pretty(bid[0]), 'amount': format_number_to_pretty(bid[1])} for bid in
                     depth['bids']],
        }

    @json
    @validate_form(
        exact=['interval', 'start', 'end'], types={'interval': int, 'start': int, 'end': int}
    )
    def kline(self, market_name: str):
        interval = context.query_string.get('interval')
        start = context.query_string.get('start')
        end = context.query_string.get('end')

        market = Market.query.filter(Market.name == market_name).one_or_none()
        if market is None:
            raise HttpBadRequest('Market not found', 'market-not-found')

        try:
            kline = stexchange_client.market_kline(market.name, start, end, interval)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [{
            'market': market.name,
            'time': k[0],
            'o': format_number_to_pretty(k[1]),
            'h': format_number_to_pretty(k[3]),
            'l': format_number_to_pretty(k[4]),
            'c': format_number_to_pretty(k[2]),
            'volume': format_number_to_pretty(k[5]),
            'amount': format_number_to_pretty(k[6]),
        } for k in kline]
