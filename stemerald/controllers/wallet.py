from nanohttp import RestController, json
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form


class DepositController(RestController):

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(whitelist=['coin', 'page'], type={'page': int})
    def list(self):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['coin'])
    def show(self, inner_resource: str):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['coin'])
    def renew(self, inner_resource: str):
        # TODO
        pass


class WithdrawController(RestController):

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(whitelist=['coin', 'page'], types={'page': int})
    def list(self):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['coin', 'amount', 'address'], types={'amount': int})
    def schedule(self):
        # TODO
        pass
