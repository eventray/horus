# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import colander
import deform
from hem.schemas import CSRFSchema


class ProfileSchema(CSRFSchema):
    username = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.TextInputWidget(template='readonly/textinput'),
        missing=colander.null,
    )
    email = colander.SchemaNode(colander.String(), validator=colander.Email())
    first = colander.SchemaNode(colander.String())
    last = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=2),
        widget=deform.widget.CheckedPasswordWidget(),
        missing=colander.null
    )
