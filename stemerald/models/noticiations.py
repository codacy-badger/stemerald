from datetime import datetime

from restfulpy.orm import OrderingMixin, FilteringMixin, DeclarativeBase, Field, TimestampMixin, SoftDeleteMixin, \
    PaginationMixin
from sqlalchemy import DateTime, Integer, ForeignKey, Unicode, JSON
from sqlalchemy.ext.hybrid import hybrid_property


class Notification(SoftDeleteMixin, TimestampMixin, PaginationMixin, OrderingMixin, FilteringMixin, DeclarativeBase):
    """
    Note: This table is experimental!
    """

    __tablename__ = 'notification'

    id = Field(Integer(), primary_key=True)
    member_id = Field(Integer(), ForeignKey('member.id'))

    read_at = Field(DateTime(), nullable=True)

    title = Field(Unicode(100))
    description = Field(Unicode(500))
    thumbnail = Field(Unicode(500), nullable=True)

    link = Field(Unicode(), nullable=True)  # TODO
    """
    Optional. 
    
    Can be 'web url' or 'deep link'
    """

    template = Field(Unicode(256), nullable=True)  # TODO
    """
    Refer wherever you want
    e.g. abc.html
    """

    body = Field(JSON, nullable=True)  # TODO
    """
    Use it as however you want. For exp.:
    
    * {
    *     "firstName": "Jack",
    *     "lastName": "Daniel"
    * }
    """

    severity = Field(Integer, nullable=False, default=50)  # TODO
    """
    How much important is it (1 to 100)
    How much important is it (1 to 100)
    
    * 0 means 'flash' (one time show)
    * 100 (and more) means 'pinned'
    
    """

    topic = Field(Unicode(64), nullable=False)  # TODO
    """
    Optional. e.g.: security, ...
    """

    type = Field(Unicode(50), nullable=True)  # TODO
    """
    Use it whatever you want
    e.g. text, html, image, ...
    """

    target = Field(Unicode(50), nullable=True)  # TODO
    """
    'null' means anywhere
    e.g.: app, web, ... (Use it however you want)
    """

    @hybrid_property
    def is_read(self):
        return self.read_at is not None

    @is_read.setter
    def is_read(self, value):
        self.read_at = datetime.now() if value else None

    @is_read.expression
    def is_email_verified(self):
        # noinspection PyUnresolvedReferences
        return self.read_at.isnot(None)
