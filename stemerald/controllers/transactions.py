from typing import Union

from restfulpy.authorization import authorize
from restfulpy.orm import commit, DBSession

from nanohttp import json, HttpMethodNotAllowed, context, HttpConflict, HttpBadRequest, HttpNotFound, HttpFound, \
    settings, RestController
from restfulpy.controllers import ModelRestController
from restfulpy.logging_ import get_logger
from restfulpy.validation import validate_form, prevent_form

from stemerald.models import *
from stemerald.shaparak import create_shaparak_provider, ShaparakError
from stemerald.stexchange import StexchangeException, stexchange_http_exception_handler, stexchange_client

logger = get_logger('CLIENT')

MemberId = Union[int, str]


class BankCardController(ModelRestController):
    __model__ = BankCard

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'take', 'skip', 'pan', 'fiatSymbol', 'holder', 'isVerified', 'error'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'id']},
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = BankCard.query

        if context.identity.is_in_roles('client'):
            query = query.filter(BankCard.client_id == context.identity.id)

        return query

    @json
    @authorize('trusted_client')
    @validate_form(exact=['pan', 'fiatSymbol', 'holder'])
    @commit
    def add(self):
        bank_card = BankCard()
        bank_card.client_id = context.identity.id
        bank_card.fiat_symbol = context.form.get('fiatSymbol')
        bank_card.holder = context.form.get('holder')
        bank_card.pan = context.form.get('pan')
        DBSession.add(bank_card)
        return bank_card

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def accept(self, shetab_address_id: int):
        bank_card = BankCard.query.filter(BankCard.id == shetab_address_id).one_or_none()
        if bank_card is None:
            raise HttpNotFound()

        if bank_card.is_verified is True:
            raise HttpConflict('Already accepted')

        bank_card.error = None
        bank_card.is_verified = True

        return bank_card

    @json
    @authorize('admin')
    @validate_form(exact=['error'])
    @commit
    def reject(self, shetab_address_id: int):
        bank_card = BankCard.query.filter(BankCard.id == shetab_address_id).one_or_none()
        if bank_card is None:
            raise HttpNotFound()

        if bank_card.is_verified is True:
            raise HttpConflict('Already accepted')

        bank_card.error = context.form.get('error')

        return bank_card


class BankAccountController(ModelRestController):
    __model__ = BankAccount

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'take', 'skip', 'fiatSymbol', 'iban', 'bic', 'owner', 'isVerified', 'error'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'id']},
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = BankAccount.query

        if context.identity.is_in_roles('client'):
            query = query.filter(BankAccount.client_id == context.identity.id)

        return query

    @json
    @authorize('trusted_client')
    @validate_form(exact=['fiatSymbol', 'iban', 'owner'])
    @commit
    def add(self):
        sheba_address = BankAccount()
        sheba_address.client_id = context.identity.id
        sheba_address.fiat_symbol = context.form.get('fiatSymbol')
        sheba_address.iban = context.form.get('iban')
        sheba_address.bic = context.form.get('bic', None)
        sheba_address.owner = context.form.get('owner')
        DBSession.add(sheba_address)
        return sheba_address

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def accept(self, bank_account_id: int):
        sheba_address = BankAccount.query.filter(BankAccount.id == bank_account_id).one_or_none()
        if sheba_address is None:
            raise HttpNotFound()

        if sheba_address.is_verified is True:
            raise HttpConflict('Already accepted')

        sheba_address.error = None
        sheba_address.is_verified = True

        return sheba_address

    @json
    @authorize('admin')
    @validate_form(exact=['error'])
    @commit
    def reject(self, bank_account_id: int):
        sheba_address = BankAccount.query.filter(BankAccount.id == bank_account_id).one_or_none()
        if sheba_address is None:
            raise HttpNotFound()

        if sheba_address.is_verified is True:
            raise HttpConflict('Already accepted')

        sheba_address.error = context.form.get('error')

        return sheba_address


class BankingController(RestController):
    cards = BankCardController()
    accounts = BankAccountController()


