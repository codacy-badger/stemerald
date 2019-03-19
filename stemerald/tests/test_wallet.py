import ujson

from restfulpy.testing import FormParameter

from stemerald.models import Client, Cryptocurrency
from stemerald.stawallet import StawalletClient, stawallet_client, StawalletHttpException
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As

current_balance = 3001

withdraw_min = 1000
withdraw_max = 599000
withdraw_static_commission = 129
withdraw_permille_commission = 23
withdraw_max_commission = 746

mock_address_usage = {'1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj': False}


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

            def post_invoice(self, wallet_id, user_id, force=False):
                if wallet_id == 1 and user_id == 1:
                    if mock_address_usage['1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj']:
                        return ujson.loads("""
                                    [ 
                                        {
                                          "id" : 2,
                                          "wallet" : "BTC",
                                          "extra" : null,
                                          "user" : "1",
                                          "creation" : "2019-03-19T12:11:10.337+03:00",
                                          "expiration" : null,
                                          "address" : {
                                            "id" : 2,
                                            "wallet" : "BTC",
                                            "address" : "1AJbsFZ64EpEfS5UAjAfcUG8pH8Jn3rn1F",
                                            "active" : true
                                          }
                                        } 
                                    ]
                                    """
                                           )
                    else:
                        raise StawalletHttpException(409, {})

            def get_deposits(self, wallet_id, user_id, page=0):
                if wallet_id == 1 and user_id == 1:
                    if mock_address_usage['1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj']:
                        return ujson.loads("""
                                        [{
                                          "id" : 1,
                                          "invoice" : {
                                            "id" : 1,
                                            "wallet" : "BTC",
                                            "extra" : null,
                                            "user" : "1",
                                            "creation" : "2019-03-19T12:38:11.310+03:00",
                                            "expiration" : null,
                                            "address" : {
                                              "id" : 2,
                                              "wallet" : "BTC",
                                              "address" : "1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj",
                                              "active" : true
                                            }
                                          },
                                          "grossAmount" : 198763,
                                          "netAmount" : 198000,
                                          "proof" : {
                                            "txHash" : "5061556f857e118aae8d948496f61f645e12cf7ca2a107f8e4ae78b535e86dfb",
                                            "blockHash" : "000000000000000000188252ee9277e8f60482a91b7f3cc9a4a7fb75ded482a8",
                                            "blockHeight" : 562456,
                                            "confirmationsLeft" : 0,
                                            "confirmationsTrace" : [ ],
                                            "link" : "https://www.blockchain.com/btc/tx/5061556f857e118aae8d948496f61f645e12cf7ca2a107f8e4ae78b535e86dfb",
                                            "extra" : null,
                                            "error" : null
                                          },
                                          "status" : "ACCEPTED",
                                          "extra" : null,
                                          "confirmed" : true
                                        }]"""
                                           )
                    else:
                        return ujson.loads("[]")

            def get_deposit(self, wallet_id, deposit_id):
                if wallet_id == 1 and deposit_id == 1:
                    if mock_address_usage['1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj']:
                        return ujson.loads("""
                                        {
                                          "id" : 1,
                                          "invoice" : {
                                            "id" : 1,
                                            "wallet" : "BTC",
                                            "extra" : null,
                                            "user" : "1",
                                            "creation" : "2019-03-19T12:38:11.310+03:00",
                                            "expiration" : null,
                                            "address" : {
                                              "id" : 2,
                                              "wallet" : "BTC",
                                              "address" : "1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj",
                                              "active" : true
                                            }
                                          },
                                          "grossAmount" : 198763,
                                          "netAmount" : 198000,
                                          "proof" : {
                                            "txHash" : "5061556f857e118aae8d948496f61f645e12cf7ca2a107f8e4ae78b535e86dfb",
                                            "blockHash" : "000000000000000000188252ee9277e8f60482a91b7f3cc9a4a7fb75ded482a8",
                                            "blockHeight" : 562456,
                                            "confirmationsLeft" : 0,
                                            "confirmationsTrace" : [ ],
                                            "link" : "https://www.blockchain.com/btc/tx/5061556f857e118aae8d948496f61f645e12cf7ca2a107f8e4ae78b535e86dfb",
                                            "extra" : null,
                                            "error" : null
                                          },
                                          "status" : "ACCEPTED",
                                          "extra" : null,
                                          "confirmed" : true
                                        }"""
                                           )

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

        stawallet_client._set_instance(MockStawalletClient())

    def test_deposit(self):
        self.login('client1@test.com', '123456')

        # 0. Deposit list should be empty
        response, ___ = self.request(
            As.client, 'LIST', self.deposit_url,
            query_string={'cryptocurrencySymbol': 'BTC', 'page': 0},
        )
        self.assertEqual(len(response), 0)

        # 1. Ask for a deposit address
        response, ___ = self.request(
            As.client, 'SHOW', self.deposit_url,
            query_string={'cryptocurrencySymbol': 'BTC'},
        )

        self.assertEqual(1, response['id'])
        self.assertEqual('1', response['user'])
        self.assertIsNotNone(response['creation'])
        self.assertIsNone(response['expiration'])
        self.assertIsNone(response['extra'])
        self.assertEqual('1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj', response['address'])

        # 2. Ask for a deposit address renew (face error, because of unused address)
        self.request(
            As.client, 'RENEW', self.deposit_url,
            query_string={'cryptocurrencySymbol': 'BTC'},
            expected_status=400,
            expected_headers={'x-reason': 'address-not-used'}
        )

        # Add a fake deposit
        mock_address_usage['1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj'] = True

        # 3. Check the deposit list
        response, ___ = self.request(
            As.client, 'LIST', self.deposit_url,
            query_string={'cryptocurrencySymbol': 'BTC', 'page': 0},
        )

        self.assertEqual(len(response), 1)
        self.assertEqual(1, response[0]['id'])
        self.assertEqual('1', response[0]['user'])
        self.assertIsNotNone(response[0]['netAmount'])
        self.assertIn('isConfirmed', response[0])
        self.assertIn('grossAmount', response[0])
        self.assertIn('txHash', response[0])
        self.assertIn('blockHeight', response[0])
        self.assertIn('blockHash', response[0])
        self.assertIn('link', response[0])
        self.assertIn('confirmationsLeft', response[0])
        self.assertIn('error', response[0])
        self.assertIn('invoice', response[0])
        self.assertIn('extra', response[0])
        self.assertIn('toAddress', response[0])

        # 4. Get new deposit by id
        response, ___ = self.request(
            As.client, 'GET', f'{self.deposit_url}/1',
            query_string={'cryptocurrencySymbol': 'BTC'},
        )

        self.assertEqual(1, response['id'])
        self.assertEqual('1', response['user'])

        # 5. Ask for address renew (successful)
        response, ___ = self.request(
            As.client, 'RENEW', self.deposit_url,
            query_string={'cryptocurrencySymbol': 'BTC'},
        )

        self.assertEqual(2, response['id'])  # Next id
        self.assertEqual('1', response['user'])
        self.assertEqual('1AJbsFZ64EpEfS5UAjAfcUG8pH8Jn3rn1F', response['address'])  # Another address

    # def test_withdraw(self):
    #     self.login('client1@test.com', '123456')
    #
    #     # 1. Schedule a withdraw (not enough credit)
    #     self.request(
    #         As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
    #         params=[
    #             FormParameter('cryptocurrencySymbol', 'BTC'),
    #             FormParameter('amount', 599000),
    #             FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
    #         ],
    #         expected_status=400
    #     )
    #
    #     # 2. Schedule a withdraw (bad address)
    #     self.request(
    #         As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
    #         params=[
    #             FormParameter('cryptocurrencySymbol', 'BTC'),
    #             FormParameter('amount', 2000),
    #             FormParameter('address', 'bad-address'),
    #         ],
    #         expected_status=400,
    #         expected_headers={'x-reason': 'bad-address'}
    #     )
    #
    #     # 3. Schedule a withdraw
    #     result, ___ = self.request(
    #         As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
    #         params=[
    #             FormParameter('cryptocurrencyCode', 'BTC'),
    #             FormParameter('amount', 2000),
    #             FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
    #         ],
    #     )
    #
    #     self.assertIn('id', result)
    #
    #     self.assertEqual(result['amount'], 2000)
    #     self.assertEqual(result['commission'], 175)
    #     self.assertEqual(result['address'], '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV')
    #
    #     self.assertIsNone(result['cryptotxId'])
    #     self.assertIsNone(result['error'])
    #
    #     # Check balance
    #     balance = stexchange_client.balance_query(self.mockup_client_1_id, 'BTC').get('BTC')
    #     self.assertEqual(int(balance['available']), 826)
    #     self.assertEqual(int(balance['freeze']), 0)
