from restfulpy.orm import DeclarativeBase, Field
from restfulpy.orm.field import relationship
from restfulpy.orm.mixins import FilteringMixin
from sqlalchemy import Integer, ForeignKey, Unicode


class Country(DeclarativeBase):
    __tablename__ = 'country'

    id = Field(Integer(), primary_key=True)

    name = Field(Unicode(50))
    code = Field(Unicode(10), min_length=1, max_length=10, pattern=r'^[a-z]{1,10}$', unique=True)

    phone_prefix = Field(Integer())


class State(FilteringMixin, DeclarativeBase):
    __tablename__ = 'state'

    id = Field(Integer(), primary_key=True)
    country_id = Field(Integer(), ForeignKey('country.id'))

    name = Field(Unicode(50))

    country = relationship('Country', uselist=False)


class City(FilteringMixin, DeclarativeBase):
    __tablename__ = 'city'

    id = Field(Integer(), primary_key=True)
    state_id = Field(Integer(), ForeignKey('state.id'))

    name = Field(Unicode(50))

    state = relationship('State', uselist=False)
