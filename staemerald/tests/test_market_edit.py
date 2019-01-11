from restfulpy.testing import FormParameter

from staemerald.models import Market, Cryptocurrency, Fiat, Admin
from staemerald.tests.helpers import WebTestCase, As


class MarketEditTestCase(WebTestCase):
    url = '/apiv1/markets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        usd = Fiat(code='usd', name='USA Dollar')
        btc = Cryptocurrency(code='btc', name='Bitcoin')
        ltc = Cryptocurrency(code='ltc', name='Litecoin')

        btc_usd = Market(base_currency=btc, quote_currency=usd, price_latest=10)
        ltc_btc = Market(base_currency=ltc, quote_currency=btc, price_latest=10)

        cls.session.add(usd)
        cls.session.add(btc)
        cls.session.add(ltc)
        cls.session.add(btc_usd)
        cls.session.add(ltc_btc)

        cls.session.commit()

        cls.btc_usd_id = btc_usd.id

    def test_currency_edit(self):
        self.login('admin1@test.com', '123456')

        response, ___ = self.request(
            As.admin, 'EDIT', f'{self.url}/{self.btc_usd_id}',
            params=[
                FormParameter('buyAmountMin', 0),
                FormParameter('buyAmountMax', 23),
                FormParameter('buyStaticCommission', 565),
                FormParameter('buyStaticCommission', 23123),
                FormParameter('buyPermilleCommission', 0),
                FormParameter('buyMaxCommission', 231),
                FormParameter('sellAmountMin', 743),
                FormParameter('sellAmountMax', 934),
                FormParameter('sellStaticCommission', 54),
                FormParameter('sellPermilleCommission', 345),
                FormParameter('sellMaxCommission', 0),
            ]
        )

        self.assertIn('id', response)
        self.assertIn('buyAmountMin', response)
        self.assertIn('sellAmountMin', response)
