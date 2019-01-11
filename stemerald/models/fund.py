from sqlalchemy import Integer, ForeignKey, CheckConstraint, Unicode, BigInteger
from sqlalchemy.ext.hybrid import hybrid_property

from restfulpy.orm import DeclarativeBase, ModifiedMixin, FilteringMixin, OrderingMixin, Field, relationship


class Fund(FilteringMixin, OrderingMixin, ModifiedMixin, DeclarativeBase):
    __tablename__ = 'fund'

    client_id = Field(Integer(), ForeignKey('client.id'), primary_key=True)
    currency_code = Field(Unicode(), ForeignKey('currency.code'), primary_key=True)

    total_balance = Field(BigInteger(), default=0)  # TODO: Constraint
    blocked_balance = Field(BigInteger(), default=0)  # TODO: Constraint

    client = relationship('Client', uselist=False, lazy='select', protected=True)
    currency = relationship('Currency', uselist=False)

    __table_args__ = (
        CheckConstraint('blocked_balance >= 0', name='cc_positive_balance'),
        CheckConstraint('total_balance >= blocked_balance', name='cc_total_grater_than_blocked'),
    )

    @hybrid_property
    def available_balance(self):
        return self.total_balance - self.blocked_balance

    @classmethod
    def get_fund(cls, client_id, currency_code=None):
        """
        :param client_id:
        :param currency_code:
        :return: The specific currency's fund if `currency_code` is not None, else all currency's balance.
        """
        query = cls.query.filter(cls.client_id == client_id)
        if currency_code is not None:
            return query.filter(cls.currency_code == currency_code).one()

        return query.all()

    @classmethod
    def get_fund_with_lock(cls, client_id, currency_code, session=None):
        return (session.query(cls) if session else cls.query) \
            .filter(cls.client_id == client_id) \
            .filter(cls.currency_code == currency_code) \
            .with_for_update() \
            .one()
