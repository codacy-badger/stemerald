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
                'prec': x['prec'],
            } for x in stexchange_client.asset_list() if any(x['name'] == sm.symbol for sm in supporting_assets)]

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    @json
    @authorize("admin")
    def overview(self):
        try:
            return [{
                'name': x['name'],
                'totalBalance': x['total_balance'],
                'availableCount': x['available_count'],
                'availableBalance': x['available_balance'],
                'freezeCount': x['available_count'],
                'freezeBalance': x['available_count'],
            } for x in stexchange_client.asset_summary()]

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
                    result.append({
                        'name': key,
                        'available': value['available'],
                        'freeze': value['freeze'],
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
        asset = Currency.query.filter(Currency.symbol == context.query_string.get('asset', None)).one_or_none()
        if asset is None:
            raise HttpBadRequest('Asset not found', 'market-not-found')
        try:
            return [
                {
                    'time': x['timestamp'],
                    'asset': x['asset'],
                    'business': x['business'],
                    'change': x['change'],
                    'balance': x['balance'],
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
