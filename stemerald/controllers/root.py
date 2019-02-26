from restfulpy.authorization import authorize
from restfulpy.orm import commit
from restfulpy.validation import validate_form

from stemerald.controllers.assets import AssetsController, BalancesController
from stemerald.controllers.territories import TerritoryController
from stemerald.controllers.transactions import TransactionController, BankCardController, BankAccountController
from nanohttp import Controller, json, HttpNotFound
from restfulpy.controllers import RootController, ModelRestController

import stemerald
from stemerald.controllers.wallet import DepositController, WithdrawController
from stemerald.models import Currency
from stemerald.controllers.security import LogController, IpWhitelistController
from stemerald.controllers.members import ClientController, AdminController, SessionController
from stemerald.controllers.tickets import TicketController
from stemerald.controllers.trading import TradeController, OrderController
from stemerald.controllers.market import MarketController


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
    def edit(self, currency_symbol: str):
        currency = Currency.query.filter(Currency.symbol == currency_symbol).one_or_none()

        if currency is None:
            raise HttpNotFound()

        currency.update_from_request()
        return currency


class ApiV2(Controller):
    # Users
    admins = AdminController()
    clients = ClientController()
    territories = TerritoryController()

    # Security
    sessions = SessionController()
    logs = LogController()
    ipwhitelists = IpWhitelistController()  # TODO

    # Support
    tickets = TicketController()

    # Base
    currencies = CurrencyController()  # TODO
    markets = MarketController()  # TODO

    # Trading
    orders = OrderController()  # TODO
    trades = TradeController()  # TODO

    # Assets
    assets = AssetsController()  # FIXME
    balances = BalancesController()  # FIXME

    # Transactions (fiat)
    transactions = TransactionController()  # TODO

    # Wallet (crypto)
    deposits = DepositController()  # TODO
    withdraws = WithdrawController()  # TODO

    @json
    def version(self):
        return {
            'version': stemerald.__version__
        }


class Root(RootController):
    apiv2 = ApiV2()


setattr(ApiV2, 'bank-cards', BankCardController())
setattr(ApiV2, 'bank-accounts', BankAccountController())
