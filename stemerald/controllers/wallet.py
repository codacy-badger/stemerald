from nanohttp import RestController, json, context, HttpNotFound, HttpBadRequest, HttpInternalServerError
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form

from stemerald.models import Cryptocurrency
from stemerald.stawallet import stawallet_client, StawalletException


class DepositController(RestController):

    def __fetch_cryptocurrency(self):
        cryptocurrency = Cryptocurrency.query \
            .filter(Cryptocurrency.symbol == context.query_string.get("cryptocurrencySymbol")) \
            .one_or_none()

        if cryptocurrency is None:
            raise HttpBadRequest('Bad cryptocurrencySymbol')

        return cryptocurrency

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(whitelist=['cryptocurrencySymbol', 'page'], requires=['cryptocurrencySymbol'], type={'page': int})
    def list(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            return [
                {

                }
                for item in stawallet_client.get_deposits(
                    wallet_id=cryptocurrency.wallet_id,
                    user_id=context.identity.id,
                    page=context.query_string.get('page', 0)
                )
            ]
        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['coin'])
    def show(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            invoice = stawallet_client.get_invoices(wallet_id=cryptocurrency.wallet_id, user_id=context.identity.id)[-1]
            
        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['coin'])
    def renew(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            return [
                {

                }
                for item in stawallet_client.get_invoices(
                    wallet_id=cryptocurrency.wallet_id,
                    user_id=context.identity.id,
                    page=context.query_string.get('page', 0)
                )
            ]
        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")


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
