import hashlib
import uuid
import os
from _ast import BoolOp
from datetime import datetime

from nanohttp import context
from nanohttp.exceptions import HttpBadRequest, HttpUnauthorized, HttpNotFound
from restfulpy.orm import DeclarativeBase, Field, relationship, DBSession
from restfulpy.orm.mixins import ActivationMixin, ModifiedMixin, OrderingMixin, FilteringMixin
from restfulpy.principal import JwtPrincipal, JwtRefreshToken
from sqlalchemy import ForeignKey, CheckConstraint, Boolean
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import synonym
from sqlalchemy.sql.sqltypes import Integer, Unicode, Enum, DateTime, JSON
from sqlalchemy_media import Image, WandAnalyzer, ImageValidator, ImageProcessor

from stemerald.models import Currency, Fund


class Member(ModifiedMixin, ActivationMixin, OrderingMixin, FilteringMixin, DeclarativeBase):
    __tablename__ = 'member'

    id = Field(Integer, primary_key=True)
    _password = Field('password', Unicode(), index=True, json='password', protected=True, min_length=6)

    email = Field(Unicode(), unique=True, index=True, pattern=r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)')

    type = Field(Unicode(50))

    @classmethod
    def _hash_password(cls, password):
        salt = hashlib.sha256()
        salt.update(os.urandom(60))
        salt = salt.hexdigest()

        hashed_pass = hashlib.sha256()
        # Make sure password is a str because we cannot hash unicode objects
        hashed_pass.update((password + salt).encode('utf-8'))
        hashed_pass = hashed_pass.hexdigest()

        password = salt + hashed_pass
        return password

    def _set_password(self, password):
        """Hash ``password`` on the fly and store its hashed version."""
        min_length = self.__class__.password.info['min_length']
        if len(password) < min_length:
            raise HttpBadRequest('Please enter at least %d characters for password field.' % min_length)
        self._password = self._hash_password(password)

    def _get_password(self):
        """Return the hashed version of the password."""
        return self._password

    password = synonym('_password', descriptor=property(_get_password, _set_password), info=dict(protected=True))

    def validate_password(self, password):
        """
        Check the password against existing credentials.

        :param password: the password that was provided by the user to
            try and authenticate. This is the clear text version that we will
            need to match against the hashed one in the database.
        :type password: unicode object.
        :return: Whether the password is valid.
        :rtype: bool

        """
        hashed_pass = hashlib.sha256()
        hashed_pass.update((password + self.password[:64]).encode('utf-8'))
        return self.password[64:] == hashed_pass.hexdigest()

    def create_jwt_principal(self, session_id=None):
        # FIXME: IMPORTANT Include user password as salt in signature

        if session_id is None:
            session_id = str(uuid.uuid4())

        return JwtPrincipal(dict(
            id=self.id,
            roles=self.roles,
            email=self.email,
            sessionId=session_id
        ))

    @classmethod
    def current(cls):
        if context.identity is None:
            raise HttpUnauthorized()

        return cls.query.filter(cls.email == context.identity.email).one()

    def change_password(self, current_password, new_password):
        if not self.validate_password(current_password):
            raise HttpBadRequest()

        self.password = new_password

    def create_refresh_principal(self):
        return JwtRefreshToken(dict(
            id=self.id
        ))

    @property
    def sessions(self):
        return context.application.__authenticator__.get_member_sessions_info(self.id)

    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
        'polymorphic_on': type
    }


class Admin(Member):
    __tablename__ = 'admin'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    id = Field(Integer, ForeignKey(Member.id), primary_key=True)

    @property
    def roles(self):
        return ['admin']


