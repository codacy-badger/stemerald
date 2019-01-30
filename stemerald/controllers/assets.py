from nanohttp import RestController, context
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form, prevent_form

from stemerald import stexchange_client


class AssetsController(RestController):
    @authorize("client")
    def list(self):
        return stexchange_client.asset_list()


class BalancesController(RestController):

    @authorize("client")
    @prevent_form
    def summary(self):
        assets = stexchange_client.asset_list()
        result = []
        for key, value in stexchange_client.balance_query(context.identity.id, *assets):
            result.append({
                'name': key,
                'available': value['available'],
                'freeze': value['freeze'],
            })
        return result

    @authorize("client")
    @validate_form(
        whitelist=['take', 'skip'],
    )
    def list(self):
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
