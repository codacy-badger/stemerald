from datetime import datetime

from nanohttp import RestController, json, context, HttpBadRequest
from restfulpy.authorization import authorize
from restfulpy.utils import format_iso_datetime
from restfulpy.validation import prevent_form, validate_form

from stemerald.models import Market
from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class MarketController(RestController):

    def __fetch_market(self, market_name=None) -> Market:
        market_name = (market_name or context.query_string.get("marketName", None)) \
                      or context.form.get("marketName", None)
        market = Market.query \
            .filter(Market.name == market_name) \
            .one_or_none()

        if market is None:
            raise HttpBadRequest('Bad market', 'bad-market')

        return market

    @authorize('client')
    def _peek_me(self, market: Market):
        try:
            response = stexchange_client.market_user_deals(
                user_id=context.identity.id,
                market=market.name,
                offset=int(context.query_string['offset']),
                limit=int(context.query_string['limit'])
            )
            return [
                {
                    'id': deal['id'],
                    'time': format_iso_datetime(
                        datetime.utcfromtimestamp(int(deal['time']))) if 'time' in deal else None,
                    'side': deal['side'],
                    'user': deal['user'],
                    'price': market.quote_currency.normalized_to_output(deal['price']),
                    'amount': market.base_currency.normalized_to_output(deal['amount']),
                    'fee': market.quote_currency.normalized_to_output(deal['fee']),  # FIXME: Is it (quote_currency)
                    'deal': market.quote_currency.normalized_to_output(deal['deal']),  # FIXME: Is it (quote_currency)
                    'dealOrderId': deal['deal_order_id'],
                    'role': deal['role'],
                } for deal in response['records']
            ]
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @validate_form(whitelist=['limit', 'lastId', 'offset'])
    def peek(self, market: str, inner_resource: str):

        market = self.__fetch_market(market)

        if inner_resource == 'mydeals':
            return self._peek_me(market)
        elif inner_resource == 'marketdeals':
            try:
                response = stexchange_client.market_deals(
                    market=market.name,
                    limit=int(context.query_string['limit']),
                    last_id=int(context.query_string['lastId'])
                )
            except StexchangeException as e:
                raise stexchange_http_exception_handler(e)

            return [
                {
                    'id': deal['id'],
                    'time': format_iso_datetime(
                        datetime.utcfromtimestamp(int(deal['time']))) if 'time' in deal else None,
                    'price': market.quote_currency.normalized_to_output(deal['price']),
                    'amount': market.base_currency.normalized_to_output(deal['amount']),
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
                'minAmount': list(filter(lambda y: y.name == market['name'], supporting_markets))[0]
                    .base_currency.normalized_to_output(market['min_amount']),
                'moneyPrec': market['money_prec'],
            } for market in response if any(market['name'] == sm.name for sm in supporting_markets)
        ]

    @json
    @prevent_form
    def last(self, market_name: str):

        market = self.__fetch_market(market_name)

        try:
            return {
                'name': market.name,
                'price': market.quote_currency.normalized_to_output(stexchange_client.market_last(market.name)),
            }
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @prevent_form
    def summary(self, market_name: str):

        market = self.__fetch_market(market_name)

        try:
            response = stexchange_client.market_summary(market_name)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [
            {
                'name': market_summary['name'],
                'bidAmount': market.base_currency.normalized_to_output(market_summary['bid_amount']),
                'bidCount': market_summary['bid_count'],
                'askAmount': market.base_currency.normalized_to_output(market_summary['ask_amount']),
                'askCount': market_summary['ask_count'],
            } for market_summary in response
        ]

    @json
    @validate_form(exact=['period'])
    def status(self, market_name: str):
        period = context.query_string.get('period')

        market = self.__fetch_market(market_name)

        try:
            if period == 'today':
                status = stexchange_client.market_status_today(market.name)
            else:
                status = stexchange_client.market_status(market.name, int(period))
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return {
            'open': market.quote_currency.normalized_to_output(status['open']),
            'high': market.quote_currency.normalized_to_output(status['high']),
            'low': market.quote_currency.normalized_to_output(status['low']),
            'close': market.quote_currency.normalized_to_output(status.get('close', None)),
            'volume': market.base_currency.normalized_to_output(status['volume']),
            # FIXME: Is it (base_currency) right?
            'deal': market.quote_currency.normalized_to_output(status['deal']),  # FIXME: Is it (quote_currency) right?
            'last': market.quote_currency.normalized_to_output(status['last']),
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

        market = self.__fetch_market(market_name)

        try:
            result = stexchange_client.order_book(market.name, side, offset, limit)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [{
            'createdAt': format_iso_datetime(
                datetime.utcfromtimestamp(int(order['ctime']))) if 'ctime' in order else None,
            'modifiedAt': format_iso_datetime(
                datetime.utcfromtimestamp(int(order['mtime']))) if 'mtime' in order else None,
            'market': order.get('market', None),
            'type': 'limit' if order.get('type', None) == 1 else 'market',
            'side': 'sell' if order.get('side', None) == 1 else 'buy',
            'amount': market.base_currency.normalized_to_output(order.get('amount', None)),
            'price': market.quote_currency.normalized_to_output(order.get('price', None)),
        } for order in result['orders']]

    @json
    @validate_form(
        whitelist=['interval', 'limit'], types={'interval': int, 'limit': int}
    )
    def depth(self, market_name: str):
        limit = min(context.query_string.get('limit', 10), 10)
        interval = context.query_string.get('interval', 0)

        market = self.__fetch_market(market_name)

        try:
            depth = stexchange_client.order_depth(market.name, limit, interval)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return {
            'asks': [{'price': market.quote_currency.normalized_to_output(ask[0]),
                      'amount': market.base_currency.normalized_to_output(ask[1])} for ask in
                     depth['asks']],
            'bids': [{'price': market.quote_currency.normalized_to_output(bid[0]),
                      'amount': market.base_currency.normalized_to_output(bid[1])} for bid in
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

        market = self.__fetch_market(market_name)

        try:
            kline = stexchange_client.market_kline(market.name, start, end, interval)
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return [{
            'market': market.name,
            'time': k[0],
            'o': market.quote_currency.normalized_to_output(k[1]),
            'h': market.quote_currency.normalized_to_output(k[3]),
            'l': market.quote_currency.normalized_to_output(k[4]),
            'c': market.quote_currency.normalized_to_output(k[2]),
            'volume': market.base_currency.normalized_to_output(k[5]),  # FIXME: Is it (base_currency) right?
            'amount': market.base_currency.normalized_to_output(k[6]),  # FIXME: Is it (base_currency) right?
        } for k in kline]
