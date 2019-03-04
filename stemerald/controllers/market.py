from nanohttp import RestController, json, context, HttpBadRequest, HttpNotFound
from restfulpy.authorization import authorize
from restfulpy.validation import prevent_form, validate_form

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
                    'price': deal['price'],
                    'amount': deal['amount'],
                    'fee': deal['fee'],
                    'deal': deal['deal'],
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
                'minAmount': market['min_amount'],
                'moneyPrec': market['money_prec'],
            } for market in response if any(market['name'].lower() == sm.name for sm in supporting_markets)
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
                'price': stexchange_client.market_last(market.name),
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
                'bidAmount': market['bid_amount'],
                'bidCount': market['bid_count'],
                'askAmount': market['ask_amount'],
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
            'open': status['open'],
            'high': status['high'],
            'low': status['low'],
            'close': status.get('close', None),
            'volume': status['volume'],
            'deal': status['deal'],
            'last': status['last'],
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
            'amount': order.get('amount', None),
            'price': order.get('price', None),
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
            'asks': [{'price': ask[0], 'amount': ask[1]} for ask in depth['asks']],
            'bids': [{'price': bid[0], 'amount': bid[1]} for bid in depth['bids']],
        }
