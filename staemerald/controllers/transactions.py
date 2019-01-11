from typing import Union

from restfulpy.authorization import authorize
from restfulpy.orm import commit, DBSession
from sqlalchemy import desc

from nanohttp import json, HttpMethodNotAllowed, context, HttpConflict, HttpBadRequest, HttpNotFound, HttpFound, \
    settings
from restfulpy.controllers import ModelRestController
from restfulpy.logging_ import get_logger
from restfulpy.validation import validate_form, prevent_form

from staemerald.models import *
from staemerald.shaparak import create_shaparak_provider, ShaparakError

logger = get_logger('CLIENT')

MemberId = Union[int, str]


class ShetabAddressController(ModelRestController):
    __model__ = ShetabAddress

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'take', 'skip', 'address', 'isVerified', 'error'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'id']},
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = ShetabAddress.query

        if context.identity.is_in_roles('client'):
            query = query.filter(ShetabAddress.client_id == context.identity.id)

        return query

    @json
    @authorize('trusted_client')
    @validate_form(exact=['address'])
    @commit
    def add(self):
        shetab_address = ShetabAddress()
        shetab_address.client_id = context.identity.id
        shetab_address.address = context.form.get('address')
        DBSession.add(shetab_address)
        return shetab_address

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def accept(self, shetab_address_id: int):
        shetab_address = ShetabAddress.query.filter(ShetabAddress.id == shetab_address_id).one_or_none()
        if shetab_address is None:
            raise HttpNotFound()

        if shetab_address.is_verified is True:
            raise HttpConflict('Already accepted')

        shetab_address.error = None
        shetab_address.is_verified = True

        return shetab_address

    @json
    @authorize('admin')
    @validate_form(exact=['error'])
    @commit
    def reject(self, shetab_address_id: int):
        shetab_address = ShetabAddress.query.filter(ShetabAddress.id == shetab_address_id).one_or_none()
        if shetab_address is None:
            raise HttpNotFound()

        if shetab_address.is_verified is True:
            raise HttpConflict('Already accepted')

        shetab_address.error = context.form.get('error')

        return shetab_address


class ShebaAddressController(ModelRestController):
    __model__ = ShebaAddress

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'take', 'skip', 'address', 'isVerified', 'error'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'id']},
        types={'take': int, 'skip': int}
    )
    @__model__.expose
    def get(self):
        query = ShebaAddress.query

        if context.identity.is_in_roles('client'):
            query = query.filter(ShebaAddress.client_id == context.identity.id)

        return query

    @json
    @authorize('trusted_client')
    @validate_form(exact=['address'])
    @commit
    def add(self):
        sheba_address = ShebaAddress()
        sheba_address.client_id = context.identity.id
        sheba_address.address = context.form.get('address')
        DBSession.add(sheba_address)
        return sheba_address

    @json
    @authorize('admin')
    @prevent_form
    @commit
    def accept(self, sheba_address_id: int):
        sheba_address = ShebaAddress.query.filter(ShebaAddress.id == sheba_address_id).one_or_none()
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
    def reject(self, sheba_address_id: int):
        sheba_address = ShebaAddress.query.filter(ShebaAddress.id == sheba_address_id).one_or_none()
        if sheba_address is None:
            raise HttpNotFound()

        if sheba_address.is_verified is True:
            raise HttpConflict('Already accepted')

        sheba_address.error = context.form.get('error')

        return sheba_address


class DepositController(ModelRestController):
    __model__ = Deposit

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencyCode'])
    @commit
    def show(self, inner_resource: str):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencyCode'])
    @commit
    def renew(self, inner_resource: str):
        # TODO
        pass

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencyCode'])
    @commit
    def check(self):
        # TODO
        pass


class WithdrawController(ModelRestController):
    __model__ = Withdraw

    @json
    @authorize('semitrusted_client', 'trusted_client')
    @validate_form(exact=['cryptocurrencyCode', 'amount', 'address'], types={'amount': int})
    @commit
    def schedule(self):
        # TODO
        pass


