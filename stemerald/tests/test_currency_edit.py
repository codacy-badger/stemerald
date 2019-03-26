from restfulpy.testing import FormParameter

from stemerald.models import Admin
from stemerald.models.currencies import Cryptocurrency, Fiat
from stemerald.tests.helpers import WebTestCase, As


class CurrencyEditTestCase(WebTestCase):
    url = '/apiv2/currencies'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        cls.session.add(Fiat(symbol='USD', name='USA Dollar'))
        cls.session.add(Cryptocurrency(symbol='BTC', name='Bitcoin', wallet_id='BTC'))

        cls.session.commit()

    def test_currency_edit(self):
        self.login('admin1@test.com', '123456')

        # TODO: These input values should not be normalized
        response, ___ = self.request(
            As.admin, 'EDIT', f'{self.url}/BTC',
            params=[
                FormParameter('withdrawMin', '100'),
                FormParameter('withdrawMax', '0'),
                FormParameter('withdrawStaticCommission', '23'),
                FormParameter('withdrawCommissionRate', '0.565'),
                FormParameter('withdrawMaxCommission', '23123'),
                FormParameter('depositMin', '0'),
                FormParameter('depositMax', '231'),
                FormParameter('depositStaticCommission', '743'),
                FormParameter('depositCommissionRate', '0.934'),
                FormParameter('depositMaxCommission', '9132'),
            ]
        )

        self.assertIn('symbol', response)
        self.assertIn('withdrawMin', response)
        self.assertIn('depositMin', response)
