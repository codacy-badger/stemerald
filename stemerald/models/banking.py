from restfulpy.orm import DeclarativeBase
from restfulpy.orm.field import Field, relationship
from restfulpy.orm.mixins import ModifiedMixin, OrderingMixin, FilteringMixin, PaginationMixin, TimestampMixin
from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.sql.sqltypes import Integer, Unicode, Boolean, Enum


class BankingTransaction(ModifiedMixin, OrderingMixin, FilteringMixin, PaginationMixin, DeclarativeBase):
    __tablename__ = 'banking_transaction'

    id = Field(Integer(), primary_key=True)
    fiat_symbol = Field(Unicode(10), ForeignKey('fiat.symbol'))
    member_id = Field(Integer(), ForeignKey('member.id'))  # FIXME: Change the name to `member_id`
    payment_gateway_name = Field(Unicode(30), ForeignKey('payment_gateway.name'))
    amount = Field(BigInteger())  # Value without commission
    commission = Field(BigInteger(), default=0)
    error = Field(Unicode(), nullable=True)
    reference_id = Field(Unicode(260), nullable=True)
    banking_id_id = Field(Integer(), ForeignKey('banking_id.id'), protected=True)

    payment_gateway = relationship('PaymentGateway')
    banking_id = relationship('BankingId')

    type = Field(Unicode(50))

    member = relationship('Member')

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }


class Cashin(BankingTransaction):
    __tablename__ = 'cashin'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(BankingTransaction.id), primary_key=True)

    # TODO: Add some salt to prevent man in the middle (Extra field to send on creation and check on verification)
    transaction_id = Field(Unicode())


class Cashout(BankingTransaction):
    __tablename__ = 'cashout'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(BankingTransaction.id), primary_key=True)


class BankingId(TimestampMixin, DeclarativeBase):
    __tablename__ = 'banking_id'

    id = Field(Integer(), primary_key=True)
    client_id = Field(Integer(), ForeignKey('client.id'))

    is_verified = Field(Boolean(), default=False)
    error = Field(Unicode(), nullable=True)

    client = relationship('Client', lazy='select', protected=True)

    type = Field(Enum('bank_account', 'bank_card', name='banking_id_type'))

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }


class BankAccount(BankingId):
    __tablename__ = 'bank_account'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(BankingId.id), primary_key=True)
    fiat_symbol = Field(Unicode(10), ForeignKey('fiat.symbol'))

    iban = Field(Unicode(50), pattern=r'^[A-Z]{2}[A-Z0-9]{4,10}[0-9]{5,40}$')  # TODO: Should be unique if is_valid
    owner = Field(Unicode(100))
    bic = Field(Unicode(20), pattern=r'^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$', nullable=True)


class BankCard(BankingId):
    __tablename__ = 'bank_card'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(BankingId.id), primary_key=True)
    fiat_symbol = Field(Unicode(10), ForeignKey('fiat.symbol'))

    pan = Field(Unicode(30), pattern=r'^([0-9]{4}-){3}[0-9]{4}$')  # TODO: Should be unique if is_valid
    holder = Field(Unicode(100))
    expiration = Field(Unicode(7), pattern=r'^[0-1]{1}/[0-9]{2,4}$', nullable=True)  # mm/yy or mm/yyyy


class PaymentGateway(DeclarativeBase):
    __tablename__ = 'payment_gateway'

    name = Field(Unicode(30), primary_key=True)
    fiat_symbol = Field(Unicode(10), ForeignKey('fiat.symbol'))

    cashin_min = Field(Integer(), default=0)
    cashin_max = Field(Integer(), default=0)
    cashin_static_commission = Field(Integer(), default=0)
    cashin_permille_commission = Field(Integer(), default=0)
    cashin_max_commission = Field(Integer(), default=0)

    cashout_min = Field(Integer(), default=0)
    cashout_max = Field(Integer(), default=0)
    cashout_static_commission = Field(Integer(), default=0)
    cashout_permille_commission = Field(Integer(), default=0)
    cashout_max_commission = Field(Integer(), default=0)

    fiat = relationship('Fiat')

    def calculate_cashin_commission(self, amount):
        commission = self.cashout_static_commission
        if self.cashout_permille_commission != 0:
            commission += int((amount * self.cashout_permille_commission) / 1000)
        return min(commission, self.cashout_max_commission) if self.cashout_max_commission != 0 else commission

    def calculate_cashout_commission(self, amount):
        commission = self.cashin_static_commission
        if self.cashin_permille_commission != 0:
            commission += int((amount * self.cashin_permille_commission) / 1000)
        return min(commission, self.cashin_max_commission) if self.cashin_max_commission != 0 else commission
