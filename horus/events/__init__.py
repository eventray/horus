# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


class BaseEvent(object):
    def __init__(self, request, user):
        self.request = request
        self.user = user


class NewRegistrationEvent(BaseEvent):
    def __init__(self, request, user, activation, values):
        super(NewRegistrationEvent, self).__init__(request, user)
        self.activation = activation
        self.values = values


class RegistrationActivatedEvent(BaseEvent):
    def __init__(self, request, user, activation):
        super(RegistrationActivatedEvent, self).__init__(request, user)
        self.activation = activation


class PasswordResetEvent(BaseEvent):
    def __init__(self, request, user, password):
        super(PasswordResetEvent, self).__init__(request, user)
        self.password = password


class ProfileUpdatedEvent(BaseEvent):
    def __init__(self, request, user, values):
        super(ProfileUpdatedEvent, self).__init__(request, user)
        self.values = values
