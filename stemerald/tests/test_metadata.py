# Does it have any security issue? (about `Anonymouse access` & `field`)
from stemerald.tests.helpers import WebTestCase, As


class MetadataTestCase(WebTestCase):
    def test_metadata_client(self):
        self.request(As.anonymous, 'METADATA', '/apiv1/clients')
        self.request(As.anonymous, 'METADATA', '/apiv1/clients/evidences')
        self.request(As.anonymous, 'METADATA', '/apiv1/clients/funds')

        self.request(As.anonymous, 'METADATA', '/apiv1/shetab-addresses')
        self.request(As.anonymous, 'METADATA', '/apiv1/sheba-addresses')

        self.request(As.anonymous, 'METADATA', '/apiv1/tickets')
        self.request(As.anonymous, 'METADATA', '/apiv1/tickets/messages')
        self.request(As.anonymous, 'METADATA', '/apiv1/tickets/departments')

        self.request(As.anonymous, 'METADATA', '/apiv1/securities/logs')
        self.request(As.anonymous, 'METADATA', '/apiv1/securities/ipwhitelists')

        self.request(As.anonymous, 'METADATA', '/apiv1/territories/countries')
        self.request(As.anonymous, 'METADATA', '/apiv1/territories/states')
        self.request(As.anonymous, 'METADATA', '/apiv1/territories/cities')

        self.request(As.anonymous, 'METADATA', '/apiv1/currencies')
        # self.request(As.anonymous, 'METADATA', '/apiv1/markets')

        # self.request(As.anonymous, 'METADATA', '/apiv1/transactions')
        # self.request(As.anonymous, 'METADATA', '/apiv1/transactions/deposits')
        # self.request(As.anonymous, 'METADATA', '/apiv1/transactions/withdraws')
        # self.request(As.anonymous, 'METADATA', '/apiv1/transactions/shaparak-ins')
        # self.request(As.anonymous, 'METADATA', '/apiv1/transactions/shaparak-outs')
