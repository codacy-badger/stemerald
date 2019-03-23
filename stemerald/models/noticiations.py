from datetime import datetime

from firebase_admin import messaging
from restfulpy.logging_ import get_logger
from restfulpy.orm import OrderingMixin, FilteringMixin, Field, SoftDeleteMixin, \
    PaginationMixin
from restfulpy.taskqueue import Task
from sqlalchemy import DateTime, Integer, ForeignKey, Unicode, JSON
from sqlalchemy.ext.hybrid import hybrid_property

from stemerald.firebase import FirebaseClient
from stemerald.models import Member

logger = get_logger('NOTIFICATION')


class Notification(SoftDeleteMixin, PaginationMixin, OrderingMixin, FilteringMixin, Task):
    """
    Note: This table is experimental!
    """

    def do_(self, context):  # pragma: no cove
        from stemerald import stemerald

        app = FirebaseClient().instance

        # TODO: Retrieve notifications policy of the user
        # See documentation on defining a message payload.

        # TODO: Retrieve all registered tokens about all user's connected devices

        member = Member.query.filter(Member.id == self.member_id).one()
        sessions = stemerald.__authenticator__.get_member_sessions_info(member.id)
        firebase_tokens = [(s['firebaseToken'] if 'firebaseToken' in s else '') for s in sessions]
        firebase_tokens = list(set(filter(lambda x: (x is not None) and (len(x) > 0), firebase_tokens)))

        messages = [
            messaging.Message(
                notification=messaging.Notification(
                    title=self.title,
                    body=self.description,
                ),
                token=t,
            ) for t in firebase_tokens
        ]

        # Send a message to the device corresponding to the provided
        # registration token.
        logger.info(f'Sending notification to {self.member_id}\'s devices')
        for m in messages:
            response = messaging.send(m)
            # Response is a message ID string.
            logger.info(f'Successfully sent message: {response} to member_id: {self.member_id}')

    __tablename__ = 'notification'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__
    }

    id = Field(Integer, ForeignKey('task.id'), primary_key=True, json='id')
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

    topic = Field(Unicode(64), nullable=True)  # TODO
    """
    Optional. e.g.: security, ...
    """

    content_type = Field(Unicode(50), nullable=True, json='contentType')  # TODO
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