class ShaparakInController(ModelRestController):
    __model__ = Cashin

    @json
    @authorize('trusted_client')
    @validate_form(exact=['amount', 'shetabAddressId'], types={'amount': int})
    @commit
    def create(self):
        # TODO: Add some salt to prevent man in the middle (Extra field to send on creation and check on verification,
        # Use description part)
        amount = context.form.get('amount')
        shetab_address_id = context.form.get('shetabAddressId')

        # Check deposit range
        Fiat.query.filter(Fiat.symbol == 'irr').one()
        payment_gateway = PaymentGateway.query.filter(PaymentGateway.name == 'shaparak').one()

        if (payment_gateway.cashin_max != 0 and amount > payment_gateway.cashin_max) or amount < payment_gateway.cashin_min:
            raise HttpBadRequest('Amount is not between valid cashin range.')

        # Check sheba
        target_shetab = BankCard.query \
            .filter(BankCard.id == shetab_address_id) \
            .filter(BankCard.client_id == context.identity.id) \
            .one_or_none()

        if target_shetab is None:
            raise HttpBadRequest('Shetab address not found.')

        if target_shetab.is_verified is False:
            raise HttpConflict('Shetab address is not verified.')

        # Check commission
        commission = payment_gateway.calculate_cashin_commission(amount)

        if commission >= amount:
            raise HttpConflict('Commission is more than the amount')

        shaparak_in = Cashin()
        shaparak_in.member_id = context.identity.id
        shaparak_in.fiat_symbol = 'irr'
        shaparak_in.amount = amount
        shaparak_in.commission = commission
        shaparak_in.banking_id = target_shetab
        shaparak_in.transaction_id = ''
        shaparak_in.payment_gateway_name = 'shaparak'

        DBSession.add(shaparak_in)
        DBSession.flush()

        shaparak_provider = create_shaparak_provider()
        try:
            shaparak_in.transaction_id = shaparak_provider.create_transaction(batch_id=shaparak_in.id, amount=amount)
        except ShaparakError:
            raise HttpBadRequest('Transaction could not be created')

        return shaparak_in

    @json
    @validate_form(filter_=['status', 'transId', 'factorNumber', 'description', 'cardNumber', 'traceNumber', 'message'])
    def post(self, inner_resource: str):
        # TODO: Warning: DDOS!
        # TODO: Fix these shits!
        # TODO: Add some salt to prevent man in the middle (Extra field to send on creation and check on verification,
        # Use description part)
        if inner_resource == 'pay-irs':
            status = context.form.get('status', None)
            trans_id = context.form.get('transId', None)
            factor_number = context.form.get('factorNumber', None)
            _ = context.form.get('description', None)
            card_number = context.form.get('cardNumber', None)
            trace_number = context.form.get('traceNumber', None)
            _ = context.form.get('message', None)

            result = 'successful'

            if status == 0:
                result = 'bad-status'
            elif factor_number is None:
                result = 'bad-factor-number'
            elif trace_number is None:
                result = 'bad-trace-number'
            else:
                target_transaction = Cashin.query \
                    .filter(Cashin.id == factor_number) \
                    .filter(Cashin.reference_id.is_(None)) \
                    .filter(Cashin.transaction_id == trans_id).one_or_none()

                if target_transaction is None:
                    result = 'bad-transaction'
                elif card_number[:6] != target_transaction.banking_id.pan.replace('-', '')[:6] or \
                        card_number[-4:] != target_transaction.banking_id.pan[-4:]:
                    result = 'bad-card'
                else:
                    shaparak_provider = create_shaparak_provider()
                    try:
                        amount, _, _ = shaparak_provider.verify_transaction(target_transaction.transaction_id)

                        # TODO: After verification, add a record with error to be possible to follow the problem later
                        if int(target_transaction.amount) != int(amount):
                            result = 'bad-amount'
                        else:
                            try:
                                # Set reference_id
                                target_transaction.reference_id = trace_number

                                stexchange_client.balance_update(
                                    user_id=target_transaction.member_id,
                                    asset="irr",  # FIXME
                                    # asset=target_transaction.payment_gateway.fiat_symbol,
                                    business="cashin",  # FIXME
                                    business_id=target_transaction.id,  # FIXME: Think about double payment
                                    change=target_transaction.amount - target_transaction.commission,
                                    detail=target_transaction.to_dict(),
                                )

                                # FIXME: Important !!!! : rollback the updated balance if
                                #  DBSession.commit() was not successful

                                DBSession.commit()
                            except StexchangeException as e:
                                if DBSession.is_active:
                                    DBSession.rollback()
                                    result = 'stexchange-error' + str(
                                        e  # FIXME: Delete the exception message for deployment
                                    )

                            except:
                                if DBSession.is_active:
                                    DBSession.rollback()
                                    result = 'internal-error'

                    except ShaparakError:
                        result = 'not-verified'

            raise HttpFound(f'{settings.shaparak.pay_ir.result_redirect_url}?result={result}')

        raise HttpMethodNotAllowed()


