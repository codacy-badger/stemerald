from nanohttp import json, context, HttpBadRequest, HttpNotFound, HttpConflict, HttpMethodNotAllowed
from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.orm import DBSession, commit
from restfulpy.validation import prevent_form, validate_form
from sqlalchemy_media import store_manager
from sqlalchemy_media.exceptions import AspectRatioValidationError, DimensionValidationError, \
    ContentTypeValidationError, AnalyzeError

from staemerald.models import TicketMessage, Ticket, TicketDepartment


class TickedDepartmentController(ModelRestController):
    __model__ = TicketDepartment

    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @TicketDepartment.expose
    def get(self):
        return TicketDepartment.query


# Just for Metadata
# TODO: Become REST! User this controller to handle message append and get (using TicketController's __call__ method).
class TicketMessageController(ModelRestController):
    __model__ = TicketMessage


class TicketController(ModelRestController):
    __model__ = Ticket

    departments = TickedDepartmentController()
    messages = TicketMessageController()

    @TicketMessage.expose
    def __get_ticket_messages(self, ticket_id):
        return TicketMessage.query.filter(TicketMessage.ticket_id == ticket_id)

    @store_manager(DBSession)
    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self, ticket_id: int = None, inner_resource: str = None):
        query = Ticket.query

        if context.identity.is_in_roles('client'):
            query = query.filter(Ticket.member_id == context.identity.id)

        if ticket_id is not None:
            ticket = query.filter(Ticket.id == ticket_id).one_or_none()

            if ticket is None:
                raise HttpNotFound('Ticket not found')

            if inner_resource == 'messages':
                return self.__get_ticket_messages(ticket_id)

            elif inner_resource is None:
                return ticket

        else:
            return query

        raise HttpMethodNotAllowed()

    @store_manager(DBSession)
    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['title', 'departmentId', 'message', 'attachment', 'clientId'],
        requires=['title', 'departmentId', 'message'],
        types={'departmentId': int, 'clientId': int},
        admin={'whitelist': ['clientId'], 'requires': ['clientId']}
    )
    @commit
    def create(self):
        title = context.form.get('title')
        department_id = context.form.get('departmentId')
        message = context.form.get('message')
        attachment = context.form.get('attachment', None)
        client_id = context.form.get('clientId', None)

        if TicketDepartment.query.filter(TicketDepartment.id == department_id).count() == 0:
            raise HttpBadRequest('Bad department_id')

        ticket = Ticket()
        ticket.member_id = context.identity.id if context.identity.is_in_roles('client') else client_id
        ticket.department_id = department_id
        ticket.title = title

        ticket_message = TicketMessage()
        ticket_message.ticket = ticket
        ticket_message.member_id = context.identity.id
        ticket_message.text = message

        try:
            ticket_message.attachment = attachment

        except AspectRatioValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-aspectratio')

        except DimensionValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-dimensions')

        except (AnalyzeError, ContentTypeValidationError) as ex:
            raise HttpBadRequest(str(ex), reason='invalid-type')

        DBSession.add(ticket)
        DBSession.add(ticket_message)

        # FIXME: These are not good:
        DBSession.flush()
        result = ticket.to_dict()
        result['firstMessage'] = ticket_message.to_dict()

        return result

    @store_manager(DBSession)
    @json
    @authorize('admin', 'client')
    @validate_form(whitelist=['message', 'attachment'], requires=['message'])
    @__model__.expose
    @commit
    def append(self, ticket_id: int):
        message = context.form.get('message')
        attachment = context.form.get('attachment', None)

        ticket = Ticket.query.filter(Ticket.id == ticket_id)
        if context.identity.is_in_roles('client'):
            ticket = ticket.filter(Ticket.member_id == context.identity.id)
        ticket = ticket.one_or_none()

        if ticket is None:
            raise HttpNotFound('Ticket not found')

        ticket_message = TicketMessage()
        ticket_message.ticket_id = ticket.id
        ticket_message.member_id = context.identity.id
        ticket_message.text = message
        ticket_message.is_answer = True if ticket.member_id != context.identity.id else False

        try:
            ticket_message.attachment = attachment

        except AspectRatioValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-aspectratio')

        except DimensionValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-dimensions')

        except (AnalyzeError, ContentTypeValidationError) as ex:
            raise HttpBadRequest(str(ex), reason='invalid-type')

        DBSession.add(ticket_message)

        if ticket.is_closed is True:
            ticket.is_closed = False

        return ticket_message

    @store_manager(DBSession)
    @json
    @authorize('admin', 'client')
    @prevent_form
    @__model__.expose
    @commit
    def close(self, ticket_id: int):
        ticket = Ticket.query.filter(Ticket.id == ticket_id)
        if context.identity.is_in_roles('client'):
            ticket = ticket.filter(Ticket.member_id == context.identity.id)
        ticket = ticket.one_or_none()

        if ticket is None:
            raise HttpNotFound('Ticket not found')

        if ticket.is_closed is False:
            ticket.is_closed = True
        else:
            raise HttpConflict('Ticket already closed')

        return ticket
