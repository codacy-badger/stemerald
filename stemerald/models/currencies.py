from decimal import Decimal

from restfulpy.orm import DeclarativeBase, Field, FilteringMixin, OrderingMixin
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.sql.sqltypes import Unicode, Enum, DECIMAL

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

    def smallest_unit_to_normalized(self, number):
        """
        :return:
        """
        if number is None:
            return None
        return Decimal(number).scaleb(self.smallest_unit_scale + self.normalization_scale)

    def normalized_to_output(self, number: Decimal):
        """
        :return:
        """
        if number is None:
            return None
        if not isinstance(number, Decimal):
            number = Decimal(number)

        return ('{:.' + str(max(0, -self.smallest_unit_scale)) + 'f}') \
            .format(number.scaleb(- self.normalization_scale))

    def smallest_unit_to_output(self, number):
        if number is None:
            return None
        return self.normalized_to_output(self.smallest_unit_to_normalized(number))


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

    withdraw_min = Field(DECIMAL(18, 8), default=0)
    withdraw_max = Field(DECIMAL(18, 8), default=0)
    withdraw_static_commission = Field(DECIMAL(18, 8), default=0)
    withdraw_permille_commission = Field(DECIMAL(18, 8), default=0)
    withdraw_max_commission = Field(DECIMAL(18, 8), default=0)

    deposit_min = Field(DECIMAL(18, 8), default=0)
    deposit_max = Field(DECIMAL(18, 8), default=0)
    deposit_static_commission = Field(DECIMAL(18, 8), default=0)
    deposit_permille_commission = Field(DECIMAL(18, 8), default=0)
    deposit_max_commission = Field(DECIMAL(18, 8), default=0)

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

    def to_dict(self):
        result = super().to_dict()
        result['withdrawMin'] = self.normalized_to_output(self.normalized_to_output(self.id_card))
        result['withdrawMax'] = self.normalized_to_output(self.withdraw_max)
        result['withdrawFee'] = self.normalized_to_output(self.withdraw_static_commission)
        result['withdrawPermilleCommission'] = self.normalized_to_output(self.withdraw_permille_commission)
        result['withdrawax_commission'] = self.normalized_to_output(self.withdraw_max_commission)
        result['deposit_min'] = self.normalized_to_output(self.deposit_min)
        result['deposit_max'] = self.normalized_to_output(self.deposit_max)
        result['deposit_static_commission'] = self.normalized_to_output(self.deposit_static_commission)
        result['deposit_permille_commission'] = self.normalized_to_output(self.deposit_permille_commission)
        result['deposit_max_commission'] = self.vnormalized_to_output(self.deposit_max_commission)
        return result


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