class ShaparakOutController(ModelRestController):
    __model__ = Cashout

    @json
    @authorize('trusted_client')
    @validate_form(exact=['amount', 'shebaAddressId'], types={'amount': int})
    @commit
    def schedule(self):
        amount = context.form.get('amount')
        sheba_address_address_id = context.form.get('shebaAddressId')

        # Check withdraw range
        irr = Fiat.query.filter(Fiat.code == 'irr').one_or_none()
        payment_gateway = PaymentGateway.query.filter(PaymentGateway.name == 'shaparak').one_or_none()

        if (irr.cashout_max != 0 and amount > irr.cashout_max) or amount < irr.cashout_min:
            raise HttpBadRequest('Amount is not between valid cashout range.')

        commission = irr.calculate_withdraw_commission(amount)

        # Check balance
        try:
            available_balance = stexchange_client.balance_query(context.identity.id, 'irr')['irr']['available']
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        # FIXME: Think about concurrency
        if available_balance < amount + commission:
            raise HttpBadRequest('Not enough balance')

        # Check sheba
        target_sheba = BankAccount.query \
            .filter(BankAccount.id == sheba_address_address_id) \
            .filter(BankAccount.client_id == context.identity.id) \
            .one_or_none()

        if target_sheba is None:
            raise HttpBadRequest('Sheba address not found.')

        if target_sheba.is_verified is False:
            raise HttpConflict('Sheba address is not verified.')

        shaparak_out = Cashout()
        shaparak_out.fiat_symbol = 'irr'
        shaparak_out.member_id = context.identity.id
        shaparak_out.amount = amount
        shaparak_out.commission = commission
        shaparak_out.sheba_address_id = sheba_address_address_id
        shaparak_out.payment_gateway_name = 'shaparak'  # FIXME
        DBSession.add(shaparak_out)

        # Set new balance
        try:
            # Cash back (without commission) FIXME: Really without commission?
            stexchange_client.balance_update(
                user_id=shaparak_out.client_id,
                asset='irr',  # FIXME
                business='withdraw',  # FIXME
                business_id=shaparak_out.id,
                change=f'-{amount + commission}',
                detail=shaparak_out.to_dict(),
            )
            # FIXME: Important !!!! : rollback the updated balance if
            #  DBSession.commit() was not successful
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return shaparak_out

    @json
    @authorize('admin')
    @validate_form(exact=['referenceId'])
    @commit
    def accept(self, shaparak_out_id: int):
        reference_id = context.form.get('referenceId')

        shaparak_out = Cashout.query.filter(Cashout.id == shaparak_out_id).one_or_none()

        if shaparak_out is None:
            raise HttpNotFound()

        if shaparak_out.reference_id is not None:
            raise HttpBadRequest('This transaction already accepted.')

        if shaparak_out.error is not None:
            raise HttpBadRequest('This transaction already has an error.')

        shaparak_out.reference_id = reference_id

        return shaparak_out

    @json
    @authorize('admin')
    @validate_form(exact=['error'])
    @commit
    def reject(self, shaparak_out_id: int):
        error = context.form.get('error')

        shaparak_out = Cashout.query.filter(Cashout.id == shaparak_out_id).one_or_none()

        if shaparak_out is None:
            raise HttpNotFound()

        if shaparak_out.reference_id is not None:
            raise HttpBadRequest('This transaction already accepted.')

        if shaparak_out.error is not None:
            raise HttpBadRequest('This transaction already has an error.')

        shaparak_out.error = error

        try:
            # Cash back (without commission) FIXME: Really without commission?
            stexchange_client.balance_update(
                user_id=shaparak_out.member_id,
                asset='irr',  # FIXME
                business='cashback',  # FIXME
                business_id=shaparak_out.id,
                change=shaparak_out.amount,
                detail=shaparak_out.to_dict(),
            )
            # FIXME: Important !!!! : rollback the updated balance if
            #  DBSession.commit() was not successful
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

        return shaparak_out


class TransactionController(ModelRestController):
    __model__ = BankingTransaction

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'type', 'take', 'skip', 'fiatSymbol'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'amount', 'commission']},
        types={'take': int, 'skip': int}
    )
    @BankingTransaction.expose
    def get(self):
        query = BankingTransaction.query

        if context.identity.is_in_roles('client'):
            query = query.filter(BankingTransaction.member_id == context.identity.id)

        return query


setattr(TransactionController, 'shaparak-ins', ShaparakInController())
setattr(TransactionController, 'shaparak-outs', ShaparakOutController())
