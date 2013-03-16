# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import re
import colander as c
import deform
import deform.widget as w
from hem.db import get_session
from hem.schemas import CSRFSchema
from .interfaces import IUserClass, IUIStrings
from .models import _


def email_exists(node, val):
    '''Colander validator that ensures a User exists with the email.'''
    req = node.bindings['request']
    User = req.registry.getUtility(IUserClass)
    exists = get_session(req).query(User).filter(User.email.ilike(val)).count()
    if not exists:
        Str = req.registry.getUtility(IUIStrings)
        raise c.Invalid(node, Str.reset_password_email_must_exist.format(val))


def unique_email(node, val):
    '''Colander validator that ensures the email does not exist.'''
    req = node.bindings['request']
    User = req.registry.getUtility(IUserClass)
    other = get_session(req).query(User).filter(User.email.ilike(val)).first()
    if other:
        S = req.registry.getUtility(IUIStrings)
        raise c.Invalid(node, S.registration_email_exists.format(other.email))


def unique_username(node, value):
    '''Colander validator that ensures the username does not exist.'''
    req = node.bindings['request']
    User = req.registry.getUtility(IUserClass)
    if get_session(req).query(User).filter(User.username == value).count():
        Str = req.registry.getUtility(IUIStrings)
        raise c.Invalid(node, Str.registration_username_exists)


def unix_username(node, value):  # TODO This is currently not used
    '''Colander validator that ensures the username is alphanumeric.'''
    if not ALPHANUM.match(value):
        raise c.Invalid(node, _("Contains unacceptable characters."))
ALPHANUM = re.compile(r'^[a-zA-Z0-9_.-]+$')


class LoginSchema(CSRFSchema):
    username = c.SchemaNode(c.String())
    password = c.SchemaNode(c.String(), validator=c.Length(min=2),
        widget=deform.widget.PasswordWidget())


class RegisterSchema(CSRFSchema):
    username = c.SchemaNode(c.String(), title=_('User name'),
        description=_("Name with which you will log in"),
        validator=unique_username)
    email = c.SchemaNode(c.String(), title=_('Email'),
        validator=c.All(c.Email(), unique_email),
        description=_("Example: joe@example.com"),
        widget=w.TextInputWidget(size=40, maxlength=260, type='email'))
    password = c.SchemaNode(c.String(), validator=c.Length(min=4),
        widget=deform.widget.CheckedPasswordWidget(),
        description=_("Your password must be harder than a "
            "dictionary word or proper name!"))


class ForgotPasswordSchema(CSRFSchema):
    email = c.SchemaNode(c.Str(), title=_('Email'),
        validator=c.All(c.Email(), email_exists),
        # type='email' will render an HTML5 email field
        # if you use deform_bootstrap_extra:
        widget=w.TextInputWidget(size=40, maxlength=260, type='email'),
        description=_("The email address under which you have your account. "
            "Example: joe@example.com"))


class ResetPasswordSchema(CSRFSchema):
    username = c.SchemaNode(c.String(), missing=c.null,
        widget=deform.widget.TextInputWidget(template='readonly/textinput'))
    password = c.SchemaNode(c.String(),  validator=c.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget())


class ProfileSchema(CSRFSchema):
    username = c.SchemaNode(c.String(),
        widget=deform.widget.TextInputWidget(template='readonly/textinput'),
        missing=c.null)
    email = c.SchemaNode(c.String(), validator=c.Email())
    password = c.SchemaNode(c.String(), validator=c.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(), missing=c.null)


class AdminUserSchema(CSRFSchema):
    username = c.SchemaNode(c.String())
    email = c.SchemaNode(c.String(), validator=c.Email())
    password = c.SchemaNode(c.String(), validator=c.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(), missing=c.null)
