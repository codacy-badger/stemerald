import base64
import io
from typing import Union

import itsdangerous
import qrcode
from nanohttp import json, context, RestController, action, text
from nanohttp.configuration import settings
from nanohttp.exceptions import HttpForbidden, HttpNotFound, HttpConflict, HttpBadRequest

from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.logging_ import get_logger
from restfulpy.orm import commit, DBSession
from restfulpy.validation import validate_form, prevent_form
from sqlalchemy_media import store_manager
from sqlalchemy_media.exceptions import DimensionValidationError, AspectRatioValidationError, AnalyzeError, \
    ContentTypeValidationError

from stemerald.authentication import VerificationEmailPrincipal, ResetPasswordPrincipal
from stemerald.models import Client, Admin, Member, ClientEvidence, VerificationEmail, VerificationSms, \
    ResetPasswordEmail, SecurityLog, Fund, Invitation
from stemerald.oath import Oath

logger = get_logger('CLIENT')

MemberId = Union[int, str]

phone_pattern = r'\+[1-9]{1}[0-9]{3,14}'  # TODO: Close begin and end
email_pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'


# TODO: IMPORTANT: Invalidate member sessions in all services!

class FundController(ModelRestController):
    __model__ = Fund

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'sort', 'id', 'currencyCode'],
        client={'blacklist': ['clientId']},
        pattern={'sort': r'^(-)?(id|currencyCode)$'}
    )
    @__model__.expose
    def get(self):
        query = Fund.query

        if context.identity.is_in_roles('client'):
            query = query.filter(Fund.client_id == context.identity.id)

        return query


class SessionController(RestController):
    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['take', 'skip'],
        types={'take': int, 'skip': int}
    )
    def get(self):
        return Member.current().sessions

    @json
    @authorize('admin', 'client')
    @prevent_form
    def terminate(self, session_id: str):

        if not context.application.__authenticator__.validate_session(session_id):
            raise HttpNotFound()

        if not context.identity.is_in_roles('admin'):
            member_id = context.application.__authenticator__.get_session_member(session_id)
            if member_id != context.identity.id:
                raise HttpNotFound()

        context.application.__authenticator__.unregister_session(session_id)

        return dict(sessionId=session_id)

    # This is standard login of restfulpy-client:
    @json
    @validate_form(whitelist=['email', 'password', 'otp'], requires=['email', 'password'])
    @commit
    def post(self):
        email = context.form.get('email')
        password = context.form.get('password')
        otp = context.form.get('otp', None)

        principal = context.application.__authenticator__.login((email, password))
        token = principal.dump().decode()

        try:
            # TODO: Add this feature for admins
            if principal.is_in_roles('client'):
                client = Client.query.filter(Client.email == email).one()
                if client.has_second_factor is True:
                    if otp is None:
                        raise HttpBadRequest('Otp needed', 'bad-otp')

                    oath = Oath(seed=settings.membership.second_factor_seed, derivate_seed_from=client.email)
                    is_valid, _ = oath.verify_google_auth(otp)
                    if is_valid is False:
                        raise HttpBadRequest('Invalid otp', 'invalid-otp')

            login_log = SecurityLog.generate_log(type='login')
            DBSession.add(login_log)
            DBSession.flush()
        except Exception as e:
            # FIXME: Fix the warning
            context.application.__authenticator__.unregister_session(principal.session_id)
            raise e

        return dict(token=token)


