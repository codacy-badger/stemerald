from restfulpy.authorization import authorize
from restfulpy.orm import commit
from restfulpy.validation import validate_form

from stemerald.controllers.territories import TerritoryController
from stemerald.controllers.transactions import TransactionController, ShetabAddressController, ShebaAddressController
from nanohttp import Controller, json, HttpNotFound
from restfulpy.controllers import RootController, ModelRestController

import stemerald
from stemerald.models import Currency
from stemerald.controllers.securities import SecurityController
from stemerald.controllers.members import ClientController, AdminController, SessionController
from stemerald.controllers.tickets import TicketController
from stemerald.controllers.trading import TradeController, OrderController, MarketController


# noinspection PyUnresolvedReferences
class CurrencyController(ModelRestController):
    __model__ = Currency

    @json
    @validate_form(whitelist=['sort', 'id', 'code'], pattern={'sort': r'^(-)?(id|code)$'})
    @__model__.expose
    def get(self):
        return Currency.query

    @json
    @authorize('admin')
    @validate_form(
        whitelist=['withdrawMin', 'withdrawMax', 'withdrawStaticCommission', 'withdrawPermilleCommission',
                   'withdrawMaxCommission', 'depositMin', 'depositMax', 'depositStaticCommission',
                   'depositPermilleCommission', 'depositMaxCommission']
    )
    @__model__.expose
    @commit
    def edit(self, currency_code: str):
        currency = Currency.query.filter(Currency.code == currency_code).one_or_none()

        if currency is None:
            raise HttpNotFound()

        currency.update_from_request()
        return currency


class ApiV1(Controller):
    admins = AdminController()
    clients = ClientController()
    sessions = SessionController()

    securities = SecurityController()

    currencies = CurrencyController()
    markets = MarketController()

    orders = OrderController()
    trades = TradeController()

    transactions = TransactionController()

    tickets = TicketController()

    territories = TerritoryController()

    @json
    def version(self):
        return {
            'version': stemerald.__version__
        }


class Root(RootController):
    apiv1 = ApiV1()


setattr(ApiV1, 'shetab-addresses', ShetabAddressController())
setattr(ApiV1, 'sheba-addresses', ShebaAddressController())
