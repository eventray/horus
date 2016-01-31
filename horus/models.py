# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
try:
    from urllib.parse import urlencode  # Python 3
except ImportError:
    from urllib import urlencode  # Python 2

from pyramid.compat import text_type as unicode
from pyramid.i18n import TranslationStringFactory
from pyramid.security import Allow
from datetime import datetime
from datetime import timedelta
from datetime import date
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import or_
from sqlalchemy import func

from hem.text import generate_random_string
from hem.text import pluralize
from hem.db import get_session

import cryptacular.bcrypt
import re
import hashlib
import sqlalchemy as sa

_ = TranslationStringFactory('horus')

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()


class BaseModel(object):
    """Base class which auto-generates tablename and surrogate
    primary key column.
    """
    _idAttribute = 'id'

    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    @property
    def id_value(self):
        return getattr(self, self._idAttribute)

    @declared_attr
    def __tablename__(cls):
        """Convert CamelCase class name to underscores_between_words
        table name.
        """
        name = cls.__name__.replace('Mixin', '')
        return (
            name[0].lower() +
            re.sub(r'([A-Z])', lambda m: "_" + m.group(0).lower(), name[1:])
        )

    @declared_attr
    def id(self):
        return sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    def __json__(self, request, convert_date=True):
        """Converts all the properties of the object into a dict
        for use in json.
        """
        props = {}
        blacklist = ['password', '_password']
        for key in self.__dict__:
            if key in blacklist:
                continue
            if not key.startswith('__') and not key.startswith('_sa_'):
                obj = getattr(self, key)
                if (isinstance(obj, datetime) or isinstance(obj, date)) \
                    and convert_date:
                    obj = obj.isoformat()
                props[key] = obj
        return props

    @classmethod
    def get_all(cls, request, page=None, limit=None):
        """Gets all records of the specific item with option page and limits.
        """
        session = get_session(request)

        query = session.query(cls)

        if limit:
            query = query.limit(limit)

        if page and limit:
            offset = (page - 1) * limit
            query = query.offset(offset)

        return query

    @classmethod
    def get_by_id(cls, request, id):
        """Gets an object by its primary key."""
        session = get_session(request)
        pk = getattr(cls, cls._idAttribute)
        return session.query(cls).filter(pk == id).first()


def three_days_from_now():
    return datetime.utcnow() + timedelta(days=3)


class ActivationMixin(BaseModel):
    """Handles activations/password reset items for users.

    The code should be a random hash that is valid only once.
    After the hash is used to access the site, it'll be removed.

    The "created by" is a system: new user registration, password reset,
    forgot password etc.
    """
    @declared_attr
    def code(self):
        """A random hash that is valid only once."""
        return sa.Column(sa.Unicode(30), nullable=False,
                         unique=True,
                         default=generate_random_string)

    @declared_attr
    def valid_until(self):
        """How long will the activation key last"""
        return sa.Column(sa.DateTime, nullable=False,
                         default=three_days_from_now)

    @declared_attr
    def created_by(self):
        """The system that generated the activation key"""
        return sa.Column(sa.Unicode(30), nullable=False,
                         default='web')

    @classmethod
    def get_by_code(cls, request, code):
        session = get_session(request)
        return session.query(cls).filter(cls.code == code).first()


def default_security_code():
    return generate_random_string(12)


