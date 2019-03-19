import ujson

from restfulpy.testing import FormParameter

from stemerald.models import Client, Cryptocurrency
from stemerald.stawallet import StawalletClient, stawallet_client
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As

current_balance = 3001

withdraw_min = 1000
withdraw_max = 599000
withdraw_static_commission = 129
withdraw_permille_commission = 23
withdraw_max_commission = 746


class WalletTestCase(WebTestCase):
    withdraw_url = '/apiv2/withdraws'
    deposit_url = '/apiv2/deposits'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        cls.session.add(client1)

        cls.session.flush()

        btc = Cryptocurrency(
            symbol='BTC',
            name='Bitcoin',
            wallet_id=1,
            withdraw_min=withdraw_min,
            withdraw_max=withdraw_max,
            withdraw_static_commission=withdraw_static_commission,
            withdraw_permille_commission=withdraw_permille_commission,
            withdraw_max_commission=withdraw_max_commission,
        )
        cls.session.add(btc)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)
                self.mock_balance = [0, 0]

            def asset_list(self):
                return ujson.loads('[{"name": "BTC", "prec": 8}]')

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if user_id == cls.mockup_client_1_id and business == 'withdraw' and asset == 'BTC':
                    self.mock_balance[0] += int(change)
                return ujson.loads(
                    '{"BTC": {"available": "' +
                    str(self.mock_balance[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance[1]) +
                    '"}}'
                )

            def balance_query(self, *args, **kwargs):
                return ujson.loads(
                    '{"BTC": {"available": "' +
                    str(self.mock_balance[0]) +
                    '", "freeze": "' +
                    str(self.mock_balance[1]) +
                    '"}}'
                )

        stexchange_client._set_instance(MockStexchangeClient())

        class MockStawalletClient(StawalletClient):
            def __init__(self, headers=None):
                super().__init__("", headers)
                self.mock_balance = [0, 0]

            # def get_wallets(self):
            #     return [{
            #         'id': '1',
            #         'balance': '1',
            #         'secret': '1',
            #         'onchainStatus': '1',
            #     }]

            def get_invoice(self, wallet_id, invoice_id):
                if wallet_id == 1 and invoice_id == 1:
                    return ujson.loads("""
                                        {
                                          "id" : 1,
                                          "wallet" : "BTC",
                                          "extra" : null,
                                          "user" : "1",
                                          "creation" : "2019-03-19T12:11:10.337+03:00",
                                          "expiration" : null,
                                          "address" : {
                                            "id" : 2,
                                            "wallet" : "BTC",
                                            "address" : "1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj",
                                            "active" : true
                                          }
                                        } 
                                    """
                                       )

            def get_invoices(self, wallet_id, user_id):
                if wallet_id == 1 and user_id == 1:
                    return ujson.loads("""
                                    [ 
                                        {
                                          "id" : 1,
                                          "wallet" : "BTC",
                                          "extra" : null,
                                          "user" : "1",
                                          "creation" : "2019-03-19T12:11:10.337+03:00",
                                          "expiration" : null,
                                          "address" : {
                                            "id" : 2,
                                            "wallet" : "BTC",
                                            "address" : "1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj",
                                            "active" : true
                                          }
                                        } 
                                    ]
                                    """
                                       )
            # def post_invoice(self, wallet_id, user_id, force=False):
            #     url = f'{WALLETS_URL}/{wallet_id}/{INVOICES_URL}'
            #     query_string = {'force': force}
            #     body = {'user': user_id}
            #     return self._execute('post', url, query_string=query_string, body=body)
            #
            # def get_deposits(self, wallet_id, user_id, page=0):
            #     url = f'{WALLETS_URL}/{wallet_id}/{DEPOSITS_URL}'
            #     query_string = {'user': user_id, 'page': page}
            #     return self._execute('get', url, query_string=query_string)
            #
            # def get_deposit(self, wallet_id, deposit_id):
            #     url = f'{WALLETS_URL}/{wallet_id}/{DEPOSITS_URL}/${deposit_id}'
            #     return self._execute('get', url)
            #
            # def get_withdraws(self, wallet_id, user_id, page=0):
            #     url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}'
            #     query_string = {'user': user_id, 'page': page}
            #     return self._execute('get', url, query_string=query_string)
            #
            # def get_withdraw(self, wallet_id, withdraw_id):
            #     url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/${withdraw_id}'
            #     return self._execute('get', url)
            #
            # def schedule_withdraw(
            #         self,
            #         wallet_id,
            #         user_id,
            #         business_uid,
            #         is_manual: bool,
            #         destination_address,
            #         amount_to_be_withdrawed,
            #         withdrawal_fee,
            #         estimated_network_fee,
            #         is_decharge=False
            # ):
            #     url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}'
            #     body = {
            #         'user': user_id,
            #         'businessUid': business_uid,
            #         'isManual': is_manual,
            #         'target': destination_address,
            #         'netAmount': amount_to_be_withdrawed,
            #         'grossAmount': amount_to_be_withdrawed + withdrawal_fee,
            #         'estimatedNetworkFee': estimated_network_fee,
            #         'type': "decharge" if is_decharge else "withdraw",
            #     }
            #     return self._execute('post', url, body=body)
            #
            # def edit_withdraw(self, wallet_id, withdraw_id, is_manual: bool):
            #     url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/{withdraw_id}'
            #     body = {'isManual': is_manual}
            #     return self._execute('put', url, body=body)
            #
            # def resolve_withdraw(self, wallet_id, withdraw_id, final_network_fee, transaction_hash: str):
            #     url = f'{WALLETS_URL}/{wallet_id}/{WITHDRAWS_URL}/{withdraw_id}'
            #     body = {'finalNetworkFee': final_network_fee, 'txid': transaction_hash}
            #     return self._execute('put', url, body=body)
            #
            # def asset_list(self):
            #     return ujson.loads('[{"name": "BTC", "prec": 8}]')
            #
            # def asset_list(self):
            #     return ujson.loads('[{"name": "BTC", "prec": 8}]')
            #
            # def balance_update(self, user_id, asset, business, business_id, change, detail):
            #     if user_id == cls.mockup_client_1_id and business == 'withdraw' and asset == 'BTC':
            #         self.mock_balance[0] += int(change)
            #     return ujson.loads(
            #         '{"BTC": {"available": "' +
            #         str(self.mock_balance[0]) +
            #         '", "freeze": "' +
            #         str(self.mock_balance[1]) +
            #         '"}}'
            #     )
            #
            # def balance_query(self, *args, **kwargs):
            #     return ujson.loads(
            #         '{"BTC": {"available": "' +
            #         str(self.mock_balance[0]) +
            #         '", "freeze": "' +
            #         str(self.mock_balance[1]) +
            #         '"}}'
            #     )

        stawallet_client._set_instance(MockStawalletClient())

    def test_deposit(self):
        self.login('client1@test.com', '123456')

        # 1. Ask for a deposit address
        self.login('client1@test.com', '123456')

        response, ___ = self.request(As.client, 'SHOW', self.deposit_url,
                                     query_string={'cryptocurrencySymbol': 'BTC'}, )

        self.assertEqual(1, response['id'])
        self.assertEqual('1', response['user'])
        self.assertIsNotNone(response['creation'])
        self.assertIsNone(response['expiration'])
        self.assertIsNone(response['extra'])
        self.assertEqual('1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj', response['address'])

        # 2. Ask for a deposit address renew (face error, because of unused address)

        # Add a fake deposit

        # Check balance

        # 3. Check the deposit list

        # 4. Ask for address renew (successful)

    def test_withdraw(self):
        self.login('client1@test.com', '123456')

        # 1. Schedule a withdraw (not enough credit)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 599000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
            ],
            expected_status=400
        )

        # 2. Schedule a withdraw (bad address)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 2000),
                FormParameter('address', 'bad-address'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-address'}
        )

        # 3. Schedule a withdraw
        result, ___ = self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencyCode', 'BTC'),
                FormParameter('amount', 2000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
            ],
        )

        self.assertIn('id', result)

        self.assertEqual(result['amount'], 2000)
        self.assertEqual(result['commission'], 175)
        self.assertEqual(result['address'], '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV')

        self.assertIsNone(result['cryptotxId'])
        self.assertIsNone(result['error'])

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'BTC').get('BTC')
        self.assertEqual(int(balance['available']), 826)
        self.assertEqual(int(balance['freeze']), 0)
