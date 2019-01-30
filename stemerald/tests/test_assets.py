import ujson

from stemerald.models import Admin
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As


class AssetTestCase(WebTestCase):
    url = '/apiv1/assets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        cls.session.commit()

        class MockStexchangeClient(StexchangeClient):
            def __init__(self, headers=None):
                super().__init__("", headers)

            def asset_list(self):
                return ujson.loads('[{"name": "RINKEBY", "prec": 8}, {"name": "TESTNET3", "prec": 8}]')

            def asset_summary(self):
                return ujson.loads(
                    '[{"freeze_count": 0, "name": "RINKEBY", "total_balance": "1996.3", "available_count": 1, '
                    '"freeze_balance": "0", "available_balance": "1996.3"}, {"freeze_count": 0, "name": "TESTNET3", '
                    '"total_balance": "9137.8", "available_count": 1, "freeze_balance": "0", "available_balance": '
                    '"9137.8"}]'
                )

        stexchange_client._set_instance(MockStexchangeClient())

    def test_asset_list(self):
        response, ___ = self.request(As.anonymous, 'LIST', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('name', response[0])
        self.assertIn('prec', response[0])

    def test_asset_overview(self):
        # by admin
        self.login('admin1@test.com', '123456')

        response, ___ = self.request(As.admin, 'OVERVIEW', self.url)

        self.assertEqual(len(response), 2)
        self.assertIn('name', response[0])
        self.assertIn('totalBalance', response[0])
        self.assertIn('availableCount', response[0])
        self.assertIn('availableBalance', response[0])
        self.assertIn('freezeCount', response[0])
        self.assertIn('freezeBalance', response[0])
