from nanohttp import json, context, HttpNotFound
from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.validation import validate_form, prevent_form

from stemerald.models import Notification


class NotificationController(ModelRestController):
    __model__ = Notification

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'type', 'take', 'skip', 'fiatSymbol'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'amount', 'commission']},
        types={'take': int, 'skip': int}
    )
    @Notification.expose
    def get(self):
        query = Notification.query

        if context.identity.is_in_roles('client'):
            query = query.filter(Notification.member_id == context.identity.id)

        return query

    @json
    @authorize('admin', 'client')
    @prevent_form
    @Notification.expose
    def read(self, notification_id: int = None):
        query = Notification.query.filter(Notification.id == notification_id)

        if context.identity.is_in_roles('client'):
            query = query.filter(Notification.member_id == context.identity.id)

        notification = query.one_or_none()
        if notification is None:
            raise HttpNotFound('Notification not found', 'notification-not-found')

        if notification.is_read is False:
            notification.is_read = True

        return notification
