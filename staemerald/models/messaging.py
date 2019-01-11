from nanohttp import settings
from restfulpy.logging_ import get_logger
from restfulpy.messaging import Email
from restfulpy.orm import Field
from restfulpy.taskqueue import Task
from sqlalchemy import Integer, ForeignKey, Unicode, JSON

from staemerald.sms import create_sms_provider

logger = get_logger('MESSAGING')


class Sms(Task):
    """
    This is the base SMS task
    """
    __tablename__ = 'sms'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__
    }

    id = Field(Integer, ForeignKey('task.id'), primary_key=True, json='id')
    to = Field(Unicode(25), pattern=r'\+[1-9]{1}[0-9]{3,14}')
    body = Field(JSON, json='body')

    @property
    def message_format(self):
        raise NotImplementedError()

    @property
    def sms_text(self):
        return self.message_format % self.body

    def do_(self, context):  # pragma: no cove
        create_sms_provider().send(self.to, self.sms_text)
        logger.info('%s has been sent to %s', self.sms_text, self.to)


# noinspection PyAbstractClass
class VerificationSms(Sms):
    """
    She will confirm that "This phone is mine!".
    """
    __mapper_args__ = {
        'polymorphic_identity': 'ownership_verification_sms'
    }

    def do_(self, context):  # pragma: no cove
        code = self.body['code']
        template = self.body['template']
        create_sms_provider().send_as_verification_code(self.to, code, template)
        logger.info('%s has been sent to %s with template %s', code, self.to, template)


class VerificationEmail(Email):
    """
    She will confirm that "This Email is mine!" by this Email.
    """

    __mapper_args__ = {
        'polymorphic_identity': 'verification_email'
    }

    template_filename = 'verification.mako'

    @property
    def email_body(self):
        body = self.body.copy()
        body.setdefault('receiver', self.to)
        body.setdefault('url', settings.email_verification.url)
        return body


class ResetPasswordEmail(Email):
    __mapper_args__ = {
        'polymorphic_identity': 'reset_password_email'
    }

    template_filename = 'reset_password.mako'

    @property
    def email_body(self):
        body = self.body.copy()
        body.setdefault('receiver', self.to)
        body.setdefault('url', settings.reset_password.url)
        return body
