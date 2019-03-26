from restfulpy.orm import DeclarativeBase, Field, FilteringMixin, OrderingMixin
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.sql.sqltypes import Unicode, Enum

from stemerald.math import parse_lowest_unit


class Currency(OrderingMixin, FilteringMixin, DeclarativeBase):
    __tablename__ = 'currency'

    symbol = Field(Unicode(10), min_length=1, max_length=10, pattern=r'^[A-Z0-9]{1,10}$', primary_key=True)
    name = Field(Unicode(25), min_length=1, max_length=25)

    normalization_scale = Field(Integer(), default=0)
    smallest_unit_scale = Field(Integer(), default=0)

    type = Field(Enum('fiat', 'cryptocurrency', name='currency_type'))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }

    def normalize_from_smallest_unit_string(self, number):
        """
        :return:
        """
        return parse_lowest_unit(number, smallest_unit_scale, normalizing_ten_pow)


class Cryptocurrency(Currency):
    __tablename__ = 'cryptocurrency'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    symbol = Field(
        Unicode(10),
        ForeignKey(Currency.symbol),
        min_length=1,
        max_length=10,
        pattern=r'^[A-Z0-9]{1,10}$',
        primary_key=True
    )

    # A reference to an external cryptocurrency wallet
    wallet_id = Field(Unicode(32))
    wallet_latest_sync = Field(Integer(), default=0)

    withdraw_min = Field(Integer(), default=0)
    withdraw_max = Field(Integer(), default=0)
    withdraw_static_commission = Field(Integer(), default=0)
    withdraw_permille_commission = Field(Integer(), default=0)
    withdraw_max_commission = Field(Integer(), default=0)

    deposit_min = Field(Integer(), default=0)
    deposit_max = Field(Integer(), default=0)
    deposit_static_commission = Field(Integer(), default=0)
    deposit_permille_commission = Field(Integer(), default=0)
    deposit_max_commission = Field(Integer(), default=0)

    def calculate_withdraw_commission(self, amount):
        commission = self.withdraw_static_commission
        if self.withdraw_permille_commission != 0:
            commission += int((amount * self.withdraw_permille_commission) / 1000)
        return min(commission, self.withdraw_max_commission) if self.withdraw_max_commission != 0 else commission

    def calculate_deposit_commission(self, amount):
        commission = self.deposit_static_commission
        if self.deposit_permille_commission != 0:
            commission += int((amount * self.deposit_permille_commission) / 1000)
        return min(commission, self.deposit_max_commission) if self.deposit_max_commission != 0 else commission


class Fiat(Currency):
    __tablename__ = 'fiat'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    symbol = Field(
        Unicode(10), ForeignKey(Currency.symbol),
        min_length=1,
        max_length=10,
        pattern=r'^[A-Z0-9]{1,10}$',
        primary_key=True
    )
