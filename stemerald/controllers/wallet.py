from nanohttp import RestController, json, context, HttpNotFound, HttpBadRequest, HttpInternalServerError
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form

from stemerald.models import Cryptocurrency
from stemerald.stawallet import stawallet_client, StawalletException


def deposit_to_dict(deposit):
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
    @validate_form(exact=['cryptocurrencySymbol', 'page'], types={'page': int})
    def list(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            results = stawallet_client.get_deposits(
                wallet_id=cryptocurrency.wallet_id,
                user_id=context.identity.id,
                page=context.query_string.get("page")
            )
            return [deposit_to_dict(deposit) for deposit in results]

        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencySymbol'])
    def get(self, deposit_id: str):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            deposit = stawallet_client.get_deposit(wallet_id=cryptocurrency.wallet_id, deposit_id=int(deposit_id))
            if deposit['user'] != context.identity.id:
                raise HttpNotFound()

            return deposit_to_dict(deposit)

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
    @validate_form(exact=['cryptocurrencySymbol', 'page'], types={'page': int})
    def list(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            results = stawallet_client.get_withdraws(
                wallet_id=cryptocurrency.wallet_id,
                user_id=context.identity.id,
                page=context.query_string.get("page")
            )
            return [withdraw_to_dict(withdraw) for withdraw in results]

        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencySymbol'])
    def get(self, withdraw_id: str):
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
    @validate_form(exact=['cryptocurrencySymbol', 'amount', 'address', 'businessUid'], types={'amount': int})
    def schedule(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        estimated_network_fee = 0  # FIXME: Estimate it # TODO: Compare it with the user input
        withdrawal_fee = 0  # FIXME: Calculate it # TODO: Compare it with the user input
        try:
            withdraw = stawallet_client.schedule_withdraw(
                wallet_id=cryptocurrency.wallet.id,
                user_id=context.identity.id,
                business_uid=context.form.get('businessUid'),  # FIXME Do not get this from user directly
                is_manual=False,  # TODO Check the amount
                destination_address=context.form.get('address'),
                amount_to_be_withdrawed=context.form.get('amount'),
                withdrawal_fee=withdrawal_fee,
                estimated_network_fee=estimated_network_fee,
                is_decharge=False,
            )
            return withdraw_to_dict(withdraw)

        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")
