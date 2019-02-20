import redis
from nanohttp import settings
from restfulpy.messaging import Messenger
from restfulpy.testing import ModelRestCrudTestCase

from stemerald import stemerald
from stemerald.sms import SmsProvider


class WebTestCase(ModelRestCrudTestCase):
    application = stemerald

    @classmethod
    def configure_app(cls):
        super().configure_app()
        settings.merge("""
        logging:
          handlers:
            console:
              level: warning
              
        sms:
          provider: stemerald.tests.helpers.MockupSmsProvider
        
        """)

    def login(self, email, password):
        result, metadata = self.request(None, 'POST', '/apiv2/sessions', doc=False, params={
            'email': email,
            'password': password
        })
        self.wsgi_app.jwt_token = result['token']
        return result['token']

    def logout(self):
        self.wsgi_app.jwt_token = ''

    @classmethod
    def _flush_redis_db(cls):
        redis.StrictRedis(
            host=settings.redis.host,
            port=settings.redis.port,
            db=settings.redis.db,
            password=settings.redis.password
        ).flushdb()


class As:
    anonymous = 'Anonymous'
    client = 'Client'
    distrusted_client = 'Distrusted_Client'
    semitrusted_client = 'Semitrusted_Client'
    trusted_client = 'Trusted_Client'
    admin = 'Admin'
    member = '|'.join((admin, client))
    everyone = '|'.join((admin, client, anonymous))


class MockupSmsProvider(SmsProvider):
    _last_message = None

    @property
    def last_message(self):
        return self.__class__._last_message

    @last_message.setter
    def last_message(self, value):
        self.__class__._last_message = value

    def send(self, to_number, text):
        super().send(to_number, text)
        self.last_message = {
            'to': to_number,
            'text': text
        }

    def send_as_verification_code(self, to_number, code, template):
        super().send_as_verification_code(to_number, code, template)
        self.last_message = {
            'to': to_number,
            'code': code,
            'template': template
        }


class MockupMessenger(Messenger):
    _last_message = None

    @property
    def last_message(self):
        return self.__class__._last_message

    @last_message.setter
    def last_message(self, value):
        self.__class__._last_message = value

    def send(self, to, subject, body, cc=None, bcc=None, template_filename=None, from_=None, attachments=None):
        """
        Sending messages by email
        """
        self.render_body(body, template_filename)
