from os.path import join, exists

from nanohttp import settings
from restfulpy.testing import FormParameter

from staemerald.models import Client, Admin, TicketMessage, TicketDepartment
from staemerald.tests import STUFF_DIR
from staemerald.tests.helpers import WebTestCase, As


class ClientActivationTestCase(WebTestCase):
    url = '/apiv1/tickets'

    # noinspection PyArgumentList
    @classmethod
    def mockup(cls):
        cls.mockup_attachment1 = join(STUFF_DIR, 'test-image-1.jpg')
        cls.mockup_attachment2 = join(STUFF_DIR, 'test-image-2.png')

        admin1 = Admin()
        admin1.email = 'admin1@test.com'
        admin1.password = '123456'
        admin1.is_active = True
        cls.session.add(admin1)

        client1 = Client()
        client1.email = 'client1@test.com'
        client1.password = '123456'
        client1.is_active = True
        cls.session.add(client1)

        client2 = Client()
        client2.email = 'client2@test.com'
        client2.password = '123456'
        client2.is_active = True
        client2.is_email_verified = True
        cls.session.add(client2)

        department1 = TicketDepartment(title='department-1')
        department2 = TicketDepartment(title='department-2')
        cls.session.add(department1)
        cls.session.add(department2)

        cls.session.commit()

        cls.mockup_department1_id = department1.id
        cls.mockup_admin1_id = admin1.id
        cls.mockup_client1_id = client1.id
        cls.mockup_client2_id = client2.id

    def test_client_activation(self):
        self.login('client1@test.com', '123456')

        # 1. Get departments
        result, ___ = self.request(As.member, 'GET', f'{self.url}/departments')

        self.assertEqual(len(result), 2)
        self.assertIn('id', result[0])
        self.assertIn('title', result[0])

        # 2. Create ticket by client
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.client, 'CREATE', self.url, params=[
            FormParameter('departmentId', self.mockup_department1_id),
            FormParameter('title', 'test-title'),
            FormParameter('message', 'test-message'),
            FormParameter('attachment', self.mockup_attachment1, type_='file', optional=True),
        ])

        self.assertIn('id', result)
        self.assertIn('title', result)
        self.assertIn('isClosed', result)
        self.assertIn('closedAt', result)
        self.assertIn('departmentId', result)
        self.assertIn('department', result)
        self.assertIn('memberId', result)
        self.assertIn('firstMessage', result)
        self.assertIn('createdAt', result)
        self.assertIn('modifiedAt', result)

        self.assertIn('id', result['firstMessage'])
        self.assertIn('text', result['firstMessage'])
        self.assertIn('memberId', result['firstMessage'])
        self.assertIn('createdAt', result['firstMessage'])
        self.assertIn('modifiedAt', result['firstMessage'])
        self.assertIn('isAnswer', result['firstMessage'])
        self.assertIn('attachment', result['firstMessage'])

        self.assertFalse(result['firstMessage']['isAnswer'])
        self.assertIsNotNone(result['firstMessage']['id'])
        first_message_id = result['firstMessage']['id']

        ticket_message = self.session.query(TicketMessage) \
            .filter(TicketMessage.id == result['firstMessage']['id']) \
            .one_or_none()
        assert exists(join(settings.media_storage.file_system_dir, ticket_message._attachment.path))

        ticket_id = result['id']

        # by admin
        self.login('admin1@test.com', '123456')
        self.request(As.admin, 'CREATE', self.url, params=[
            FormParameter('departmentId', self.mockup_department1_id),
            FormParameter('title', 'test-2-title'),
            FormParameter('message', 'test-2-message'),
            FormParameter('attachment', self.mockup_attachment1, type_='file', optional=True),
        ], expected_status=400)

        result, ___ = self.request(As.admin, 'CREATE', self.url, params=[
            FormParameter('departmentId', self.mockup_department1_id),
            FormParameter('title', 'test-2-title'),
            FormParameter('message', 'test-2-message'),
            FormParameter('attachment', self.mockup_attachment1, type_='file', optional=True),
            FormParameter('clientId', self.mockup_client2_id, type_=int),
        ])

        self.assertEqual(result['memberId'], self.mockup_client2_id)

        # 3. Append a ticket (answer)
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.member, 'APPEND', f'{self.url}/{ticket_id}', params=[
            FormParameter('message', 'test-message-answer'),
            FormParameter('attachment', self.mockup_attachment2, type_='file', optional=True),
        ])

        self.assertIn('id', result)
        self.assertIn('text', result)
        self.assertIn('memberId', result)
        self.assertIn('createdAt', result)
        self.assertIn('modifiedAt', result)
        self.assertIn('isAnswer', result)
        self.assertIn('attachment', result)
        self.assertTrue(result['isAnswer'])

        # 4. Append a ticket (message)
        self.login('client1@test.com', '123456')
        self.request(As.member, 'APPEND', f'{self.url}/{ticket_id}', params=[
            FormParameter('message', 'test-message-2'),
        ])
        self.request(As.member, 'APPEND', f'{self.url}/{ticket_id}', params=[
            FormParameter('message', 'test-message-3'),
        ])

        # 5. Append a ticket that not mine (client) -> not permitted
        self.login('client2@test.com', '123456')
        self.request(As.member, 'APPEND', f'{self.url}/{ticket_id}', params=[
            FormParameter('message', 'test-message-4'),
        ], expected_status=404)

        # 7. Close a ticket
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.member, 'CLOSE', f'{self.url}/{ticket_id}')

        self.assertTrue(result['isClosed'])

        # 8. Reopen a ticket by appending
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.member, 'APPEND', f'{self.url}/{ticket_id}', params=[
            FormParameter('message', 'test-message-5'),
        ])

        # 9. Get ticket list
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.client, 'GET', self.url)

        self.assertEqual(len(result), 1)
        self.assertFalse(result[0]['isClosed'])
        self.assertEqual(result[0]['firstMessage']['id'], first_message_id)

        # by admin
        self.login('admin1@test.com', '123456')
        result, ___ = self.request(As.admin, 'GET', self.url)

        self.assertEqual(len(result), 2)

        # 10. Get ticket by id
        self.login('client1@test.com', '123456')
        result, ___ = self.request(As.member, 'GET', f'{self.url}/{ticket_id}')

        self.assertFalse(result['isClosed'])
        self.assertEqual(result['firstMessage']['id'], first_message_id)

        # 11. Get ticket messages
        result, ___ = self.request(As.member, 'GET', f'{self.url}/{ticket_id}/messages')

        self.assertEqual(len(result), 5)
        self.assertIn('id', result[0])
        self.assertIn('text', result[0])
