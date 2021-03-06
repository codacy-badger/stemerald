from decimal import Decimal

from nanohttp import HttpBadRequest, settings
from restfulpy.orm import DeclarativeBase
from restfulpy.orm.field import Field, relationship
from restfulpy.orm.mixins import FilteringMixin, OrderingMixin
from sqlalchemy import ForeignKey, DECIMAL
from sqlalchemy.sql.sqltypes import Integer, Unicode, BigInteger

from stemerald.stexchange import stexchange_client, StexchangeException, stexchange_http_exception_handler


class Market(OrderingMixin, FilteringMixin, DeclarativeBase):
    """
    Currency pairs are sometimes then written by concatenating the ISO currency codes (ISO 4217) of the base currency
    and the counter currency, separating them with a slash character. Often the slash character is omitted,
    alternatively the slash may be replaced by and etc. A widely traded currency pair is the relation of the euro
    against the US dollar, designated as EUR/USD. The quotation EUR/USD 1.2500 means that one euro is exchanged for
    1.2500 US dollars. Here, EUR is the base currency and USD is the quote currency(counter currency). This means that
    1 Euro can be exchangeable to 1.25 US Dollars.

    Reference: https://en.wikipedia.org/wiki/Currency_pair

    """
    __tablename__ = 'market'

    name = Field(Unicode(20), pattern=r'^[A-Z0-9]{1,10}_[A-Z0-9]{1,10}$', primary_key=True)  # e.g. btc_usd

    base_currency_symbol = Field(Unicode(), ForeignKey('currency.symbol'), protected=True)
    quote_currency_symbol = Field(Unicode(), ForeignKey('currency.symbol'), protected=True)

    base_currency = relationship('Currency', foreign_keys=[base_currency_symbol])
    quote_currency = relationship('Currency', foreign_keys=[quote_currency_symbol])

    buy_amount_min = Field(DECIMAL(18, 8), default=Decimal('0.00000100'))
    buy_amount_max = Field(DECIMAL(18, 8), default=Decimal('100.00000000'))

    sell_amount_min = Field(DECIMAL(18, 8), default=Decimal('0.00000100'))
    sell_amount_max = Field(DECIMAL(18, 8), default=Decimal('100.00000000'))

    taker_commission_rate = Field(Unicode(10), default='0.4')
    maker_commission_rate = Field(Unicode(10), default='0.1')

    # taker_static_commission = Field(BigInteger(), default=0)
    # taker_permille_commission = Field(Integer(), default=0)
    # taker_max_commission = Field(BigInteger(), default=0)

    # maker_static_commission = Field(BigInteger(), default=0)
    # maker_permille_commission = Field(Integer(), default=0)
    # maker_max_commission = Field(BigInteger(), default=0)

    def to_dict(self):
        result = super().to_dict()
        # TODO: Get the current user's wallet_tier_policy about this currency
        # result['tirePolicy'] = {}
        result['buyAmountMin'] = self.base_currency.normalized_to_output(self.buy_amount_min)
        result['buyAmountMax'] = self.base_currency.normalized_to_output(self.buy_amount_max)
        result['sellAmountMin'] = self.base_currency.normalized_to_output(self.sell_amount_min)
        result['sellAmountMax'] = self.base_currency.normalized_to_output(self.sell_amount_max)
        return result

    def get_last_price(self):
        try:
            return Decimal(stexchange_client.market_last(self.name))
        except StexchangeException as e:
            raise stexchange_http_exception_handler(e)

    def validate_ranges(self, type_, total_amount, price=None):

        # TODO: Review and rewrite the price threshold validator
        # threshold = Decimal(settings.trader.price_threshold_permille)
        # price_rate = Decimal(1000 * (price or self.get_last_price()) / self.get_last_price()) - Decimal(1000)

        if type_ == 'buy':
            # if price_rate > threshold:
            #     raise HttpBadRequest('Price not in valid range', 'price-not-in-range')

            if total_amount < self.buy_amount_min or \
                    (self.buy_amount_max != 0 and total_amount > self.buy_amount_max):
                raise HttpBadRequest('Amount not in range', 'amount-not-in-range')

        elif type_ == 'sell':
            # if price_rate < -threshold:
            #     raise HttpBadRequest('Price not in valid range', 'price-not-in-range')

            if total_amount < self.sell_amount_min or \
                    (self.sell_amount_max != 0 and total_amount > self.sell_amount_max):
                raise HttpBadRequest('Amount not in range', 'amount-not-in-range')
