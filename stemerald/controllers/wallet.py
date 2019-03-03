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
    @validate_form(exact=['cryptocurrencySymbol'])
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


def withdraw_to_dict(withdraw):
    return {
        'id': withdraw['businessUid'],
        'user': withdraw['user'],
        'target': withdraw['target'],
        'netAmount': withdraw['netAmount'],
        'grossAmount': withdraw['grossAmount'],
        'estimatedNetworkFee': withdraw['estimatedNetworkFee'],
        'finalNetworkFee': withdraw['finalNetworkFee'],
        'type': withdraw['type'],
        'isManual': withdraw['isManual'],
        'status': withdraw['status'],
        'txid': withdraw['txid'],
        'issuedAt': withdraw['issuedAt'],
        'paidAt': withdraw['paidAt'],
        'txHash': withdraw['proof']['txHash'] if (withdraw['proof'] is not None) else None,
        'blockHeight': withdraw['proof']['blockHeight'] if (withdraw['proof'] is not None) else None,
        'blockHash': withdraw['proof']['blockHash'] if (withdraw['proof'] is not None) else None,
        'link': withdraw['proof']['link'] if (withdraw['proof'] is not None) else None,
        'confirmationsLeft': withdraw['proof']['confirmationsLeft'] if (
                withdraw['proof'] is not None) else None,
        'error': withdraw['proof']['error'] if (withdraw['proof'] is not None) else None,
    }


class WithdrawController(RestController):

    def __fetch_cryptocurrency(self):
        cryptocurrency = Cryptocurrency.query \
            .filter(Cryptocurrency.symbol == context.query_string.get("cryptocurrencySymbol")) \
            .one_or_none()

        if cryptocurrency is None:
            raise HttpBadRequest('Bad cryptocurrencySymbol')

        return cryptocurrency

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(whitelist=['cryptocurrencySymbol', 'page'], types={'page': int})
    def list(self):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencySymbol'])
    def get(self, withdraw_id: int):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            withdraw = stawallet_client.get_withdraw(wallet_id=cryptocurrency.wallet_id, withdraw_id=int(withdraw_id))
            if withdraw['user'] != context.identity.id:
                raise HttpNotFound()

            return withdraw_to_dict(withdraw)

        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencySymbol', 'amount', 'address'], types={'amount': int})
    def schedule(self):
        stawallet_client.schedule_withdraw()
        pass
