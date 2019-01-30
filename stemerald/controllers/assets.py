from nanohttp import RestController, context, json
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form, prevent_form

from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class AssetsController(RestController):

    @json
    def list(self):
        try:
            return [{
                'name': x['name'],
                'prec': x['prec'],
            } for x in stexchange_client.asset_list()]

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

    @json
    @authorize("client")
    @prevent_form
    def overview(self):
        asset_names = [x['name'] for x in stexchange_client.asset_list()]
        result = []
        try:
            for key, value in stexchange_client.balance_query(context.identity.id, *asset_names).items():
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
        whitelist=['take', 'skip'],
    )
    def list(self):
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
                    limit=context.query_string.get('take', 0),
                    offset=context.query_string.get('skip', 0)
                )['records']
            ]

        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)
