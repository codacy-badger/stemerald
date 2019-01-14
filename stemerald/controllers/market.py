from nanohttp import RestController, json
from restfulpy.validation import prevent_form

from stemerald.stexchange import stexchange_client, StexchangeClient, stexchange_http_exception_handler


class MarketController(RestController):

    @json
    @prevent_form
    def list(self):
        response = stexchange_client.market_list()
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
        except StexchangeClient as e:
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
