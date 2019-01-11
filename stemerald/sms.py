import requests
from nanohttp import settings
from restfulpy.logging_ import get_logger
from restfulpy.utils import construct_class_by_name

logger = get_logger('SMS')


class SmsSendingError(Exception):
    def __init__(self, response):
        logger.info(f'Error sending sms: {response.text}')


class SmsProvider:
    def send(self, to_number, text):
        logger.info(
            'SMS is sending for number : %s with text : %s by : %s' % (to_number, text, self.__class__.__name__)
        )

    def send_as_verification_code(self, to_number, token, template):
        logger.info(
            'SMS is sending for number : %s with token : %s with template %s by : %s' %
            (to_number, token, template, self.__class__.__name__)
        )


class ConsoleSmsProvider(SmsProvider):  # pragma: no cover
    def send(self, to_number, text):
        super().send(to_number, text)
        print('SMS send request received for number : %s with text : %s' % (to_number, text))

    def send_as_verification_code(self, to_number, token, template):
        super().send_as_verification_code(to_number, token, template)
        print('Verification SMS send request received for number : %s with token : %s with template %s by : %s' %
              (to_number, token, template, self.__class__.__name__))


class KavenegarSmsProvider(SmsProvider):
    @classmethod
    def _request(cls, url, data):
        response = requests.request('POST', url, params=data)

        if response.status_code != 200:
            raise SmsSendingError(response)

        return response.json()

    def send(self, to_number, text):
        raise NotImplementedError

    def send_as_verification_code(self, to_number, token, template):
        super().send_as_verification_code(to_number, token, template)

        self._request(settings.sms.kavenegar.verification_code_url, {
            'receptor': to_number,
            'token': token,
            'template': template,
        })


# FIXME: DO NOT create this object every time
def create_sms_provider() -> SmsProvider:
    return construct_class_by_name(settings.sms.provider)