class NoUsernameMixin(BaseModel):
    @declared_attr
    def email(self):
        """ E-mail for user """
        return sa.Column(sa.Unicode(100), nullable=False, unique=True)

    @declared_attr
    def status(self):
        """ Status of user """
        return sa.Column(sa.Integer())

    @declared_attr
    def security_code(self):
        """Can be used for API calls or password reset."""
        return sa.Column(
            sa.Unicode(256),
            nullable=True,
            unique=True,
            default=default_security_code
        )

    @declared_attr
    def last_login_date(self):
        """ Date of user's last login """
        return sa.Column(
            sa.TIMESTAMP(timezone=False)
            , default=sa.func.now()
            , server_default=sa.func.now()
            , nullable=False
        )

    @declared_attr
    def registered_date(self):
        """ Date of user's registration """
        return sa.Column(
            sa.TIMESTAMP(timezone=False)
            , default=sa.sql.func.now()
            , server_default=sa.func.now()
            , nullable=False
        )

    @declared_attr
    def salt(self):
        """ Password salt for user """
        return sa.Column(sa.Unicode(256), nullable=False)

    @declared_attr
    def _password(self):
        """ Password hash for user object """
        return sa.Column('password', sa.Unicode(256), nullable=False)

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._set_password(value)

    @declared_attr
    def activation_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('%s.%s' % (
            ActivationMixin.__tablename__,
            self._idAttribute)))

    @declared_attr
    def activation(self):
        return sa.orm.relationship('Activation', backref='user')

    @property
    def is_activated(self):
        return self.activation_id is None

    def _get_password(self):
        return self._password

    def _set_password(self, raw_password):
        self._password = self._hash_password(raw_password)

    def _hash_password(self, password):
        if not self.salt:
            self.salt = generate_random_string(24)

        return unicode(crypt.encode(password + self.salt))

    def gravatar_url(self, default='mm', size=80, cacheable=True):
        '''Returns a Gravatar image URL for this user.'''
        base = "http://www.gravatar.com/avatar/" if cacheable else \
            "https://secure.gravatar.com/avatar/"
        return base + \
            hashlib.md5(self.email.encode('utf8').lower()).hexdigest() + \
            "?" + urlencode({'d': default, 's': str(size)})

    @classmethod
    def generate_random_password(cls, chars=12):
        """ generates random string of fixed length"""
        return generate_random_string(chars)

    @classmethod
    def get_by_email(cls, request, email):
        session = get_session(request)
        return session.query(cls).filter(
            func.lower(cls.email) == email.lower()
        ).first()

    @classmethod
    def get_by_activation(cls, request, activation):
        session = get_session(request)
        return session.query(cls).filter(
            cls.activation_id == activation.id_value
        ).first()

    @classmethod
    def get_by_security_code(cls, request, security_code):
        session = get_session(request)
        return session.query(cls).filter(
            cls.security_code == security_code
        ).first()

    @classmethod
    def get_by_email_password(cls, request, handle, password):
        '''Only returns the user object if the password is correct.'''
        user = cls.get_by_email(request, handle)
        return cls.validate_user(user, password)
    get_user = get_by_email_password  # get_user is overridden in UsernameMixin

    @classmethod
    def validate_user(cls, user, password):
        '''Checks the password and returns the user object.'''
        if not user:
            return None
        if user.password is None:
            return False
        if crypt.check(user.password, password + user.salt):
            return user

    def __repr__(self):
        return '<User: %s>' % self.email

    @property
    def __acl__(self):
        return [
            (Allow, 'user:%s' % self.id_value, 'access_user')
        ]


class UsernameMixin(NoUsernameMixin):
    '''Additional username column for sites that need it.'''
    @declared_attr
    def username(self):
        return sa.Column(sa.Unicode(30), nullable=False, unique=True)

    @classmethod
    def get_by_username(cls, request, username):
        session = get_session(request)
        return session.query(cls).filter(
            func.lower(cls.username) == username.lower()
        ).first()

    @classmethod
    def get_by_username_or_email(cls, request, username, email):
        session = get_session(request)
        return session.query(cls).filter(
            or_(
                func.lower(cls.username) == username.lower(),
                cls.email == email
            )
        ).first()

    @classmethod
    def get_by_username_password(cls, request, username, password):
        '''Only returns the user object if the password is correct.'''
        user = cls.get_by_username(request, username)
        return cls.validate_user(user, password)

    @classmethod
    def get_user(cls, request, handle, password):
        '''We override this method because ``handle`` could be a
        username or an email.
        '''
        if '@' in handle:
            return cls.get_by_email_password(request, handle, password)
        else:
            return cls.get_by_username_password(request, handle, password)

UserMixin = UsernameMixin  # The "UserMixin" name is kept for backwards compat


class GroupMixin(BaseModel):
    """ base mixin for group object"""

    @declared_attr
    def name(self):
        return sa.Column(sa.Unicode(50), unique=True)

    @declared_attr
    def description(self):
        return sa.Column(sa.UnicodeText())

    @declared_attr
    def users(self):
        """Relationship for users belonging to this group"""
        return sa.orm.relationship(
            'User',
            secondary=UserGroupMixin.__tablename__,
            # order_by='%s.user.username' % UserMixin.__tablename__,
            passive_deletes=True,
            passive_updates=True,
            backref=pluralize(GroupMixin.__tablename__),
        )

#    @declared_attr
#    def permissions(self):
#        """ permissions assigned to this group"""
#        return sa.orm.relationship('GroupPermission'
#            , backref='groups'
#            , cascade="all, delete-orphan"
#            , passive_deletes=True
#            , passive_updates=True
#        )

    def __repr__(self):
        return '<Group: %s>' % self.name


class UserGroupMixin(BaseModel):
    @declared_attr
    def group_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('%s.%s' % (
                GroupMixin.__tablename__,
                self._idAttribute)
            )
        )

    @declared_attr
    def user_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey('user.' + self._idAttribute,
                          onupdate='CASCADE', ondelete='CASCADE'),
        )

    def __repr__(self):
        return '<UserGroup: %s, %s>' % (self.group_id, self.user_id,)

__all__ = [
    k for k, v in locals().items()
    if (
        isinstance(v, type) and issubclass(v, BaseModel)
    )
]