class Client(Member):
    __tablename__ = 'client'
    __mapper_args__ = {
        'polymorphic_identity': __tablename__,
    }

    # noinspection PyArgumentList
    def __init__(self, session=None):
        # TODO: Move them somewhere better
        self.evidence = ClientEvidence()

        # FIXME: Should not use DBSession always
        for currency in (session or DBSession).query(Currency).all():
            self.funds.append(Fund(client=self, currency=currency))

    id = Field(Integer, ForeignKey(Member.id), primary_key=True)

    has_second_factor = Field(Boolean(), default=False)

    invitation_code = Field(Unicode(), ForeignKey('invitation.code'), nullable=True)

    email_verified_at = Field(DateTime(), nullable=True, protected=True)
    evidence_verified_at = Field(DateTime(), nullable=True, protected=True)

    # FIXME: is `select` the best choice?
    evidence = relationship('ClientEvidence', lazy='select', uselist=False, protected=True)
    funds = relationship('Fund', lazy='select', protected=True)

    @hybrid_property
    def is_email_verified(self):
        return self.email_verified_at is not None

    @is_email_verified.setter
    def is_email_verified(self, value):
        self.email_verified_at = datetime.now() if value else None

    @is_email_verified.expression
    def is_email_verified(self):
        # noinspection PyUnresolvedReferences
        return self.email_verified_at.isnot(None)

    @hybrid_property
    def is_evidence_verified(self):
        return self.evidence_verified_at is not None

    @is_evidence_verified.setter
    def is_evidence_verified(self, value):
        self.evidence_verified_at = datetime.now() if value else None

    @is_evidence_verified.expression
    def is_evidence_verified(self):
        # noinspection PyUnresolvedReferences
        return self.evidence_verified_at.isnot(None)

    @classmethod
    def import_value(cls, column, v):
        if column.key == cls.is_email_verified.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        if column.key == cls.is_evidence_verified.key and not isinstance(v, bool):
            return str(v).lower() == 'true'
        return super().import_value(column, v)

    @property
    def roles(self):
        roles = ['client']
        if self.is_evidence_verified:
            return roles + ['trusted_client']
        elif self.is_email_verified:
            return roles + ['semitrusted_client']
        else:
            return roles + ['distrusted_client']

    @classmethod
    def is_exists(cls, client_id):
        return cls.query.filter(cls.id == client_id).count() > 0


class ClientIdCard(Image):
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


class ClientEvidence(ModifiedMixin, DeclarativeBase):
    __tablename__ = 'client_evidence'

    client_id = Field(Integer(), ForeignKey('member.id'), primary_key=True)

    first_name = Field(Unicode(50), nullable=True)
    last_name = Field(Unicode(50), nullable=True)

    mobile_phone = Field(Unicode(50), min_length=10, pattern=r'^\+[1-9]{1}[0-9]{3,14}$', watermark='Mobile Phone',
                         example='+989876543210', nullable=True, unique=True)

    fixed_phone = Field(Unicode(50), min_length=10, pattern=r'^\+[1-9]{1}[0-9]{3,14}$', watermark='Fixed Phone',
                        example='+982167653945', nullable=True, unique=True)

    gender = Field(Enum('male', 'female', name='gender'), nullable=True)
    birthday = Field(DateTime(), nullable=True)

    city_id = Field(Integer, ForeignKey('city.id'), nullable=True)
    city = relationship('City', uselist=False)
    national_code = Field(Unicode(50), nullable=True)

    address = Field(Unicode(), nullable=True)

    _id_card = Field(ClientIdCard.as_mutable(JSON), nullable=True, protected=True)  # Attachment
    _id_card_secondary = Field(ClientIdCard.as_mutable(JSON), nullable=True, protected=True)  # Attachment

    error = Field(Unicode(), nullable=True)

    @property
    def id_card(self):
        return self._id_card.locate() if self._id_card else None

    @id_card.setter
    def id_card(self, value):
        if value is not None:
            self._id_card = ClientIdCard.create_from(value)
        else:
            self._id_card = None

    @property
    def id_card_secondary(self):
        return self._id_card_secondary.locate() if self._id_card_secondary else None

    @id_card_secondary.setter
    def id_card_secondary(self, value):
        if value is not None:
            self._id_card_secondary = ClientIdCard.create_from(value)
        else:
            self._id_card_secondary = None

    def to_dict(self):
        result = super().to_dict()
        result['idCard'] = self.id_card
        result['idCardSecondary'] = self.id_card_secondary
        return result


class Invitation(ActivationMixin, DeclarativeBase):
    __tablename__ = 'invitation'

    code = Field(Unicode(), primary_key=True)

    total_sits = Field(Integer())
    filled_sits = Field(Integer(), default=0)

    __table_args__ = (
        CheckConstraint('total_sits >= filled_sits', name='cc_invitation_total_sits_grater_that_filled'),
    )

    @property
    def unfilled_sits(self):
        return self.total_sits - self.filled_sits

    @classmethod
    def ensure_code(cls, code):
        invitation = Invitation.query.filter(Invitation.code == code).with_for_update().one_or_none()

        if invitation is None:
            raise HttpNotFound()

        return invitation
