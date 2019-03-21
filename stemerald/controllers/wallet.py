from nanohttp import RestController, json, context, HttpNotFound, HttpBadRequest, HttpInternalServerError
from restfulpy.authorization import authorize
from restfulpy.validation import validate_form

from stemerald.models import Cryptocurrency
from stemerald.stawallet import stawallet_client, StawalletException, StawalletHttpException
from stemerald.stexchange import StexchangeException, stexchange_client, BalanceNotEnoughException, \
    RepeatUpdateException


def deposit_to_dict(deposit):
    return {
        'id': deposit['id'],
        'user': deposit['invoice']['user'],
        'isConfirmed': deposit['confirmed'],
        'netAmount': deposit['netAmount'],
        'grossAmount': deposit['grossAmount'],
        'toAddress': deposit['invoice']['address'],
        'status': deposit['status'],
        'txHash': deposit['proof']['txHash'],
        'blockHeight': deposit['proof']['blockHeight'],
        'blockHash': deposit['proof']['blockHash'],
        'link': deposit['proof']['link'],
        'confirmationsLeft': deposit['proof']['confirmationsLeft'],
        'error': deposit['proof']['error'],
        'invoice': invoice_to_dict(deposit['invoice']),
        'extra': deposit['extra'],
    }


def invoice_to_dict(invoice):
    return {
        'id': invoice['id'],
        'user': invoice['user'],
        'extra': invoice['extra'],
        'creation': invoice['creation'],
        'expiration': invoice['expiration'],
        'address': invoice['address']['address'],
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
            if int(deposit['invoice']['user']) != context.identity.id:
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
            return invoice_to_dict(stawallet_client.get_invoices(
                wallet_id=cryptocurrency.wallet_id,
                user_id=context.identity.id
            )[0])

        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error")

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencySymbol'])
    def renew(self):
        cryptocurrency = self.__fetch_cryptocurrency()
        try:
            return invoice_to_dict(stawallet_client.post_invoice(
                wallet_id=cryptocurrency.wallet_id,
                user_id=context.identity.id,
                force=False
            )[-1])
        except StawalletHttpException as e:
            if e.http_status_code == 409:
                raise HttpBadRequest('Address has not been used', 'address-not-used')
            else:
                raise HttpInternalServerError("Wallet access error")
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
        amount = context.form.get("amount")
        if amount < 0:
            raise HttpBadRequest("Amount should be greater than zero")

        cryptocurrency = self.__fetch_cryptocurrency()
        estimated_network_fee = 0  # FIXME: Estimate it # TODO: Compare it with the user input
        withdrawal_fee = 0  # FIXME: Calculate it # TODO: Compare it with the user input
        cryptocurrency.calculate_withdraw_commission()

        # 1. First we inquire the possibility of doing transaction by our wallet provider (stawallet):
        try:
            withdraw_quote = stawallet_client.quote_withdraw(
                wallet_id=cryptocurrency.wallet.id,
                user_id=context.identity.id,
                business_uid=context.form.get('businessUid'),  # FIXME Do not get this from user directly
                destination_address=context.form.get('address'),
                amount=context.form.get('amount') - withdrawal_fee,
            )
        except StawalletException as e:
            raise HttpInternalServerError("Wallet access error", 'wallet-access-error')

        if not withdraw_quote['amountValid']:
            raise HttpBadRequest('Bad amount', 'bad-amount')

        if not withdraw_quote['addressValid']:
            raise HttpBadRequest('Bad address', 'bad-address')

        if not withdraw_quote['businessUidValid']:
            raise HttpBadRequest('Bad businessUid', 'bad-business-uid')

        if not withdraw_quote['businessUidDuplicated']:
            raise HttpBadRequest('BusinessUid already exists', 'already-submitted')

        # Now, it seem's we won't have any problem to with this request

        # 2. Lets reduce the user's balance (and also find out whether it's balance is enough or not):

        try:
            stexchange_client.balance_update(
                user_id=context.identity.id,
                asset=cryptocurrency.wallet_id,  # FIXME
                business='withdraw',
                business_id=context.form.get('businessUid'),  # FIXME Do not get this from user directly
                change=f'-{amount}',
                detail=withdraw_quote.to_dict(),  # FIXME
            )

        except BalanceNotEnoughException as e:
            raise HttpBadRequest('Balance not enough', 'balance-not-enough')

        except RepeatUpdateException as e:
            # This money has been already reduced from the users balance.
            # Why? Maybe because of a recent corrupted request
            # TODO: Handle it properly, might be a security risk
            # No need to raise an exception # TODO: Can be dangerous
            # TODO: Log
            pass

        except StexchangeException as e:
            raise HttpInternalServerError("Wallet access error. Contact administrator.", 'wallet-access-error')

        # 3: No let's really submit a withdraw request to our wallets

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

        except StexchangeException as e:
            # try:
            # stexchange_client.balance_update(
            #     user_id=shaparak_out.member_id,
            #     asset=shaparak_out.payment_gateway.fiat_symbol,  # FIXME
            #     business='cashback',  # FIXME
            #     business_id=shaparak_out.id,
            #     change=shaparak_out.amount,
            #     detail=shaparak_out.to_dict(),
            # )
            # FIXME: Important !!!! : rollback the updated balance if
            #  DBSession.commit() was not successful
            # except StexchangeException as e:
            #     raise stexchange_http_exception_handler(e)
            # TODO: Client should be retry in case of the below excepion to prevent client's money loss

            raise HttpInternalServerError("Wallet access error. Contact administrator.", 'wallet-access-error')

        # FIXME: This scenario has some blind spots and risks. Review it and warn the support team about possible errors
        #  and cases.
