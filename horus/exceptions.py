# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from pyramid.settings import asbool


class AuthenticationFailure(Exception):
    pass


class FormValidationFailure(Exception):
    def __init__(self, form, exc):
        Exception.__init__(self)
        self.form = form
        self.exc = exc

    def result(self, request, **cstruct):
        settings = request.registry.settings
        retail = asbool(settings.get('horus.deform_retail', False))

        if retail:
            form = self.form
            errors = self.form.error.children
        else:
            form = self.exc
            errors = self.exc.error.children

        for k, v in cstruct.items():
            form.cstruct[k] = v

        if not retail:
            form = form.render()
        return {'form': form, 'errors': errors}
