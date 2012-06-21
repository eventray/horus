from pyramid.i18n               import TranslationStringFactory
from pyramid.security           import Allow
from datetime                   import datetime
from datetime                   import timedelta
from datetime                   import date
from sqlalchemy.ext.declarative import declared_attr
from horus.lib                  import generate_random_string

import cryptacular.bcrypt
import re
import urllib
import hashlib
import sqlalchemy as sa


_ = TranslationStringFactory('horus')

crypt = cryptacular.bcrypt.BCRYPTPasswordManager()

class BaseModel(object):
    """Base class which auto-generates tablename, and surrogate
    primary key column.
    """
    __table_args__ = {
        'sqlite_autoincrement': True,
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    @declared_attr
    def __tablename__(cls):
        """Convert CamelCase class name to underscores_between_words 
        table name."""
        name = cls.__name__
        return (
            name[0].lower() + 
            re.sub(r'([A-Z])', lambda m:"_" + m.group(0).lower(), name[1:])
        )

    # We use pk instead of id because id is a python builtin
    pk =  sa.Column(sa.Integer, autoincrement=True, primary_key=True)

    def __json__(self):
        """Converts all the properties of the object into a dict
        for use in json
        """
        props = {}

        for key in self.__dict__:
            if not key.startswith('__') and not key.startswith('_sa_'):
                obj = getattr(self, key)

                if isinstance(obj, datetime) or isinstance(obj, date):
                        props[key] = obj.isoformat()
                else:
                    props[key] = getattr(self, key)

        return props

class Activation(BaseModel):
    """
    Handle activations/password reset items for users

    The code should be a random hash that is valid only one time
    After that hash is used to access the site it'll be removed

    The created by is a system: new user registration, password reset, forgot
    password, etc.

    """
    code = sa.Column(sa.UnicodeText)
    valid_until = sa.Column(sa.DateTime)
    created_by = sa.Column('created_by', sa.UnicodeText)

    def __init__(self, created_system=None, valid_until=None):
        """ Create a new activation, valid_length is in days """
        self.code =  generate_random_string(12)
        self.created_by = created_system

        if valid_until:
            self.valid_until = valid_until
        else:
             self.valid_until = datetime.utcnow() + timedelta(days=3)

class UserMixin(BaseModel):
    user_name = sa.Column(sa.UnicodeText, unique=True)
    email = sa.Column(sa.UnicodeText, unique=True)

    @declared_attr
    def user_name(self):
        """ Unique user name """
        return sa.Column(sa.Unicode(30), unique=True)

    @declared_attr
    def email(self):
        """ E-mail for user """
        return sa.Column(sa.Unicode(100), nullable=False, unique=True)

    @declared_attr
    def status(self):
        """ Status of user """
        return sa.Column(sa.Integer(), nullable=False)

    @declared_attr
    def security_code(self):
        """ Security code user, can be used for API calls or password reset """
        return sa.Column(sa.Unicode(256))

    @declared_attr
    def last_login_date(self):
        """ Date of user's last login """
        return sa.Column(
            sa.TIMESTAMP(timezone=False)
            , default=sa.sql.func.now()
            , server_default=sa.func.now()
        )

    @declared_attr
    def registered_date(self):
        """ Date of user's registration """
        return sa.sa.Column(
            sa.TIMESTAMP(timezone=False)
            , default=sa.sql.func.now()
            , server_default=sa.func.now()
        )

    @declared_attr
    def salt(self):
        """ Password salt for user """
        return sa.Column(sa.Unicode(256))

    @declared_attr
    def password(self):
        """ Password hash for user object """
        return sa.Column(sa.Unicode(256))

    def set_password(self, raw_password):
        self.password = self.hash_password(raw_password)

    def hash_password(self, password):
        if not self.salt:
            self.salt = generate_random_string(24)

        return unicode(crypt.encode(password + self.salt))

    @classmethod
    def generate_random_password(cls, chars=12):
        """ generates random string of fixed length"""
        return generate_random_string(chars)

    def gravatar_url(self, default='mm'):
        """ returns user gravatar url """
        # construct the url
        h = hashlib.md5(self.email.encode('utf8').lower()).hexdigest()
        base_url = "https://secure.gravatar.com/avatar/%s?%s"
        gravatar_url = base_url % (h, urllib.urlencode({'d': default}))

        return gravatar_url

    def __repr__(self):
        return '<User: %s>' % self.user_name

    @property
    def __acl__(self):
        return [
                (Allow, 'user:%s' % self.pk, 'access_user')
        ]

class GroupMixin(BaseModel):
    """ base mixin for group object"""

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(50), unique=True)

    @declared_attr
    def description(self):
        return sa.Column(sa.UnicodeText())

    @declared_attr
    def users(self):
        """ relationship for users belonging to this group"""
        return sa.orm.relationship(
            'User'
            , secondary='users_groups'
            , order_by='User.user_name'
            , passive_deletes=True
            , passive_updates=True
            , backref='groups'
        )

    @declared_attr
    def permissions(self):
        """ permissions assigned to this group"""
        return sa.orm.relationship('GroupPermission'
            , backref='groups'
            , cascade="all, delete-orphan"
            , passive_deletes=True
            , passive_updates=True
        )

    def __repr__(self):
        return '<Group: %s>' % self.group_name

class GroupPermissionMixin(BaseModel):
    """ group permission mixin """
    @declared_attr
    def group_name(self):
        return sa.Column(
            sa.Unicode(50)
            , sa.ForeignKey('group.group_name', onupdate='CASCADE'
            , ondelete='CASCADE'), primary_key=True
        )

    @declared_attr
    def permission_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<GroupPermission: %s>' % self.permission_name

class UserGroupMixin(BaseModel):
    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(50),
                         sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def user_name(self):
        return sa.Column(sa.Unicode(30),
                        sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)

    def __repr__(self):
        return '<UserGroup: %s, %s>' % (self.group_name, self.user_name,)

