from nanohttp import RestController, context, json, HttpBadRequest
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form, prevent_form

from stemerald.models import Currency
from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class AssetsController(RestController):

    @json
    def list(self):
        supporting_assets = Currency.query.all()
        try:
            return [{
                'name': x['name'],
                'currency': list(filter(lambda y: y.symbol == x['name'], supporting_assets))[0].to_dict(),
                'prec': x['prec'],
            } for x in stexchange_client.asset_list() if any(x['name'] == sm.symbol for sm in supporting_assets)]

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @authorize("admin")
    def overview(self):

        try:
            response = []
            asset_summaries = stexchange_client.asset_summary()

            for asset in asset_summaries:
                currency = Currency.query.filter(Currency.symbol == asset['name']).one_or_none()
                if currency is None:
                    continue

                response.append(
                    {
                        'name': asset['name'],
                        'currency': currency.to_dict(),
                        'totalBalance': currency.normalized_to_output(asset['total_balance']),
                        'availableCount': currency.normalized_to_output(asset['available_count']),
                        'availableBalance': currency.normalized_to_output(asset['available_balance']),
                        'freezeCount': currency.normalized_to_output(asset['available_count']),
                        'freezeBalance': currency.normalized_to_output(asset['available_count']),
                    }
                )

            return response

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)


class BalancesController(RestController):
    PAGE_SIZE = 20

    @json
    @authorize("client")
    @prevent_form
    def overview(self):
        supporting_assets = Currency.query.all()
        asset_names = [x['name'] for x in stexchange_client.asset_list()]
        result = []
        try:
            for key, value in stexchange_client.balance_query(context.identity.id, *asset_names).items():
                if any(key == sm.symbol for sm in supporting_assets):
                    currency = list(filter(lambda x: x.symbol == key, supporting_assets))[0]
                    result.append({
                        'name': key,
                        'currency': currency.to_dict(),
                        'available': currency.normalized_to_output(value['available']),
                        'freeze': currency.normalized_to_output(value['freeze']),
                    })

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return result

    @json
    @authorize("client")
    @validate_form(
        exact=['asset', 'page'], types={'page': int}
    )
    def history(self):
        currency = Currency.query.filter(Currency.symbol == context.query_string.get('asset', None)).one_or_none()
        if currency is None:
            raise HttpBadRequest('Currency not found', 'market-not-found')
        try:
            return [
                {
                    'time': x['timestamp'],
                    'asset': x['asset'],
                    'currency': currency.to_dict(),
                    'business': x['business'],
                    'change': currency.normalized_to_output(x['change']),
                    'balance': currency.normalized_to_output(x['balance']),
                    'detail': x['detail'],
                } for x in stexchange_client.balance_history(
                    context.identity.id,
                    asset=context.query_string.get('asset', None),
                    limit=context.query_string.get('take', self.PAGE_SIZE),
                    business='deposit,withdraw,cashin,cashout,cashback',
                    offset=context.query_string.get('skip', self.PAGE_SIZE * context.query_string.get('page', 0))
                )['records']
            ]

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)
