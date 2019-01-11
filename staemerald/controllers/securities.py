from nanohttp import json, context
from nanohttp.controllers import RestController
from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.validation import prevent_form, validate_form

from staemerald.models import SecurityLog, IpWhitelist


class LogController(ModelRestController):
    __model__ = SecurityLog

    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = SecurityLog.query
        if context.identity.is_in_roles('client'):
            query = query.filter(SecurityLog.client_id == context.identity.id)

        return query


class IpWhitelistController(ModelRestController):
    __model__ = IpWhitelist

    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = SecurityLog.query
        if context.iedntity.is_in_roles('client'):
            query = query.filter(SecurityLog.client_id == context.identity.id)

        return query


class SecurityController(RestController):
    logs = LogController()
    ipwhitelists = LogController()
