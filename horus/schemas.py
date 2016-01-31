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


def username_does_not_contain_at(node, value):
    '''Colander validator that ensures the username does not contain an
    ``@`` character.

    This is important because the system can be configured to accept
    an email or a username in the same field at login time, so the
    presence or absence of the @ tells us whether it is an email address.
    '''
    if '@' in value:
        raise c.Invalid(node, _("May not contain this character: @"))


# Schema fragments
# ----------------
# These functions reduce duplication in the schemas defined below,
# while ensuring some constant values are consistent among those schemas.

def get_username_creation_node(
        title=_('User name'), description=_("Name with which you will log in"),
        validator=None):
    return c.SchemaNode(
        c.String(), title=title, description=description,
        validator=validator or c.All(
            c.Length(max=30), username_does_not_contain_at, unique_username))


def get_email_node(validator=None, description=None):
    return c.SchemaNode(
        c.String(), title=_('Email'), description=description,
        validator=validator or c.All(c.Email(), unique_email),
        widget=w.TextInputWidget(size=40, maxlength=260, type='email',
                                 placeholder=_("joe@example.com")))


def get_checked_password_node(description=_(
        "Your password must be harder than a dictionary word or proper name!"),
        **kw):
    return c.SchemaNode(
        c.String(), title=_('Password'), validator=c.Length(min=4),
        widget=deform.widget.CheckedPasswordWidget(),
        description=description, **kw)


# Schemas
# -------

class UsernameLoginSchema(CSRFSchema):
    handle = c.SchemaNode(c.String(), title=_('User name'))
    password = c.SchemaNode(c.String(), widget=deform.widget.PasswordWidget())
LoginSchema = UsernameLoginSchema  # The name "LoginSchema" is deprecated.


class EmailLoginSchema(CSRFSchema):
    '''For login, some apps just use email and have no username column.'''
    handle = get_email_node(validator=c.Email())
    password = c.SchemaNode(c.String(), widget=deform.widget.PasswordWidget())


class UsernameRegisterSchema(CSRFSchema):
    username = get_username_creation_node()
    email = get_email_node()
    password = get_checked_password_node()
RegisterSchema = UsernameRegisterSchema  # name "RegisterSchema" is deprecated.


class EmailRegisterSchema(CSRFSchema):
    email = get_email_node()
    password = get_checked_password_node()


class ForgotPasswordSchema(CSRFSchema):
    email = get_email_node(
        validator=c.All(c.Email(), email_exists),
        description=_("The email address under which you have your account."))


class UsernameResetPasswordSchema(CSRFSchema):
    username = c.SchemaNode(
        c.String(), title=_('User name'), missing=c.null,
        widget=deform.widget.TextInputWidget(template='readonly/textinput'))
    password = get_checked_password_node()
ResetPasswordSchema = UsernameResetPasswordSchema  # deprecated name


class EmailResetPasswordSchema(CSRFSchema):
    email = c.SchemaNode(
        c.String(), title=_('Email'), missing=c.null,
        widget=deform.widget.TextInputWidget(template='readonly/textinput'))
    password = get_checked_password_node()


class UsernameProfileSchema(CSRFSchema):
    username = c.SchemaNode(
        c.String(),
        widget=deform.widget.TextInputWidget(template='readonly/textinput'),
        missing=c.null)
    email = get_email_node(description=None, validator=c.Email())
    password = get_checked_password_node(missing=c.null)
ProfileSchema = UsernameProfileSchema  # The name "ProfileSchema" is obsolete.


class EmailProfileSchema(CSRFSchema):
    email = get_email_node(description=None, validator=c.Email())
    password = get_checked_password_node(missing=c.null)


class UsernameAdminUserSchema(CSRFSchema):
    username = get_username_creation_node(description=None)
    email = get_email_node(description=None, validator=c.Email())
    password = get_checked_password_node(description=None, missing=c.null)
AdminUserSchema = UsernameAdminUserSchema  # deprecated name: AdminUserSchema


class EmailAdminUserSchema(CSRFSchema):
    email = get_email_node(description=None, validator=c.Email())
    password = get_checked_password_node(description=None, missing=c.null)
