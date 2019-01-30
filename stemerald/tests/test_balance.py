import ujson

from stemerald.models import Admin, Client
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As


class BalanceTestCase(WebTestCase):
    url = '/apiv1/balances'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        cls.session.commit()

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)

            def asset_list(self):
                return ujson.loads('[{"name": "RINKEBY", "prec": 8}, {"name": "TESTNET3", "prec": 8}]')

            def balance_query(self, *args, **kwargs):
                return ujson.loads(
                    '{"TESTNET3": {"available": "9137.8", "freeze": "0"}, "RINKEBY": {"available": "100.65", '
                    '"freeze": "10.01"}}'
                )

            def balance_history(self, *args, **kwargs):
                return ujson.loads(
                    '{"offset": 0, "limit": 10, "records": [{"time": 1547419212.987738, "asset": "TESTNET3", '
                    '"balance": "9137.8", "change": "100", "business": "null", "detail": {"id": 1547419212}}, '
                    '{"time": 1547419172.410369, "asset": "TESTNET3", "balance": "9038.4", "change": "100", '
                    '"business": "null", "detail": {"id": 1547419172}}, {"time": 1547419117.182499, '
                    '"asset": "TESTNET3", "balance": "8939", "change": "100", "business": "null", "detail": {"id": '
                    '1547419117}}, {"time": 1547419093.216783, "asset": "TESTNET3", "balance": "8839.6", '
                    '"change": "100", "business": "null", "detail": {"id": 1547419093}}, {"time": 1547419090.127026, '
                    '"asset": "TESTNET3", "balance": "8740.2", "change": "100", "business": "null", "detail": {"id": '
                    '1547419090}}, {"time": 1547419079.001812, "asset": "TESTNET3", "balance": "8640.8", '
                    '"change": "100", "business": "null", "detail": {"id": 1547419078}}, {"time": 1547419050.210154, '
                    '"asset": "TESTNET3", "balance": "8541", "change": "100", "business": "null", "detail": {"id": '
                    '1547419050}}, {"time": 1547419045.657284, "asset": "TESTNET3", "balance": "8441.2", '
                    '"change": "100", "business": "null", "detail": {"id": 1547419045}}, {"time": 1547419044.539546, '
                    '"asset": "TESTNET3", "balance": "8341.4", "change": "100", "business": "null", "detail": {"id": '
                    '1547419044}}, {"time": 1547419042.979995, "asset": "TESTNET3", "balance": "8241.6", '
                    '"change": "100", "business": "null", "detail": {"id": 1547419042}}]}'
                )

        stexchange_client._set_instance(MockStexchangeClient())

    def test_balance_list(self):
        self.login('client1@test.com', '123456')

        response, ___ = self.request(As.client, 'OVERVIEW', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('name', response[0])
        self.assertIn('available', response[0])
        self.assertIn('freeze', response[0])
