import requests

from restfulpy.logging_ import get_logger

from stemerald.helpers import DeferredObject

logger = get_logger('STAWALLET_REST_CLIENT')

WALLETS_URL = "wallets"
INVOICES_URL = "invoices"
DEPOSITS_URL = "deposits"
WITHDRAWS_URL = "whitdraws"
QUOTES_URL = "quotes"


class StawalletClient:

    def __init__(self, server_url, headers=None):
        self.server_url = server_url
        self.headers = {'content-type': 'application/x-www-form-urlencoded'}
        self.headers.update(headers or {})

    def _execute(self, method, url, query_string: dict = None, body: dict = None):
        url = '/'.join([self.server_url, url])

        logger.debug(f"Requesting {method} over {url} with query: {query_string} with body: {body}")

        try:
            response = requests.request(
                params=query_string,
                method=method,
                url=url,
                data=body,
                headers=self.headers
            )

            print(response.url)
            print(response.text)
            if response.status_code == 200:
                return response.json()

            raise StawalletHttpException(response.status_code, response.text)

        except Exception as e:
            raise StawalletUnknownException(f"Request error: {str(e)}")

    def get_wallets(self):
        url = f'{WALLETS_URL}'
        return self._execute('get', url)

    def get_invoice(self, wallet_id, invoice_id):
        url = f'{WALLETS_URL}/{wallet_id}/{INVOICES_URL}/{invoice_id}'
        return self._execute('get', url)

    def get_invoices(self, wallet_id, user_id):
        url = f'{WALLETS_URL}/{wallet_id}/{INVOICES_URL}'
        query_string = {'user': user_id}
        return self._execute('get', url, query_string=query_string)

    def post_invoice(self, wallet_id, user_id, force=False):
        url = f'{WALLETS_URL}/{wallet_id}/{INVOICES_URL}'
        query_string = {'force': force}
        body = {'user': user_id}
        return self._execute('post', url, query_string=query_string, body=body)

    def get_deposits(self, wallet_id, user_id, page=0, asc=None, after=None):
        url = f'{WALLETS_URL}/{wallet_id}/{DEPOSITS_URL}'
        query_string = {'user': user_id, 'page': page}
        if asc is not None:
            query_string['asc'] = asc
        if after is not None:
            query_string['after'] = after
        return self._execute('get', url, query_string=query_string)

    def get_deposit(self, wallet_id, deposit_id):
        url = f'{WALLETS_URL}/{wallet_id}/{DEPOSITS_URL}/${deposit_id}'
        return self._execute('get', url)

    def get_withdraws(self, wallet_id, user_id, page=0):
        url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}'
        query_string = {'user': user_id, 'page': page}
        return self._execute('get', url, query_string=query_string)

    def get_withdraw(self, wallet_id, withdraw_id):
        url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/${withdraw_id}'
        return self._execute('get', url)

    def schedule_withdraw(
            self,
            wallet_id,
            user_id,
            business_uid,
            is_manual: bool,
            destination_address,
            amount_to_be_withdrawed,
            withdrawal_fee,
            estimated_network_fee,
            is_decharge=False
    ):
        url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}'
        body = {
            'user': user_id,
            'businessUid': business_uid,
            'isManual': is_manual,
            'target': destination_address,
            'netAmount': amount_to_be_withdrawed,
            'grossAmount': amount_to_be_withdrawed + withdrawal_fee,
            'estimatedNetworkFee': estimated_network_fee,
            'type': "decharge" if is_decharge else "withdraw",
        }
        return self._execute('post', url, body=body)

    def edit_withdraw(self, wallet_id, withdraw_id, is_manual: bool):
        url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/{withdraw_id}'
        body = {'isManual': is_manual}
        return self._execute('put', url, body=body)

    def resolve_withdraw(self, wallet_id, withdraw_id, final_network_fee, transaction_hash: str):
        url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/{withdraw_id}'
        body = {'finalNetworkFee': final_network_fee, 'txid': transaction_hash}
        return self._execute('put', url, body=body)

    def quote_withdraw(self,
                       wallet_id,
                       user_id,
                       business_uid,
                       destination_address,
                       amount,
                       ):
        url = f'{WALLETS_URL}/{wallet_id}/{QUOTES_URL}/{WITHDRAWS_URL}'
        query_string = {
            'user': user_id,
            'businessUid': business_uid,
            'target': destination_address,
            'amount': amount,
        }
        return self._execute('get', url, query_string=query_string)


class StawalletException(BaseException):
    def __init__(self, message):
        """
        :param message: error message
        """
        self.message = message
        logger.error(f"Stawallet REST Error: {message}")


class StawalletHttpException(StawalletException):
    def __init__(self, http_status_code: int, error: map):
        super(StawalletHttpException, self).__init__(f"http exception code {http_status_code} because of: {str(error)}")
        self.http_status_code = http_status_code


class StawalletUnknownException(StawalletException):
    def __init__(self, message=""):
        super(StawalletUnknownException, self).__init__(f"unknown exception: {message}")


if __name__ == '__main__':
    sx = StawalletClient(server_url="http://localhost:8080")

    print(sx.get_wallets())

    """
    Sample results:

    * {"status": "success"}
    """

stawallet_client: StawalletClient = DeferredObject(StawalletClient)
