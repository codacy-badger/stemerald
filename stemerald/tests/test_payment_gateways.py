import ujson

from restfulpy.testing import FormParameter

from stemerald.models import Client, BankAccount, Admin, Fiat, PaymentGateway
from stemerald.stexchange import StexchangeClient, stexchange_client
from stemerald.tests.helpers import WebTestCase, As

current_balance = 3001

cashout_min = 1000
cashout_max = 599000
cashout_static_commission = 129
cashout_commission_rate = '0.023'
cashout_max_commission = 746

mockup_transaction_id = '4738'
mockup_amount = 4576


class PaymentGatewayTestCase(WebTestCase):
    url = '/apiv2/transactions/payment-gateways'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        irr = Fiat(
            symbol='IRR',
            name='Iran Rial',
        )
        cls.session.add(irr)

        # Adding a payment gateway
        shaparak = PaymentGateway()
        shaparak.name = "shaparak"
        shaparak.fiat_symbol = "IRR"
        shaparak.cashout_min = cashout_min,
        shaparak.cashout_max = cashout_max,
        shaparak.cashout_static_commission = cashout_static_commission
        shaparak.cashout_commission_rate = cashout_commission_rate
        shaparak.cashout_max_commission = cashout_max_commission
        cls.session.add(shaparak)

        cls.session.commit()

        cls.mockup_payment_gateway_name = shaparak.name

    def test_payment_gateways(self):
        result, ___ = self.request(As.anonymous, 'GET', self.url)

        self.assertEqual(len(result), 1)
        self.assertIn(result[0]['name'], 'shaparak')
        self.assertIn(result[0]['fiatSymbol'], 'IRR')
        self.assertIn('cashoutMin', result[0])
        self.assertIn('cashoutMax', result[0])
        self.assertIn('cashoutStaticCommission', result[0])
        self.assertIn('cashoutCommissionRate', result[0])
        self.assertIn('cashoutMaxCommission', result[0])
