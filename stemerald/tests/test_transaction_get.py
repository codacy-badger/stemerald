from stemerald.models import Client, Admin, Cryptocurrency, Cashin, Fiat, Cashout, BankAccount, BankCard
from stemerald.tests.helpers import WebTestCase, As


class TransactionGetTestCase(WebTestCase):
    url = '/apiv2/transactions'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        cls.session.add(Cryptocurrency(symbol='btc', name='Bitcoin', wallet_id=1))
        cls.session.add(Fiat(symbol='irr', name='Iran Rial'))

        cls.session.flush()

        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        cls.session.add(client1)

        # Adding a deposit

        # Adding a withdraw

        # Adding a shaparak-in
        shetab_address = BankCard()
        shetab_address.address = '0000-1111-2222-3333'
        shetab_address.client = client1
        shetab_address.is_verified = True
        shaparak_in = Cashin()
        shaparak_in.client = client1
        shaparak_in.amount = 342523
        shaparak_in.commission = 6323
        shaparak_in.currency_code = 'irr'
        shaparak_in.transaction_id = '34982309434583'
        shaparak_in.shetab_address = shetab_address
        cls.session.add(shaparak_in)

        # Adding a shaparak-out
        sheba_address = BankAccount()
        sheba_address.address = 'IR123444567889445535345345'
        sheba_address.client = client1
        sheba_address.is_verified = True
        shaparak_out = Cashout()
        shaparak_out.client = client1
        shaparak_out.amount = 5554
        shaparak_out.commission = 523
        shaparak_out.currency_code = 'irr'
        shaparak_out.error = 'some-error'
        shaparak_out.sheba_address = sheba_address
        cls.session.add(shaparak_out)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id

    def test_transaction_get(self):
        # 1. Get transactions by admin
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'GET', self.url, query_string={'clientId': self.mockup_client_1_id})

        self.assertEqual(len(result), 4)
        self.assertIn('id', result[0])
        self.assertIn('amount', result[0])
        self.assertIn('commission', result[0])
        self.assertIn('currencyCode', result[0])
        self.assertIn('type', result[0])

        # 2. Get transactions by client
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.client, 'GET', self.url)

        self.assertEqual(len(result), 4)
        self.assertIn('id', result[0])
        self.assertIn('amount', result[0])
        self.assertIn('commission', result[0])
        self.assertIn('currencyCode', result[0])
        self.assertIn('type', result[0])