# TODO: Make it REST! (Get client_id before this controller)
class EvidenceController(ModelRestController):
    __model__ = ClientEvidence

    @store_manager(DBSession)
    @json
    @authorize('admin')
    @validate_form(
        whitelist=['clientId', 'take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        return ClientEvidence.query

    @store_manager(DBSession)
    @json
    @authorize('semitrusted_client')
    @validate_form(
        exact=[
            'firstName', 'lastName', 'gender', 'birthday', 'cityId', 'nationalCode', 'address', 'idCard',
            'idCardSecondary'
        ]
    )
    @__model__.expose
    @commit
    def submit(self):
        evidence = Client.current().evidence

        if evidence.mobile_phone is None or evidence.fixed_phone is None:
            raise HttpForbidden('Please verify your mobile and fixed phone first.')

        evidence.update_from_request()

        id_card = context.form.get('idCard')
        id_card_secondary = context.form.get('idCardSecondary')

        try:
            evidence.id_card = id_card
            evidence.id_card_secondary = id_card_secondary

        except AspectRatioValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-aspectratio')

        except DimensionValidationError as ex:
            raise HttpBadRequest(str(ex), reason='invalid-dimensions')

        except (AnalyzeError, ContentTypeValidationError) as ex:
            raise HttpBadRequest(str(ex), reason='invalid-type')

        return evidence

    @store_manager(DBSession)
    @json
    @authorize('admin')
    @validate_form(exact=['clientId'])
    @__model__.expose
    @commit
    def accept(self):
        client_id = context.form.get('clientId')

        client = Client.query.filter(Client.id == client_id).one_or_none()

        if client is None:
            raise HttpNotFound()

        # TODO: Check all fields are not `None`

        if client.is_email_verified is False or client.is_evidence_verified is True:
            raise HttpConflict()

        client.evidence.error = None
        client.is_evidence_verified = True

        return client

    @store_manager(DBSession)
    @json
    @authorize('admin')
    @validate_form(exact=['clientId', 'error'])
    @__model__.expose
    @commit
    def reject(self):
        client_id = context.form.get('clientId')
        error = context.form.get('error')

        client = Client.query.filter(Client.id == client_id).one_or_none()

        if client is None:
            raise HttpNotFound()

        if client.is_email_verified is False or client.is_evidence_verified is True:
            raise HttpConflict()

        client.evidence.error = error

        return client


class ClientPasswordController(RestController):
    @json
    @authorize('client')
    @validate_form(exact=['currentPassword', 'newPassword'])
    @commit
    def change(self):
        current_password = context.form.get('currentPassword')
        new_password = context.form.get('newPassword')

        client = Client.current()
        client.change_password(current_password=current_password, new_password=new_password)

        context.application.__authenticator__.invalidate_member(context.identity.id)

        return client

    @json
    @validate_form(exact=['email'])
    @commit
    def schedule(self):
        email = context.form.get('email')

        client = Client.query.filter(Client.email == email).one_or_none()
        if client is not None:
            principal = ResetPasswordPrincipal({'email': client.email})
            # noinspection PyArgumentList
            task = ResetPasswordEmail(
                to=client.email,
                subject='Reset password',
                body={'token': principal.dump().decode()},
            )
            DBSession.add(task)

        return dict(success=True)

    @json
    @validate_form(exact=['token', 'password'])
    @commit
    def reset(self):
        token = context.form.get('token')
        password = context.form.get('password')

        try:
            principal = ResetPasswordPrincipal.load(token)
        except itsdangerous.SignatureExpired:
            raise HttpBadRequest()

        except itsdangerous.BadData:
            raise HttpBadRequest()

        client = Client.query.filter(Client.email == principal.email).one_or_none()
        if client is None:
            raise HttpBadRequest()

        client.password = password
        context.application.__authenticator__.invalidate_member(client.id)

        return dict(success=True)


class InvitationController(ModelRestController):
    __model__ = Invitation

    @json
    @authorize('admin')
    @prevent_form
    @__model__.expose
    def get(self, code: str = None):
        if code is None:
            return Invitation.query

        return Invitation.ensure_code(code)

    @json
    @authorize('admin')
    @validate_form(exact=['code', 'totalSits'], types={'totalSits': int})
    @__model__.expose
    @commit
    def create(self):
        invitation = Invitation()
        invitation.update_from_request()
        invitation.is_active = True
        DBSession.add(invitation)
        return invitation

    @json
    @authorize('admin')
    @validate_form(whitelist=['code', 'totalSits'], types={'totalSits': int})
    @commit
    def edit(self, code: str):
        invitation = Invitation.ensure_code(code)
        invitation.update_from_request()
        if invitation.total_sits < invitation.filled_sits:
            raise HttpBadRequest('Total sits should not be grater than filled sits.', 'filled-sits-grater-than-total')
        return invitation

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def activate(self, code: str):
        invitation = Invitation.ensure_code(code)
        invitation.is_active = True
        return invitation

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def deactivate(self, code: str):
        invitation = Invitation.ensure_code(code)
        invitation.is_active = False
        return invitation


class SecondfactorController(RestController):
    @action
    @authorize('client')
    @prevent_form
    @commit
    def enable(self):
        Client.current().has_second_factor = True
        return {'message': 'done'}

    @json
    @authorize('client')
    @prevent_form
    @commit
    def disable(self):
        Client.current().has_second_factor = False
        return {'message': 'done'}

    @text(content_type='images/png')
    @authorize('client')
    @prevent_form
    @commit
    def provision(self):
        client = Client.current()
        if client.has_second_factor is False:
            raise HttpBadRequest('Client haven\'t enabled 2-factor authentication')
        # TODO: Use another salt too (password or ...)
        oath = Oath(seed=settings.membership.second_factor_seed, derivate_seed_from=client.email)

        with io.BytesIO() as virtual_file:
            qrcode.make(oath.get_google_auth_uri(client.email)).save(stream=virtual_file)
            return base64.b64encode(virtual_file.getvalue()).decode()


class ClientController(ModelRestController):
    __model__ = Client

    passwords = ClientPasswordController()
    evidences = EvidenceController()
    funds = FundController()
    invitations = InvitationController()
    secondfactors = SecondfactorController()

    @store_manager(DBSession)
    @json
    @authorize('admin', 'client')
    @validate_form(
        whitelist=['id', 'take', 'skip'],
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self, client_id: MemberId = None, inner_resource: str = None):
        if context.identity.is_in_roles('client'):
            if client_id == 'me':
                client = Client.current()

                if inner_resource == 'evidences':
                    return client.evidence

                return client

        elif context.identity.is_in_roles('admin'):

            query = Client.query
            if client_id is not None:
                client = query.filter(Client.id == client_id).one_or_none()

                if client is None:
                    raise HttpNotFound()

                if inner_resource == 'evidences':
                    return client.evidence

                return client

            return query

        raise HttpNotFound()

    @json
    @validate_form(whitelist=['email', 'password', 'invitationCode'], required=['email', 'password'])
    @__model__.expose
    @commit
    def register(self):
        email = context.form.get('email')
        password = context.form.get('password')
        invitation_code = context.form.get('invitationCode', None)

        client = Client()

        if invitation_code is None and settings.membership.invitation_code_required is True:
            raise HttpBadRequest('Bad invitation code', 'bad-invitation-code')

        if invitation_code is not None:
            invitation = Invitation.query.filter(Invitation.code == invitation_code).with_for_update().one_or_none()
            if invitation is None or invitation.is_active is False:
                raise HttpBadRequest('Bad invitation code', 'bad-invitation-code')

            if invitation.unfilled_sits <= 0:
                raise HttpBadRequest('Fully filled invitation code', 'fully-filled-invitation-code')

            invitation.filled_sits += 1
            client.invitation_code = invitation_code

        client.email = email
        client.password = password
        client.is_active = True
        DBSession.add(client)

        return client

    @action
    @authorize('client')
    @validate_form(white_list=['phone'], pattern={'phone': phone_pattern})
    @commit
    def schedule(self, inner_resource: str = None):
        if inner_resource == 'email-verifications':
            return self.__schedule_email_verification()

        elif inner_resource == 'mobile-phone-verifications':
            return self.__schedule_mobile_phone_verification()

        elif inner_resource == 'fixed-phone-verifications':
            return self.__schedule_fixed_phone_verification()

        raise HttpNotFound()

    @authorize('distrusted_client')
    @prevent_form
    def __schedule_email_verification(self):
        client = Client.current()

        if client.is_email_verified is True or client.is_evidence_verified is True:
            raise HttpConflict('Already verified.', 'already-verified')

        principal = VerificationEmailPrincipal({'id': client.id})
        # noinspection PyArgumentList
        task = VerificationEmail(
            to=client.email,
            subject='Email verification',
            body={'token': principal.dump().decode()},
        )

        DBSession.add(task)
        return

    @authorize('semitrusted_client')
    @validate_form(exact=['phone'])
    def __schedule_mobile_phone_verification(self):
        client = Client.current()

        if client.evidence.mobile_phone is not None:
            raise HttpConflict('Already verified.', 'already-verified')

        phone = context.form.get('phone')

        # TODO: The following error can cause security issues!
        if ClientEvidence.query.filter(ClientEvidence.mobile_phone == phone).count() > 0:
            raise HttpConflict('Already used.', 'already-used')

        oath = Oath(seed=settings.mobile_phone_verification.seed, derivate_seed_from=client.email)
        code = oath.generate(challenge=phone[1:])

        sms = VerificationSms()
        sms.to = phone
        sms.body = {'code': code, 'template': settings.mobile_phone_verification.template}

        DBSession.add(sms)

    @authorize('semitrusted_client')
    @validate_form(exact=['phone'])
    def __schedule_fixed_phone_verification(self):
        client = Client.current()

        if client.evidence.fixed_phone is not None:
            raise HttpConflict('Already verified.', 'already-verified')

        phone = context.form.get('phone')

        # TODO: The following error can cause security issues!
        if ClientEvidence.query.filter(ClientEvidence.fixed_phone == phone).count() > 0:
            raise HttpConflict('Already used.', 'already-used')

        oath = Oath(seed=settings.fixed_phone_verification.seed, derivate_seed_from=client.email)
        code = oath.generate(challenge=phone[1:])

        sms = VerificationSms()
        sms.to = phone
        sms.body = {'code': code, 'template': settings.fixed_phone_verification.template}

        DBSession.add(sms)

    @json
    @authorize('client')
    @validate_form(whitelist=['token', 'phone', 'code'], pattern={'phone': phone_pattern, 'code': r'^[0-9]{6}$'})
    @commit
    def verify(self, inner_resource: str = None):
        if inner_resource == 'email-verifications':
            return self.__verify_email_verification()

        elif inner_resource == 'mobile-phone-verifications':
            return self.__verify_mobile_phone_verification()

        elif inner_resource == 'fixed-phone-verifications':
            return self.__verify_fixed_phone_verification()

        raise HttpNotFound()

    @authorize('distrusted_client')
    @validate_form(exact=['token'])
    def __verify_email_verification(self):
        token = context.form.get('token')
        try:
            principal = VerificationEmailPrincipal.load(token)
        except itsdangerous.SignatureExpired:
            raise HttpBadRequest()

        except itsdangerous.BadData:
            raise HttpBadRequest()

        if principal.id != context.identity.id:
            raise HttpBadRequest()

        client = Client.current()
        client.is_email_verified = True
        context.application.__authenticator__.invalidate_member(client.id)

        return client

    @authorize('semitrusted_client')
    @validate_form(exact=['phone', 'code'])
    def __verify_mobile_phone_verification(self):
        client = Client.current()

        if client.evidence.mobile_phone is not None:
            raise HttpConflict('Already verified.', 'already-verified')

        phone = context.form.get('phone')
        code = context.form.get('code')

        oath = Oath(seed=settings.mobile_phone_verification.seed, derivate_seed_from=client.email)
        if oath.verify(challenge=phone[1:], code=code)[0] is True:
            client.evidence.mobile_phone = phone
            context.application.__authenticator__.invalidate_member(client.id)
            return client

        raise HttpBadRequest()

    @authorize('semitrusted_client')
    @validate_form(exact=['phone', 'code'])
    def __verify_fixed_phone_verification(self):
        client = Client.current()

        if client.evidence.fixed_phone is not None:
            raise HttpConflict('Already verified.', 'already-verified')

        phone = context.form.get('phone')
        code = context.form.get('code')

        oath = Oath(seed=settings.fixed_phone_verification.seed, derivate_seed_from=client.email)
        if oath.verify(challenge=phone[1:], code=code)[0] is True:
            client.evidence.fixed_phone = phone
            context.application.__authenticator__.invalidate_member(client.id)
            return client

        raise HttpBadRequest()

    @json
    @authorize('admin')
    @prevent_form
    @__model__.expose
    @commit
    def activate(self, client_id: MemberId = None):
        client = Client.query.filter(Client.id == client_id).one_or_none()
        if client is None:
            raise HttpNotFound()

        if client.is_active is True:
            raise HttpConflict()

        client.is_active = True

        return client

    @json
    @authorize('admin')
    @prevent_form
    @__model__.expose
    @commit
    def deactivate(self, client_id: MemberId = None):
        client = Client.query.filter(Client.id == client_id).one_or_none()
        if client is None:
            raise HttpNotFound()

        if client.is_active is False:
            raise HttpConflict()

        client.is_active = False

        context.application.__authenticator__.invalidate_member(client_id)

        return client

    @json
    @authorize('admin', 'client')
    @validate_form(whitelist=['name'])
    @__model__.expose
    @commit
    def edit(self):
        pass


class AdminController(ModelRestController):
    __model__ = Admin

    @json
    @authorize('admin')
    @prevent_form
    @__model__.expose
    def get(self):
        pass

    @json
    def metadata(self):
        raise HttpForbidden()
