import ujson

from stemerald.models import Admin, Client, Cryptocurrency
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As


class BalanceTestCase(WebTestCase):
    url = '/apiv2/balances'

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

        testnet = Cryptocurrency(symbol='TESTNET3', name='TESTNET3', wallet_id=1)
        rinkeby = Cryptocurrency(symbol='RINKEBY', name='RINKEBY', wallet_id=2)
        cls.session.add(testnet)
        cls.session.add(rinkeby)

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

        stexchange_client._set_instance(MockStexchangeClient())

    def test_balance_list(self):
        self.login('client1@test.com', '123456')

        response, ___ = self.request(As.client, 'OVERVIEW', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('name', response[0])
        self.assertIn('available', response[0])
        self.assertIn('freeze', response[0])
