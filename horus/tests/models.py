# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from sqlalchemy.ext.declarative import declarative_base
from horus.models               import GroupMixin
from horus.models               import UserMixin
from horus.models               import UserGroupMixin
from horus.models               import ActivationMixin
from horus.models               import BaseModel

Base = declarative_base(cls=BaseModel)


class User(UserMixin, Base):
    pass


class Group(GroupMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base):
    pass


class Activation(ActivationMixin, Base):
    pass
