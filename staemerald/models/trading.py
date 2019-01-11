from restfulpy.orm import DeclarativeBase
from restfulpy.orm.field import Field, relationship
from restfulpy.orm.mixins import FilteringMixin, OrderingMixin
from sqlalchemy import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, Unicode, BigInteger


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

    id = Field(Integer(), primary_key=True)

    base_currency_code = Field(Unicode(), ForeignKey('currency.code'), protected=True)
    quote_currency_code = Field(Unicode(), ForeignKey('currency.code'), protected=True)

    base_currency = relationship('Currency', foreign_keys=[base_currency_code])
    quote_currency = relationship('Currency', foreign_keys=[quote_currency_code])

    buy_amount_min = Field(BigInteger(), default=0)
    buy_amount_max = Field(BigInteger(), default=0)
    buy_static_commission = Field(BigInteger(), default=0)
    buy_permille_commission = Field(Integer(), default=0)
    buy_max_commission = Field(BigInteger(), default=0)

    sell_amount_min = Field(BigInteger(), default=0)
    sell_amount_max = Field(BigInteger(), default=0)
    sell_static_commission = Field(BigInteger(), default=0)
    sell_permille_commission = Field(Integer(), default=0)
    sell_max_commission = Field(BigInteger(), default=0)

    divide_by_ten = Field(Integer(), default=0)
    price_latest = Field(BigInteger(), default=0)
    price_24 = Field(BigInteger(), default=0)
    price_lowest_24 = Field(BigInteger(), default=0)
    price_highest_24 = Field(BigInteger(), default=0)
    cap_total = Field(BigInteger(), default=0)
    cap_24 = Field(BigInteger(), default=0)
    cap_quote_total = Field(BigInteger(), default=0)
    cap_quote_24 = Field(BigInteger(), default=0)

    @property
    def divide_by(self):
        return 10 ** self.divide_by_ten
