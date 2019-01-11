from restfulpy.testing import FormParameter

from staemerald.models import Admin
from staemerald.models.currencies import Cryptocurrency, Fiat
from staemerald.tests.helpers import WebTestCase, As


class CurrencyEditTestCase(WebTestCase):
    url = '/apiv1/currencies'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        cls.session.add(Fiat(code='usd', name='USA Dollar'))
        cls.session.add(Cryptocurrency(code='btc', name='Bitcoin'))

        cls.session.commit()

    def test_currency_edit(self):
        self.login('admin1@test.com', '123456')

        response, ___ = self.request(
            As.admin, 'EDIT', f'{self.url}/btc',
            params=[
                FormParameter('withdrawMin', 100),
                FormParameter('withdrawMax', 0),
                FormParameter('withdrawStaticCommission', 23),
                FormParameter('withdrawPermilleCommission', 565),
                FormParameter('withdrawMaxCommission', 23123),
                FormParameter('depositMin', 0),
                FormParameter('depositMax', 231),
                FormParameter('depositStaticCommission', 743),
                FormParameter('depositPermilleCommission', 934),
                FormParameter('depositMaxCommission', 9132),
            ]
        )

        self.assertIn('code', response)
        self.assertIn('withdrawMin', response)
        self.assertIn('depositMin', response)
