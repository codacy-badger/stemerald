from nanohttp import json, context, RestController, HttpNotFound, HttpConflict
from restfulpy.authorization import authorize
from restfulpy.controllers import ModelRestController
from restfulpy.orm import commit, DBSession
from restfulpy.validation import validate_form, prevent_form

from stemerald.models import BankCard, BankAccount


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

