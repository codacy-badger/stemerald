from datetime import datetime

from restfulpy.orm import DeclarativeBase, DBSession, ModifiedMixin, PaginationMixin
from restfulpy.orm.field import Field, relationship
from sqlalchemy import ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.sql.sqltypes import Integer, Boolean, Unicode, DateTime, JSON
from sqlalchemy_media import Image, WandAnalyzer, ImageValidator, ImageProcessor


class TicketDepartment(DeclarativeBase):
    __tablename__ = 'ticket_department'

    id = Field(Integer(), primary_key=True)
    title = Field(Unicode(50))


# TODO: Fix the Ticket and it's messages structure
class Ticket(ModifiedMixin, PaginationMixin, DeclarativeBase):
    __tablename__ = 'ticket'

    id = Field(Integer(), primary_key=True)

    title = Field(Unicode())
    member_id = Field(Integer(), ForeignKey('member.id'))
    department_id = Field(Integer(), ForeignKey('ticket_department.id'))

    closed_at = Field(DateTime(), nullable=True)

    department = relationship('TicketDepartment', uselist=False)

    @hybrid_property
    def is_closed(self):
        return self.closed_at is not None

    @is_closed.setter
    def is_closed(self, value):
        self.closed_at = datetime.now() if value else None

    @is_closed.expression
    def is_closed(self):
        # noinspection PyUnresolvedReferences
        return self.closed_at.isnot(None)

    @classmethod
    def import_value(cls, column, v):
        # noinspection PyUnresolvedReferences
        if column.key == cls.is_closed.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        # noinspection PyUnresolvedReferences
        return super().import_value(column, v)

    def to_dict(self):
        result = super().to_dict()
        first_message = DBSession.query(TicketMessage) \
            .filter(TicketMessage.ticket_id == self.id) \
            .order_by(TicketMessage.created_at) \
            .first()
        result['firstMessage'] = first_message.to_dict() if (first_message is not None) else None
        return result


class TicketAttachment(Image):
    __pre_processors__ = [
        WandAnalyzer(),
        ImageValidator(
            minimum=(200, 200),
            maximum=(1000, 1000),
            min_aspect_ratio=0.1,
            max_aspect_ratio=100,
            content_types=['image/jpeg', 'image/png']
        ),
        ImageProcessor(
            fmt='jpeg',
            width=200
        )
    ]


class TicketMessage(ModifiedMixin, PaginationMixin, DeclarativeBase):
    __tablename__ = 'ticket_message'

    id = Field(Integer(), primary_key=True)
    ticket_id = Field(Integer(), ForeignKey(Ticket.id))
    member_id = Field(Integer(), ForeignKey('member.id'))
    text = Field(Unicode())

    is_answer = Field(Boolean(), default=False)

    _attachment = Field(TicketAttachment.as_mutable(JSON), nullable=True, protected=True)

    ticket = relationship(Ticket, lazy='select', uselist=False, protected=True)

    @property
    def attachment(self):
        return self._attachment.locate() if self._attachment else None

    @attachment.setter
    def attachment(self, value):
        if value is not None:
            self._attachment = TicketAttachment.create_from(value)
        else:
            self._attachment = None

    def to_dict(self):
        result = super().to_dict()
        result['attachment'] = self.attachment
        return result
