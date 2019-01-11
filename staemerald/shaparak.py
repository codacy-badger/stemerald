import requests
from nanohttp.configuration import settings
from restfulpy.logging_ import get_logger
from restfulpy.utils import construct_class_by_name

logger = get_logger('PAYMENT')


class ShaparakError(Exception):
    def __init__(self, response):
        super().__init__()
        error = response.text if response else 'NA'
        logger.info(f'Unsuccessful payment: {error}')


class ShaparakProvider:
    def create_transaction(self, batch_id, amount):
        """
        :param batch_id: Id of transaction record in our system
        :param amount: amount
        :return: Transaction id (returned from payment gateway)
        """
        raise NotImplementedError

    def verify_transaction(self, transaction_id):
        """
        :param transaction_id: Id of transaction in pay.ir
        :return: (amount, reference_id, card_address)
        """
        raise NotImplementedError


class PayIrProvider(ShaparakProvider):  # pragma: no cover
    send_url = 'https://pay.ir/payment/send'
    verify_url = 'https://pay.ir/payment/verify'

    def __init__(self):
        self.api_key = settings.shaparak.pay_ir.api_key
        self.redirect_url = settings.shaparak.pay_ir.post_redirect_url

    @classmethod
    def _request(cls, url, data):
        response = requests.request('POST', url, data=data)

        if response.status_code != 200:
            raise ShaparakError(response.text)

        response = response.json()

        if response['status'] != 1:
            raise ShaparakError(response.text)

        return response

    def create_transaction(self, batch_id, amount):
        response = self._request(self.send_url, data={
            'api': self.api_key,
            'amount': amount,
            'redirect': self.redirect_url,
            'factorNumber': batch_id,
        })

        return response['transId']

    def verify_transaction(self, transaction_id):
        response = self._request(self.verify_url, data={
            'api': self.api_key,
            'transId': transaction_id,
        })

        return response['amount'], '0000-0000-0000-0000', 0  # FIXME: Add shaparak_card_address and reference_id


# FIXME: DO NOT create this object every time
def create_shaparak_provider() -> ShaparakProvider:
    return construct_class_by_name(settings.shaparak.provider)
