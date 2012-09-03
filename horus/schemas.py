# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import colander
import deform
from pyramid_deform import CSRFSchema


class LoginSchema(CSRFSchema):
    User_name = colander.SchemaNode(colander.String())
    Password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.PasswordWidget())


class RegisterSchema(CSRFSchema):
    User_name = colander.SchemaNode(colander.String())
    Email = colander.SchemaNode(colander.String(),
        validator=colander.Email())
    Password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget())


class ForgotPasswordSchema(CSRFSchema):
    Email = colander.SchemaNode(colander.String(),
        validator=colander.Email())


class ResetPasswordSchema(CSRFSchema):
    User_name = colander.SchemaNode(colander.String(),
            widget=deform.widget.TextInputWidget(template='readonly/textinput'),
            missing=colander.null,
    )
    Password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget())


class ProfileSchema(CSRFSchema):
    User_name = colander.SchemaNode(colander.String(),
            widget=deform.widget.TextInputWidget(template='readonly/textinput'),
            missing=colander.null,
        )
    Email = colander.SchemaNode(colander.String(),
        validator=colander.Email())
    Password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(),
        missing=colander.null)


class AdminUserSchema(CSRFSchema):
    user_name = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(
        colander.String(),
        validator=colander.Email()
    )
    password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(),
        missing=colander.null
    )
