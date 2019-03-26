from decimal import Decimal

from nanohttp import HttpBadRequest
from restfulpy.orm import DeclarativeBase, Field, FilteringMixin, OrderingMixin
from sqlalchemy import Integer, ForeignKey
from sqlalchemy.sql.sqltypes import Unicode, Enum, DECIMAL


class Currency(OrderingMixin, FilteringMixin, DeclarativeBase):
    """
    For exp. for 'BTC' we'll use:
        * smallest_unit_scale = -8
        * normalization_scale = 0

    For exp. for 'ETH' we'll use:
        * smallest_unit_scale = -18
        * normalization_scale = -1

    For exp. for 'IRR' we'll use:
        * smallest_unit_scale = 0
        * normalization_scale = -8

    """
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

    def input_to_normalized(self, number: str, strict=True):
        """
        :return:
        """
        if number is None:
            return None

        if strict and \
                (
                        (not (self.smallest_unit_scale >= 0 and len(number.split('.')) == 1))
                        and (len(number.split('.')) == 1 or len(number.split('.')[1]) != -self.smallest_unit_scale)
                ):
            raise HttpBadRequest(f'This number is in {self.symbol} unit and this currency should be presented with '
                                 f'the exact ${-self.smallest_unit_scale} digits behind the floating-point',
                                 'bad-number-format')

        number = Decimal(number)

        return number.scaleb(-self.normalization_scale)

    def smallest_unit_to_output(self, number):
        if number is None:
            return None
        return self.normalized_to_output(self.smallest_unit_to_normalized(number))

    def to_dict(self):
        result = super().to_dict()
        # TODO: Get the current user's wallet_tier_policy about this currency
        # result['tirePolicy'] = {}
        return result

    @classmethod
    def format_normalized_string(cls, number: Decimal):
        return '{:.8f}'.format(number)


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

    withdraw_min = Field(DECIMAL(18, 8), default=Decimal('0.00001000'))
    withdraw_max = Field(DECIMAL(18, 8), default=Decimal('100.00000000'))
    withdraw_static_commission = Field(DECIMAL(18, 8), default=Decimal('0.00000000'))
    withdraw_commission_rate = Field(Unicode(10), default="0.005")
    withdraw_max_commission = Field(DECIMAL(18, 8), default=Decimal('0.00000000'))

    deposit_min = Field(DECIMAL(18, 8), default=Decimal('0.00000001'))
    deposit_max = Field(DECIMAL(18, 8), default=Decimal('100.00000000'))
    deposit_static_commission = Field(DECIMAL(18, 8), default=Decimal('0.00000000'))
    deposit_commission_rate = Field(Unicode(10), default="0.000")
    deposit_max_commission = Field(DECIMAL(18, 8), default=Decimal('0.00000000'))

    def calculate_withdraw_commission(self, amount: Decimal):
        commission = self.withdraw_static_commission
        if self.withdraw_commission_rate != Decimal(0):
            commission += amount * Decimal(self.withdraw_commission_rate)
        return min(
            commission, self.withdraw_max_commission
        ) if self.withdraw_max_commission != Decimal(0) else commission

    def calculate_deposit_commission(self, amount: Decimal):
        commission = self.deposit_static_commission
        if self.deposit_commission_rate != Decimal(0):
            commission += amount * Decimal(self.deposit_commission_rate)
        return min(
            commission, self.deposit_max_commission
        ) if self.deposit_max_commission != Decimal(0) else commission


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
