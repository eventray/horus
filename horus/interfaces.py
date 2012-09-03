# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from zope.interface import Interface


class IHorusUserClass(Interface):
    pass


class IHorusActivationClass(Interface):
    pass


class IHorusLoginSchema(Interface):
    pass


class IHorusLoginForm(Interface):
    pass


class IHorusRegisterSchema(Interface):
    pass


class IHorusRegisterForm(Interface):
    pass


class IHorusForgotPasswordForm(Interface):
    pass


class IHorusForgotPasswordSchema(Interface):
    pass


class IHorusResetPasswordForm(Interface):
    pass


class IHorusResetPasswordSchema(Interface):
    pass


class IHorusProfileForm(Interface):
    pass


class IHorusProfileSchema(Interface):
    pass
