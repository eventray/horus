# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from zope.interface import Interface


class IUserClass(Interface):
    pass


class IActivationClass(Interface):
    pass


class ILoginSchema(Interface):
    pass


class ILoginForm(Interface):
    pass


class IRegisterSchema(Interface):
    pass


class IRegisterForm(Interface):
    pass


class IForgotPasswordForm(Interface):
    pass


class IForgotPasswordSchema(Interface):
    pass


class IResetPasswordForm(Interface):
    pass


class IResetPasswordSchema(Interface):
    pass


class IProfileForm(Interface):
    pass


class IProfileSchema(Interface):
    pass
