from nanohttp import context
from restfulpy.orm import DeclarativeBase, Field
from restfulpy.orm.mixins import TimestampMixin, PaginationMixin
from sqlalchemy import Integer, ForeignKey, Unicode, Enum


class IpWhitelist(TimestampMixin, DeclarativeBase):
    __tablename__ = 'ip_whitelist'

    id = Field(Integer(), primary_key=True)
    client_id = Field(Integer(), ForeignKey('member.id'))

    ip = Field(Unicode(50), min_length=7, max_length=15, pattern=r'^([0-9]{1,3}\.){3}[0-9]{1,3}$')


class SecurityLog(TimestampMixin, PaginationMixin, DeclarativeBase):
    __tablename__ = 'security_log'

    id = Field(Integer(), primary_key=True)
    client_id = Field(Integer(), ForeignKey('member.id'))

    type = Field(Enum('login', 'password-change', name='security_log_type'))
    details = Field(Unicode())

    @classmethod
    def generate_log(cls, type):
        session_info = context.application.__authenticator__.extract_agent_info()
        remote_address = session_info['remoteAddress']
        machine = session_info['machine']
        os = session_info['os']
        agent = session_info['agent']
        client = session_info['client']
        app = session_info['app']

        log = cls()
        log.client_id = context.identity.id
        log.type = type
        log.details = f'Remote Address: {remote_address} Machine: {machine} OS: {os} Agent: {agent}' \
                      f' Client: {client} App: {app}'

        return log
