import ujson

from restfulpy.testing import FormParameter

from stemerald.models import Client, Cryptocurrency
from stemerald.stawallet import StawalletClient, stawallet_client, StawalletHttpException
from stemerald.stexchange import StexchangeClient, stexchange_client, BalanceNotEnoughException
from stemerald.tests.helpers import WebTestCase, As

current_balance = 3001

withdraw_min = 1000
withdraw_max = 599000
withdraw_static_commission = 129
withdraw_permille_commission = 23
withdraw_max_commission = 746

mock_address_usage = {'1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj': False}
mock_business_uid_usage = {'abc-def-gh': False}


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
            wallet_id='BTC',
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
                self.mock_balance = [2200, 0]

            def asset_list(self):
                return ujson.loads('[{"name": "BTC", "prec": 8}]')

            def balance_update(self, user_id, asset, business, business_id, change, detail):
                if int(change) < 0 and self.mock_balance[0] + int(change) < 0:
                    raise BalanceNotEnoughException(1)

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
                if wallet_id == 'BTC' and invoice_id == 1:
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
                if wallet_id == 'BTC' and user_id == 1:
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
                if wallet_id == 'BTC' and user_id == 1:
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
                if wallet_id == 'BTC' and user_id == 1:
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
                if wallet_id == 'BTC' and deposit_id == 1:
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

            def get_withdraws(self, wallet_id, user_id, page=0):
                if wallet_id == 'BTC' and user_id == 1:
                    if mock_address_usage['1D6CqUvHtQRXU4TZrrj5j1iofo8f4oXyLj']:
                        return ujson.loads("""
                            [ {
                              "id" : 1,
                              "businessUid" : "c0d9c0a7-6eb4-4e03-a324-f53a8be1b789",
                              "wallet" : "test-btc-wallet",
                              "user" : "1",
                              "target" : "1Mwz1i3MK7AruNFwF3X84FK4qMmpooLtZG",
                              "netAmount" : 65020000,
                              "grossAmount" : 65740000,
                              "estimatedNetworkFee" : 50000,
                              "finalNetworkFee" : null,
                              "type" : "withdraw",
                              "status" : "queued",
                              "txid" : null,
                              "proof" : null,
                              "issuedAt" : "2019-03-20T12:55:46.390+03:00",
                              "paidAt" : null,
                              "trace" : null,
                              "manual" : true
                            } ]"""
                                           )

            def get_withdraw(self, wallet_id, withdraw_id):
                return ujson.loads(
                    """
                    {
                      "id" : 1,
                      "businessUid" : "abc-def-gh",
                      "wallet" : "test-btc-wallet",
                      "user" : "1",
                      "target" : "2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV",
                      "netAmount" : 65020000,
                      "grossAmount" : 65740000,
                      "estimatedNetworkFee" : 50000,
                      "finalNetworkFee" : null,
                      "type" : "withdraw",
                      "status" : "queued",
                      "txid" : null,
                      "proof" : null,
                      "issuedAt" : "2019-03-20T12:54:44.009+03:00",
                      "paidAt" : null,
                      "trace" : null,
                      "manual" : true
                    }"""
                )

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
                mock_business_uid_usage['abc-def-gh'] = True
                return ujson.loads("""{
                      "id" : 2,
                      "businessUid" : "abc-def-gh",
                      "wallet" : "test-btc-wallet",
                      "user" : "1",
                      "target" : "2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV",
                      "netAmount" : 2000,
                      "grossAmount" : 2175,
                      "estimatedNetworkFee" : 0,
                      "finalNetworkFee" : null,
                      "type" : "withdraw",
                      "status" : "queued",
                      "txid" : null,
                      "proof" : null,
                      "issuedAt" : "2019-03-20T12:52:26.948+03:00",
                      "paidAt" : null,
                      "trace" : "2019-03-20T12:52:38.228+03:00 : Issued (automatic)",
                      "manual" : true
                    }""")

            def edit_withdraw(self, wallet_id, withdraw_id, is_manual: bool):
                return ujson.loads(
                    """
                    {
                      "id" : 2,
                      "businessUid" : "abc-def-gh",
                      "wallet" : "test-btc-wallet",
                      "user" : "1",
                      "target" : "2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV",
                      "netAmount" : 93511223,
                      "grossAmount" : 93583223,
                      "estimatedNetworkFee" : 485385,
                      "finalNetworkFee" : null,
                      "type" : "withdraw",
                      "status" : "waiting_manual",
                      "txid" : null,
                      "proof" : null,
                      "issuedAt" : "2019-03-20T12:52:26.948+03:00",
                      "paidAt" : null,
                      "trace" : "2019-03-20T12:52:38.228+03:00 : Issued (automatic)\n2019-03-20T12:53:28.001+03:00 : Change to manual",
                      "manual" : true
                    }"""
                )

            def resolve_withdraw(self, wallet_id, withdraw_id, final_network_fee, transaction_hash: str):
                return ujson.loads(
                    """
                    {
                      "id" : 2,
                      "businessUid" : "abc-def-gh",
                      "wallet" : "test-btc-wallet",
                      "user" : "1",
                      "target" : "2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV",
                      "netAmount" : 93511223,
                      "grossAmount" : 93583223,
                      "estimatedNetworkFee" : 485385,
                      "finalNetworkFee" : 485385,
                      "type" : "withdraw",
                      "status" : "pushed",
                      "txid" : "b6f6991d03df0e2e04dafffcd6bc418aac66049e2cd74b80f14ac86db1e3f0da",
                      "proof" : null,
                      "issuedAt" : "2019-03-20T12:52:26.948+03:00",
                      "paidAt" : "2019-03-20T12:54:08.547+03:00",
                      "trace" : "2019-03-20T12:52:38.228+03:00 : Issued (automatic)\n2019-03-20T12:53:28.001+03:00 : Change to manual\n2019-03-20T12:54:08.547+03:00 : Submit manual withdrawal info",
                      "manual" : null
                    }"""
                )

            def quote_withdraw(self, wallet_id, user_id, business_uid, destination_address, amount):
                return ujson.loads("""
                {
                  "estimatedNetworkFee" : 0,
                  "hasSufficientWalletBalance" : true,
                  "estimatedSendingTime" : 0,
                  "estimatedReceivingTime" : 0,
                  "errors" : [ ],
                  "addressValid" : """ + str(len(destination_address) >= 30).lower() + """,
                  "networkUp" : true,
                  "sendingManually" : false,
                  "userEligible" : true,
                  "businessUidDuplicated" : """ + str(mock_business_uid_usage['abc-def-gh']).lower() + """,
                  "businessUidValid" : true,
                  "amountValid" : true
                }"""
                                   )

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

    def test_withdraw(self):
        self.login('client1@test.com', '123456')

        # 1. Schedule a withdraw (not enough credit)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 599000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
                FormParameter('businessUid', 'abc-def-gh'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'not-enough-balance'}
        )

        # 2. Schedule a withdraw (bad address)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 2000),
                FormParameter('address', 'bad-address'),
                FormParameter('businessUid', 'abc-def-gh'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'bad-address'}
        )

        # 3. Schedule a withdraw
        result, ___ = self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 2000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
                FormParameter('businessUid', 'abc-def-gh'),
            ],
        )

        self.assertIn('id', result)

        self.assertEqual(result['netAmount'], 2000)
        self.assertEqual(result['grossAmount'], 2000 + 175)
        self.assertEqual(result['toAddress'], '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV')

        self.assertIsNone(result['txid'])
        self.assertIsNone(result['error'])

        # Check balance
        balance = stexchange_client.balance_query(self.mockup_client_1_id, 'BTC').get('BTC')
        self.assertEqual(int(balance['available']), 25)
        self.assertEqual(int(balance['freeze']), 0)

        # 4. Schedule a withdraw (duplicated businessUid)
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
            params=[
                FormParameter('cryptocurrencySymbol', 'BTC'),
                FormParameter('amount', 2000),
                FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
                FormParameter('businessUid', 'abc-def-gh'),
            ],
            expected_status=400,
            expected_headers={'x-reason': 'already-submitted'}
        )
