from stemerald.models import Client, Market, Fund
from stemerald.models.currencies import Cryptocurrency, Fiat
from stemerald.tests.helpers import WebTestCase, As


class ClientFundGetTestCase(WebTestCase):
    url = '/apiv1/clients/funds'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)
        cls.session.commit()

        usd = Fiat(code='usd', name='USA Dollar')
        btc = Cryptocurrency(code='btc', name='Bitcoin')
        ltc = Cryptocurrency(code='ltc', name='Litecoin')
        cls.session.add(usd)
        cls.session.add(btc)
        cls.session.add(ltc)

        btc_usd = Market(base_currency=btc, quote_currency=usd, price_latest=47383)
        cls.session.add(btc_usd)

        cls.session.commit()

        usd_fund1 = Fund(client=client1, currency=usd)
        usd_fund1.total_balance = 456

        btc_fund1 = Fund(client=client1, currency=btc)
        btc_fund1.total_balance = 18734
        btc_fund1.blocked_balance = 565

        ltc_fund1 = Fund(client=client1, currency=ltc)

        cls.session.add(usd_fund1)
        cls.session.add(btc_fund1)
        cls.session.add(ltc_fund1)
        cls.session.commit()

        cls.client1_id = client1.id
        cls.btc_usd_id = btc_usd.id

    def test_client_funds_get(self):
        self._flush_redis_db()
        self.login('client1@test.com', '123456')

        response, ___ = self.request(As.client, 'GET', self.url)

        btc_fund = list(filter(lambda x: x['currencyCode'] == 'btc', response))[0]
        usd_fund = list(filter(lambda x: x['currencyCode'] == 'usd', response))[0]
        ltc_fund = list(filter(lambda x: x['currencyCode'] == 'ltc', response))[0]

        self.assertEqual(btc_fund['totalBalance'], 18734)
        self.assertEqual(btc_fund['blockedBalance'], 565)
        self.assertEqual(usd_fund['totalBalance'], 456)
        self.assertEqual(usd_fund['blockedBalance'], 0)
        self.assertEqual(ltc_fund['totalBalance'], 0)
        self.assertEqual(ltc_fund['blockedBalance'], 0)
