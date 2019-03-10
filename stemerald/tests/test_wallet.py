# import ujson
#
# from restfulpy.testing import FormParameter
#
# from stemerald.models import Client, Cryptocurrency
# from stemerald.stawallet import StawalletClient, stawallet_client
# from stemerald.stexchange import StexchangeClient, stexchange_client
# from stemerald.tests.helpers import WebTestCase, As
#
# current_balance = 3001
#
# withdraw_min = 1000
# withdraw_max = 599000
# withdraw_static_commission = 129
# withdraw_permille_commission = 23
# withdraw_max_commission = 746
#
#
# class WalletTestCase(WebTestCase):
#     withdraw_url = '/apiv2/withdraws'
#     deposit_url = '/apiv2/deposits'
#
#     # noinspection PyArgumentList
#     @classmethod
#     def mockup(cls):
#         client1 = Client()
#         client1.email = 'client1@test.com'
#         client1.password = '123456'
#         client1.is_active = True
#         client1.is_email_verified = True
#         cls.session.add(client1)
#
#         cls.session.flush()
#
#         btc = Cryptocurrency(
#             symbol='BTC',
#             name='Bitcoin',
#             wallet_id=1,
#             withdraw_min=withdraw_min,
#             withdraw_max=withdraw_max,
#             withdraw_static_commission=withdraw_static_commission,
#             withdraw_permille_commission=withdraw_permille_commission,
#             withdraw_max_commission=withdraw_max_commission,
#         )
#         cls.session.add(btc)
#
#         cls.session.commit()
#
#         cls.mockup_client_1_id = client1.id
#
#         class MockStexchangeClient(StexchangeClient):
#             def __init__(self, headers=None):
#                 super().__init__("", headers)
#                 self.mock_balance = [0, 0]
#
#             def asset_list(self):
#                 return ujson.loads('[{"name": "BTC", "prec": 8}]')
#
#             def balance_update(self, user_id, asset, business, business_id, change, detail):
#                 if user_id == cls.mockup_client_1_id and business == 'withdraw' and asset == 'BTC':
#                     self.mock_balance[0] += int(change)
#                 return ujson.loads(
#                     '{"BTC": {"available": "' +
#                     str(self.mock_balance[0]) +
#                     '", "freeze": "' +
#                     str(self.mock_balance[1]) +
#                     '"}}'
#                 )
#
#             def balance_query(self, *args, **kwargs):
#                 return ujson.loads(
#                     '{"BTC": {"available": "' +
#                     str(self.mock_balance[0]) +
#                     '", "freeze": "' +
#                     str(self.mock_balance[1]) +
#                     '"}}'
#                 )
#
#         stexchange_client._set_instance(MockStexchangeClient())
#
#         class MockStawalletClient(StawalletClient):
#             def __init__(self, headers=None):
#                 super().__init__("", headers)
#                 self.mock_balance = [0, 0]
#
#             def asset_list(self):
#                 return ujson.loads('[{"name": "BTC", "prec": 8}]')
#
#             def balance_update(self, user_id, asset, business, business_id, change, detail):
#                 if user_id == cls.mockup_client_1_id and business == 'withdraw' and asset == 'BTC':
#                     self.mock_balance[0] += int(change)
#                 return ujson.loads(
#                     '{"BTC": {"available": "' +
#                     str(self.mock_balance[0]) +
#                     '", "freeze": "' +
#                     str(self.mock_balance[1]) +
#                     '"}}'
#                 )
#
#             def balance_query(self, *args, **kwargs):
#                 return ujson.loads(
#                     '{"BTC": {"available": "' +
#                     str(self.mock_balance[0]) +
#                     '", "freeze": "' +
#                     str(self.mock_balance[1]) +
#                     '"}}'
#                 )
#
#         stawallet_client._set_instance(MockStawalletClient())
#
#     def test_deposit(self):
#         self.login('client1@test.com', '123456')
#
#         # 1. Ask for a deposit address
#
#         # 2. Ask for a deposit address renew (face error, because of unused address)
#
#         # Add a fake deposit
#
#         # Check balance
#
#         # 3. Check the deposit list
#
#         # 4. Ask for address renew (successful)
#
#     def test_withdraw(self):
#         self.login('client1@test.com', '123456')
#
#         # 1. Schedule a withdraw (not enough credit)
#         self.request(
#             As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
#             params=[
#                 FormParameter('cryptocurrencySymbol', 'BTC'),
#                 FormParameter('amount', 599000),
#                 FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
#             ],
#             expected_status=400
#         )
#
#         # 2. Schedule a withdraw (bad address)
#         self.request(
#             As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
#             params=[
#                 FormParameter('cryptocurrencySymbol', 'BTC'),
#                 FormParameter('amount', 2000),
#                 FormParameter('address', 'bad-address'),
#             ],
#             expected_status=400,
#             expected_headers={'x-reason': 'bad-address'}
#         )
#
#         # 3. Schedule a withdraw
#         result, ___ = self.request(
#             As.semitrusted_client, 'SCHEDULE', self.withdraw_url,
#             params=[
#                 FormParameter('cryptocurrencyCode', 'BTC'),
#                 FormParameter('amount', 2000),
#                 FormParameter('address', '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV'),
#             ],
#         )
#
#         self.assertIn('id', result)
#
#         self.assertEqual(result['amount'], 2000)
#         self.assertEqual(result['commission'], 175)
#         self.assertEqual(result['address'], '2N2sn7skY9ZcDph2ougMdKn9a7tFj9ADhNV')
#
#         self.assertIsNone(result['cryptotxId'])
#         self.assertIsNone(result['error'])
#
#         # Check balance
#         balance = stexchange_client.balance_query(self.mockup_client_1_id, 'BTC').get('BTC')
#         self.assertEqual(int(balance['available']), 826)
#         self.assertEqual(int(balance['freeze']), 0)