class ShaparakInController(ModelRestController):
    __model__ = ShaparakIn

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
        irr = Fiat.query.filter(Fiat.code == 'irr').one_or_none()

        if (irr.deposit_max != 0 and amount > irr.deposit_max) or amount < irr.deposit_min:
            raise HttpBadRequest('Amount is not between valid deposit range.')

        # Check sheba
        target_shetab = ShetabAddress.query \
            .filter(ShetabAddress.id == shetab_address_id) \
            .filter(ShetabAddress.client_id == context.identity.id) \
            .one_or_none()

        if target_shetab is None:
            raise HttpBadRequest('Shetab address not found.')

        if target_shetab.is_verified is False:
            raise HttpConflict('Shetab address is not verified.')

        # Check commission
        irr = Fiat.query.filter(Fiat.code == 'irr').one_or_none()
        commission = irr.calculate_deposit_commission(amount)

        if commission >= amount:
            raise HttpConflict('Commission is more than the amount')

        shaparak_in = ShaparakIn()
        shaparak_in.client_id = context.identity.id
        shaparak_in.amount = amount
        shaparak_in.commission = commission
        shaparak_in.shetab_address_id = shetab_address_id
        shaparak_in.transaction_id = ''

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
                target_transaction = ShaparakIn.query \
                    .filter(ShaparakIn.id == factor_number) \
                    .filter(ShaparakIn.reference_id.is_(None)) \
                    .filter(ShaparakIn.transaction_id == trans_id).one_or_none()

                if target_transaction is None:
                    result = 'bad-transaction'
                elif card_number[:6] != target_transaction.shetab_address.address.replace('-', '')[:6] or \
                        card_number[-4:] != target_transaction.shetab_address.address[-4:]:
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

                                # Set new balance
                                fund_ = Fund.get_fund_with_lock(target_transaction.client_id, 'irr')
                                fund_.total_balance += target_transaction.amount - target_transaction.commission

                                DBSession.commit()
                            except:
                                if DBSession.is_active:
                                    DBSession.rollback()
                                    result = 'internal-error'

                    except ShaparakError:
                        result = 'not-verified'

            raise HttpFound(f'{settings.shaparak.pay_ir.result_redirect_url}?result={result}')

        raise HttpMethodNotAllowed()


class ShaparakOutController(ModelRestController):
    __model__ = ShaparakOut

    @json
    @authorize('trusted_client')
    @validate_form(exact=['amount', 'shebaAddressId'], types={'amount': int})
    @commit
    def schedule(self):
        amount = context.form.get('amount')
        sheba_address_address_id = context.form.get('shebaAddressId')

        # Check withdraw range
        irr = Fiat.query.filter(Fiat.code == 'irr').one_or_none()

        if (irr.withdraw_max != 0 and amount > irr.withdraw_max) or amount < irr.withdraw_min:
            raise HttpBadRequest('Amount is not between valid withdraw range.')

        commission = irr.calculate_withdraw_commission(amount)

        # Check balance
        fund_ = Fund.get_fund_with_lock(context.identity.id, irr.code)
        if fund_.available_balance < amount + commission:
            raise HttpBadRequest('Not enough balance')

        # Check sheba
        target_sheba = ShebaAddress.query \
            .filter(ShebaAddress.id == sheba_address_address_id) \
            .filter(ShebaAddress.client_id == context.identity.id) \
            .one_or_none()

        if target_sheba is None:
            raise HttpBadRequest('Sheba address not found.')

        if target_sheba.is_verified is False:
            raise HttpConflict('Sheba address is not verified.')

        shaparak_out = ShaparakOut()
        shaparak_out.client_id = context.identity.id
        shaparak_out.amount = amount
        shaparak_out.commission = commission
        shaparak_out.sheba_address_id = sheba_address_address_id
        DBSession.add(shaparak_out)

        # Set new balance
        fund_.total_balance -= amount + commission

        return shaparak_out

    @json
    @authorize('admin')
    @validate_form(exact=['referenceId'])
    @commit
    def accept(self, shaparak_out_id: int):
        reference_id = context.form.get('referenceId')

        shaparak_out = ShaparakOut.query.filter(ShaparakOut.id == shaparak_out_id).one_or_none()

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

        shaparak_out = ShaparakOut.query.filter(ShaparakOut.id == shaparak_out_id).one_or_none()

        if shaparak_out is None:
            raise HttpNotFound()

        if shaparak_out.reference_id is not None:
            raise HttpBadRequest('This transaction already accepted.')

        if shaparak_out.error is not None:
            raise HttpBadRequest('This transaction already has an error.')

        shaparak_out.error = error

        # Cash back (without commission) FIXME: Really without commission?
        fund_ = Fund.get_fund_with_lock(shaparak_out.client_id, 'irr')
        fund_.total_balance += shaparak_out.amount

        return shaparak_out


class TransactionController(ModelRestController):
    __model__ = Transaction

    deposits = DepositController()
    withdraws = WithdrawController()

    @json
    @authorize('admin', 'client')
    # TODO: This validate_form is toooooo important -> 'blacklist': ['clientId'] !!!
    @validate_form(
        whitelist=['clientId', 'type', 'take', 'skip', 'currencyCode'],
        client={'blacklist': ['clientId']},
        admin={'whitelist': ['sort', 'amount', 'commission']},
        types={'take': int, 'skip': int}
    )
    @Transaction.expose
    def get(self):
        query = Transaction.query

        if context.identity.is_in_roles('client'):
            query = query.filter(Transaction.client_id == context.identity.id)

        return query


setattr(TransactionController, 'shaparak-ins', ShaparakInController())
setattr(TransactionController, 'shaparak-outs', ShaparakOutController())
