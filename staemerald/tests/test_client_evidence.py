from datetime import datetime
from os.path import join, exists

from nanohttp import settings
from restfulpy.testing.documentation import FormParameter

from staemerald.models import Client, Admin, Country, State, City
from staemerald.tests import STUFF_DIR
from staemerald.tests.helpers import WebTestCase, As


class ClientEvidenceTestCase(WebTestCase):
    url = '/apiv1/clients/evidences'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        cls.mockup_id_card = join(STUFF_DIR, 'test-image-1.jpg')
        cls.mockup_id_card_secondary = join(STUFF_DIR, 'test-image-2.png')

        iran = Country(name='Iran', code='ir', phone_prefix=98)
        tehran_state = State(name='Tehran', country=iran)
        tehran_city = City(name='Tehran', state=tehran_state)

        cls.session.add(tehran_city)

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
        client1.evidence.mobile_phone = '+77777777777'
        client1.evidence.fixed_phone = '+888888888'
        cls.session.add(client1)

        cls.session.commit()

        cls.city1_id = tehran_city.id
        cls.client1_id = client1.id

    def test_client_evidence(self):
        # 1. Submit a evidence
        self.login('client1@test.com', '123456')
        self.request(As.semitrusted_client, 'SUBMIT', self.url, params=[
            FormParameter('firstName', 'test-first-name'),
            FormParameter('lastName', 'test-last-name'),
            FormParameter('gender', 'female'),
            FormParameter('birthday', datetime.now().isoformat()),
            FormParameter('cityId', self.city1_id),
            FormParameter('nationalCode', '349588398689'),
            FormParameter('address', 'test-test-test-test-no.12'),
            FormParameter('idCard', self.mockup_id_card, type_='file'),
            FormParameter('idCardSecondary', self.mockup_id_card_secondary, type_='file'),
        ])

        client = self.session.query(Client).filter(Client.id == self.client1_id).one_or_none()
        assert exists(join(settings.media_storage.file_system_dir, client.evidence._id_card.path))
        assert exists(join(settings.media_storage.file_system_dir, client.evidence._id_card_secondary.path))

        # 2. Reject it by admin
        self.login('admin1@test.com', '123456')
        self.request(As.semitrusted_client, 'REJECT', self.url, params=[
            FormParameter('clientId', self.client1_id),
            FormParameter('error', 'some-message'),
        ])

        # 3. Resubmit it by client
        self.login('client1@test.com', '123456')
        self.request(As.semitrusted_client, 'SUBMIT', self.url, params=[
            FormParameter('firstName', 'test-first-name'),
            FormParameter('lastName', 'test-last-name'),
            FormParameter('gender', 'female'),
            FormParameter('birthday', datetime.now().isoformat()),
            FormParameter('cityId', self.city1_id),
            FormParameter('nationalCode', '349588398689'),
            FormParameter('address', 'test-test-test-test-no.12'),
            FormParameter('idCard', self.mockup_id_card, type_='file'),
            FormParameter('idCardSecondary', self.mockup_id_card_secondary, type_='file'),
        ])

        # 4. Accept it by admin
        self.login('admin1@test.com', '123456')
        self.request(As.semitrusted_client, 'ACCEPT', self.url, params=[
            FormParameter('clientId', self.client1_id),
        ])

        # Check the new role:
        self.login('client1@test.com', '123456')
        response, ___ = self.request(None, 'GET', '/apiv1/clients/me', doc=False)
        self.assertEqual(response['isEvidenceVerified'], True)

        # 5. Some bad situations
        self.login('admin1@test.com', '123456')
        self.request(As.semitrusted_client, 'REJECT', self.url, params=[
            FormParameter('clientId', self.client1_id),
            FormParameter('error', 'some-message'),
        ], expected_status=409)

        self.request(As.semitrusted_client, 'ACCEPT', self.url, params=[
            FormParameter('clientId', self.client1_id),
        ], expected_status=409)

        self.login('client1@test.com', '123456')
        self.request(As.semitrusted_client, 'SUBMIT', self.url, params=[
            FormParameter('firstName', 'test-first-name'),
            FormParameter('lastName', 'test-last-name'),
            FormParameter('gender', 'female'),
            FormParameter('birthday', datetime.now().isoformat()),
            FormParameter('cityId', self.city1_id),
            FormParameter('nationalCode', '349588398689'),
            FormParameter('address', 'test-test-test-test-no.12'),
            FormParameter('idCard', self.mockup_id_card, type_='file'),
            FormParameter('idCardSecondary', self.mockup_id_card_secondary, type_='file'),
        ], expected_status=403)

        # 6. Get evidence by admin
        self.login('admin1@test.com', '123456')
        response, ___ = self.request(As.admin, 'GET', f'/apiv1/clients/{self.client1_id}/evidences')
        self.assertIn('mobilePhone', response)
        self.assertIn('fixedPhone', response)
        self.assertIn('firstName', response)
        self.assertIn('lastName', response)
        self.assertIn('gender', response)
        self.assertIn('birthday', response)
        self.assertIn('cityId', response)
        self.assertIn('nationalCode', response)
        self.assertIn('address', response)
        self.assertIn('idCard', response)
        self.assertIn('idCardSecondary', response)

        # 7. Get evidence by client
        self.login('client1@test.com', '123456')
        response, ___ = self.request(As.client, 'GET', '/apiv1/clients/me/evidences')
        self.assertIn('mobilePhone', response)
        self.assertIn('fixedPhone', response)
        self.assertIn('firstName', response)
        self.assertIn('lastName', response)
        self.assertIn('gender', response)
        self.assertIn('birthday', response)
        self.assertIn('cityId', response)
        self.assertIn('nationalCode', response)
        self.assertIn('address', response)
        self.assertIn('idCard', response)
        self.assertIn('idCardSecondary', response)
