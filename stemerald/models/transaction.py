from restfulpy.orm import DeclarativeBase
from restfulpy.orm.field import Field, relationship
from restfulpy.orm.mixins import ModifiedMixin, OrderingMixin, FilteringMixin, PaginationMixin, TimestampMixin
from sqlalchemy import ForeignKey, BigInteger
from sqlalchemy.sql.sqltypes import Integer, Unicode, Boolean


class Transaction(ModifiedMixin, OrderingMixin, FilteringMixin, PaginationMixin, DeclarativeBase):
    __tablename__ = 'transaction'

    id = Field(Integer(), primary_key=True)
    client_id = Field(Integer(), ForeignKey('member.id'))  # FIXME: Change the name to `member_id`
    currency_code = Field(Unicode(10), ForeignKey('currency.code'))
    amount = Field(BigInteger())  # Value without commission
    commission = Field(BigInteger(), default=0)

    type = Field(Unicode(50))

    client = relationship('Client')

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }


class Deposit(Transaction):
    __tablename__ = 'deposit'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(Transaction.id), primary_key=True)

    transactionHash = Field(Unicode(260), nullable=True)


class Withdraw(Transaction):
    __tablename__ = 'withdraw'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer(), ForeignKey(Transaction.id), primary_key=True)

    destination_address = Field(Unicode(130))
    transaction_hash = Field(Unicode(260), nullable=True)

    error = Field(Unicode(), nullable=True)


class ShaparakIn(Transaction):
    __tablename__ = 'shaparak_in'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    def __init__(self):
        self.currency_code = 'irr'

    id = Field(Integer(), ForeignKey(Transaction.id), primary_key=True)

    # TODO: Add some salt to prevent man in the middle (Extra field to send on creation and check on verification)
    transaction_id = Field(Unicode())
    reference_id = Field(Unicode(260), nullable=True)
    shetab_address_id = Field(Integer(), ForeignKey('shetab_address.id'), protected=True)

    shetab_address = relationship('ShetabAddress')


class ShaparakOut(Transaction):
    __tablename__ = 'shaparak_out'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    def __init__(self):
        self.currency_code = 'irr'

    id = Field(Integer(), ForeignKey(Transaction.id), primary_key=True)

    sheba_address_id = Field(Integer(), ForeignKey('sheba_address.id'), protected=True)
    reference_id = Field(Unicode(260), nullable=True)
    error = Field(Unicode(), nullable=True)

    sheba_address = relationship('ShebaAddress')


class ShebaAddress(TimestampMixin, DeclarativeBase):
    __tablename__ = 'sheba_address'

    id = Field(Integer(), primary_key=True)
    address = Field(Unicode(40), pattern=r'^IR[0-9]{24}$')  # TODO: Should be unique if is_valid
    client_id = Field(Integer(), ForeignKey('client.id'))
    is_verified = Field(Boolean(), default=False)
    error = Field(Unicode(), nullable=True)

    client = relationship('Client', lazy='select', protected=True)


class ShetabAddress(TimestampMixin, DeclarativeBase):
    __tablename__ = 'shetab_address'

    id = Field(Integer(), primary_key=True)
    address = Field(Unicode(20), pattern=r'^([0-9]{4}-){3}[0-9]{4}$')  # TODO: Should be unique if is_valid
    client_id = Field(Integer(), ForeignKey('client.id'))
    is_verified = Field(Boolean(), default=False)
    error = Field(Unicode(), nullable=True)

    client = relationship('Client', lazy='select', protected=True)
