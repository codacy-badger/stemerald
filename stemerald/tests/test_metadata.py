# Does it have any security issue? (about `Anonymouse access` & `field`)
from stemerald.tests.helpers import WebTestCase, As


class MetadataTestCase(WebTestCase):
    def test_metadata_client(self):
        self.request(As.anonymous, 'METADATA', '/apiv2/clients')
        self.request(As.anonymous, 'METADATA', '/apiv2/clients/evidences')
        self.request(As.anonymous, 'METADATA', '/apiv2/clients/funds')

        self.request(As.anonymous, 'METADATA', '/apiv2/shetab-addresses')
        self.request(As.anonymous, 'METADATA', '/apiv2/sheba-addresses')

        self.request(As.anonymous, 'METADATA', '/apiv2/tickets')
        self.request(As.anonymous, 'METADATA', '/apiv2/tickets/messages')
        self.request(As.anonymous, 'METADATA', '/apiv2/tickets/departments')

        self.request(As.anonymous, 'METADATA', '/apiv2/securities/logs')
        self.request(As.anonymous, 'METADATA', '/apiv2/securities/ipwhitelists')

        self.request(As.anonymous, 'METADATA', '/apiv2/territories/countries')
        self.request(As.anonymous, 'METADATA', '/apiv2/territories/states')
        self.request(As.anonymous, 'METADATA', '/apiv2/territories/cities')

        self.request(As.anonymous, 'METADATA', '/apiv2/currencies')
        # self.request(As.anonymous, 'METADATA', '/apiv2/markets')

        # self.request(As.anonymous, 'METADATA', '/apiv2/transactions')
        # self.request(As.anonymous, 'METADATA', '/apiv2/transactions/deposits')
        # self.request(As.anonymous, 'METADATA', '/apiv2/transactions/withdraws')
        # self.request(As.anonymous, 'METADATA', '/apiv2/transactions/shaparak-ins')
        # self.request(As.anonymous, 'METADATA', '/apiv2/transactions/shaparak-outs')
