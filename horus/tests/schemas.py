# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import colander
import deform

from pyramid_deform import CSRFSchema


class ProfileSchema(CSRFSchema):
    Username = colander.SchemaNode(colander.String(),
        widget=deform.widget.TextInputWidget(template='readonly/textinput'),
        missing=colander.null,
    )
    Email = colander.SchemaNode(colander.String(),
        validator=colander.Email())
    First = colander.SchemaNode(colander.String())
    Last = colander.SchemaNode(colander.String())
    Password = colander.SchemaNode(colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(),
        missing=colander.null)
