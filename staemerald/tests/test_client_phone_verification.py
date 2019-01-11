from restfulpy.testing.documentation import FormParameter
from freezegun import freeze_time

from staemerald.models import Client, VerificationSms
from staemerald.sms import create_sms_provider
from staemerald.tests.helpers import WebTestCase, As


class ClientPhoneVerificationTestCase(WebTestCase):
    mobile_phone_url = '/apiv1/clients/mobile-phone-verifications'
    fixed_phone_url = '/apiv1/clients/fixed-phone-verifications'

    @classmethod
    def mockup(cls):
        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        client1.is_email_verified = True
        cls.session.add(client1)

        cls.session.commit()

        cls.client1_id = client1.id

        cls.mockup_mobile_phone = '+119954395345'
        cls.valid_mobile_verification_code = '168875'
        cls.bad_mobile_verification_code = '101010'

        cls.mockup_fixed_phone = '+112159409435'
        cls.valid_fixed_verification_code = '200666'
        cls.bad_fixed_verification_code = '101010'

    @freeze_time('2019-01-01')
    def test_client_mobile_phone_verification(self):
        self.login('client1@test.com', '123456')

        # A. Schedule a verification sms for mobile phone
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.mobile_phone_url,
            params=[FormParameter('phone', self.mockup_mobile_phone)]
        )

        # Sms check:
        messenger = create_sms_provider()
        task = VerificationSms.pop()
        task.do_(None)

        # noinspection PyUnresolvedReferences
        last_message = messenger.last_message

        self.assertEqual(last_message['to'], self.mockup_mobile_phone)
        self.assertEqual(last_message['code'], self.valid_mobile_verification_code)
        self.assertEqual(last_message['template'], 'mobile')

        # B. Validate the code

        # Invalid code
        self.request(
            As.semitrusted_client, 'VERIFY', self.mobile_phone_url,
            params=[
                FormParameter('phone', self.mockup_mobile_phone),
                FormParameter('code', self.bad_mobile_verification_code)
            ],
            expected_status=400
        )

        # Another phone
        self.request(
            As.semitrusted_client, 'VERIFY', self.mobile_phone_url,
            params=[
                FormParameter('phone', '+1100000000'),
                FormParameter('code', self.valid_mobile_verification_code)
            ],
            expected_status=400
        )

        # Invalid time
        with freeze_time('2020-01-01'):
            self.login('client1@test.com', '123456')
            self.request(
                As.semitrusted_client, 'VERIFY', self.mobile_phone_url,
                params=[
                    FormParameter('phone', self.mockup_mobile_phone),
                    FormParameter('code', self.valid_mobile_verification_code)
                ],
                expected_status=400
            )
        self.login('client1@test.com', '123456')

        # Correct code
        self.request(
            As.semitrusted_client, 'VERIFY', self.mobile_phone_url,
            params=[
                FormParameter('phone', self.mockup_mobile_phone),
                FormParameter('code', self.valid_mobile_verification_code)
            ],
        )

        # After verification we should get error while calling this service again
        self.login('client1@test.com', '123456')
        self.request(
            As.semitrusted_client, 'VERIFY', self.mobile_phone_url,
            params=[
                FormParameter('phone', self.mockup_mobile_phone),
                FormParameter('code', self.valid_mobile_verification_code)
            ],
            expected_status=409
        )

    @freeze_time('2019-01-01')
    def test_client_fixed_phone_verification(self):
        self.login('client1@test.com', '123456')

        # A. Schedule a verification sms for fixed phone
        self.request(
            As.semitrusted_client, 'SCHEDULE', self.fixed_phone_url,
            params=[FormParameter('phone', self.mockup_fixed_phone)]
        )

        # Sms check:
        messenger = create_sms_provider()
        task = VerificationSms.pop()
        task.do_(None)

        # noinspection PyUnresolvedReferences
        last_message = messenger.last_message

        self.assertEqual(last_message['to'], self.mockup_fixed_phone)
        self.assertEqual(last_message['code'], self.valid_fixed_verification_code)
        self.assertEqual(last_message['template'], 'fixed')

        # B. Validate the code

        # Invalid code
        self.request(
            As.semitrusted_client, 'VERIFY', self.fixed_phone_url,
            params=[
                FormParameter('phone', self.mockup_fixed_phone),
                FormParameter('code', self.bad_fixed_verification_code)
            ],
            expected_status=400
        )

        # Another phone
        self.request(
            As.semitrusted_client, 'VERIFY', self.fixed_phone_url,
            params=[
                FormParameter('phone', '+1100000000'),
                FormParameter('code', self.valid_fixed_verification_code)
            ],
            expected_status=400
        )

        # Invalid time
        with freeze_time('2020-01-01'):
            self.login('client1@test.com', '123456')
            self.request(
                As.semitrusted_client, 'VERIFY', self.fixed_phone_url,
                params=[
                    FormParameter('phone', self.mockup_fixed_phone),
                    FormParameter('code', self.valid_fixed_verification_code)
                ],
                expected_status=400
            )
        self.login('client1@test.com', '123456')

        # Correct code
        self.request(
            As.semitrusted_client, 'VERIFY', self.fixed_phone_url,
            params=[
                FormParameter('phone', self.mockup_fixed_phone),
                FormParameter('code', self.valid_fixed_verification_code)
            ],
        )

        # After verification we should get error while calling this service again
        self.login('client1@test.com', '123456')
        self.request(
            As.semitrusted_client, 'VERIFY', self.fixed_phone_url,
            params=[
                FormParameter('phone', self.mockup_fixed_phone),
                FormParameter('code', self.valid_fixed_verification_code)
            ],
            expected_status=409
        )
