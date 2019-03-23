import ujson
from nanohttp import HttpBadRequest, settings, context
from restfulpy.authentication import StatefulAuthenticator
from restfulpy.logging_ import get_logger
from restfulpy.orm import DBSession
from restfulpy.principal import JwtPrincipal
from sqlalchemy_media import store_manager

from stemerald.models import Member

logger = get_logger('auth')


class Authenticator(StatefulAuthenticator):
    """
    BE CAREFUL WHILE EDITING THIS CLASS, IT IS NOT KID GAME !!!
    """

    firebase_token_request_header = 'X-FIREBASE-TOKEN'

    @store_manager(DBSession)
    def create_principal(self, member_id=None, session_id=None):
        member = Member.query.filter(Member.id == member_id).one()
        return member.create_jwt_principal(session_id=session_id)

    def create_refresh_principal(self, member_id=None):
        member = Member.query.filter(Member.id == member_id).one()
        return member.create_refresh_principal()

    def validate_credentials(self, credentials):
        email, password = credentials
        member = Member.query.filter(Member.email == email).one_or_none()

        if member is None or not member.validate_password(password):
            logger.info(f'Login failed (bad-email-or-password): "{email}" "{password}"')
            raise HttpBadRequest('Invalid email or password', 'bad-email-or-password')

        if member.is_active is False:
            logger.info(f'Login failed (account-deactivated): "{email}"')
            raise HttpBadRequest('Your account has been deactivated.', 'account-deactivated')

        return member

    def get_member_sessions_info(self, member_id):
        session_info_list = []
        for session_id in (self.redis.smembers(self.get_member_sessions_key(member_id)) or []):
            session_info_list.append(self.get_session_info(session_id))

        return session_info_list

    def login(self, credentials):
        principal = super().login(credentials)
        # TODO: Please follow this issue to resolve this problem:
        # https://github.com/Carrene/restfulpy/issues/152
        context.cookies[self.refresh_token_key]['path'] = '/'
        return principal

    # TODO: Open an issue on restfulpy for this:
    def get_session_info(self, session_id):
        info = self.redis.get(self.get_session_info_key(session_id.decode()))
        if info:
            result = {'id': session_id}
            result.update(ujson.loads(info))
            return result
        return None

    def extract_agent_info(self):
        result = super().extract_agent_info()

        remote_address = None
        remote_address_key = settings.cdn.remote_address_key
        if remote_address_key in context.environ and context.environ[remote_address_key]:
            remote_address = context.environ[remote_address_key]
        result['remoteAddress'] = remote_address or 'NA'

        result['firebaseToken'] = context.environ[self.firebase_token_request_header] or ''

        return result


class VerificationEmailPrincipal(JwtPrincipal):
    @classmethod
    def get_config(cls):
        config = super().get_config().copy()
        config.update(settings.email_verification)
        return config


class ResetPasswordPrincipal(JwtPrincipal):
    @classmethod
    def get_config(cls):
        config = super().get_config().copy()
        config.update(settings.reset_password)
        return config
