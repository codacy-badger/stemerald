from restfulpy.testing import FormParameter

from staemerald.models import Client, ShebaAddress, Admin, Fiat, Fund
from staemerald.tests.helpers import WebTestCase, As

current_balance = 3001

withdraw_min = 1000
withdraw_max = 599000
withdraw_static_commission = 129
withdraw_permille_commission = 23
withdraw_max_commission = 746

mockup_transaction_id = '4738'
mockup_amount = 4576


class TransactionShaparakInTestCase(WebTestCase):
    url = '/apiv1/transactions/shaparak-outs'

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
        client1.is_email_verified = True
        client1.is_evidence_verified = True
        cls.session.add(client1)

        client2 = Client()
        client2.email = 'client2@test.com'
        client2.password = '123456'
        client2.is_active = True
        client2.is_email_verified = True
        client2.is_evidence_verified = True
        cls.session.add(client2)

        irr = Fiat(
            code='irr',
            name='Iran Rial',
            withdraw_min=withdraw_min,
            withdraw_max=withdraw_max,
            withdraw_static_commission=withdraw_static_commission,
            withdraw_permille_commission=withdraw_permille_commission,
            withdraw_max_commission=withdraw_max_commission,
        )
        cls.session.add(irr)

        cls.session.add(Fund(client=client1, currency=irr, total_balance=current_balance))
        cls.session.add(Fund(client=client2, currency=irr, total_balance=0))

        # Mine, verified:
        sheba_address_1 = ShebaAddress(client=client1, address='IR123456789123456789123456', is_verified=True)
        # Mine, unverified:
        sheba_address_2 = ShebaAddress(client=client1, address='IR837498056254698443242343', is_verified=False)
        # Other's, verified:
        sheba_address_3 = ShebaAddress(client=client2, address='IR673943849382759839285634', is_verified=True)

        for address in [sheba_address_1, sheba_address_2, sheba_address_3]:
            cls.session.add(address)

        cls.session.commit()

        cls.mockup_client_1_id = client1.id

        cls.mockup_sheba_address_verified_id = sheba_address_1.id
        cls.mockup_sheba_address_unverified_id = sheba_address_2.id
        cls.mockup_sheba_address_others_id = sheba_address_3.id

    def test_transaction_deposit_create(self):
        self.login('client1@test.com', '123456')

        # 1. Schedule an Shaparak-Out transaction (another's sheba address)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 2000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_others_id),
        ], expected_status=400)

        # 2. Schedule an Shaparak-Out transaction (unverified sheba address)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 2000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_unverified_id),
        ], expected_status=409)

        # 3. Schedule an Shaparak-Out transaction (less than minimum or more than max)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 1, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ], expected_status=400)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 99999999999, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ], expected_status=400)

        # 4. Schedule an Shaparak-Out transaction (more than balance)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 599000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ], expected_status=400)

        # 4. Schedule an Shaparak-Out transaction (amount < balance < amount + commission)
        self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 3000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ], expected_status=400)

        # 5. Schedule an Shaparak-Out transaction (everything is good)
        result, ___ = self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 2000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ])

        transaction_id = result['id']

        # Check balance
        fund = self.session.query(Fund) \
            .filter(Fund.client_id == self.mockup_client_1_id) \
            .filter(Fund.currency_code == 'irr') \
            .one_or_none()
        self.assertEqual(fund.total_balance, 826)
        self.assertEqual(fund.blocked_balance, 0)

        # 6. Reject the Shaparak-Out request
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ])

        # Already rejected
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ], expected_status=400)
        self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '6786543'),
        ], expected_status=400)

        self.assertIsNone(result['referenceId'])

        # Check balance (cash back without commission)
        self.session.refresh(fund)
        self.assertEqual(fund.total_balance, 2826)
        self.assertEqual(fund.blocked_balance, 0)

        # 7. Accept the Shaparak-Out request ()
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.trusted_client, 'SCHEDULE', self.url, params=[
            FormParameter('amount', 2000, type_=int),
            FormParameter('shebaAddressId', self.mockup_sheba_address_verified_id),
        ])
        transaction_id = result['id']
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '3874948957'),
        ])

        # Already accepted
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'REJECT', f'{self.url}/{transaction_id}', params=[
            FormParameter('error', 'some-error'),
        ], expected_status=400)
        self.request(As.admin, 'ACCEPT', f'{self.url}/{transaction_id}', params=[
            FormParameter('referenceId', '45598'),
        ], expected_status=400)

        self.assertIsNotNone(result['referenceId'])

        # Check balance
        self.session.refresh(fund)
        self.assertEqual(fund.total_balance, 651)
        self.assertEqual(fund.blocked_balance, 0)
