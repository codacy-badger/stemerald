from nanohttp import RestController
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form


class AssetController(RestController):

    @authorize("client")
    @validate_form(
        whitelist=['id', 'currencyCode'],
        client={'blacklist': ['clientId']},
        pattern={'sort': r'^(-)?(id|currencyCode)$'}
    )
    def get(self):
        pass
