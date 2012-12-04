# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid import httpexceptions as exc
from pyramid.response import Response
try:
    import json
except ImportError:
    import simplejson as json


class JSONError(exc.HTTPError):
    def __init__(self, errors, status=400):
        body = {'status': 'error', 'errors': errors}
        Response.__init__(self, json.dumps(body, use_decimal=True))
        self.status = status
        self.content_type = 'application/json'


class HTTPUnauthorized(JSONError):
    def __init__(self, errors):
        super(HTTPUnauthorized, self).__init__(errors, status=401)


class HTTPInternalServerError(JSONError):
    def __init__(self, errors):
        super(HTTPInternalServerError, self).__init__(errors, status=500)


class HTTPNotFound(JSONError):
    def __init__(self, errors):
        super(HTTPNotFound, self).__init__(errors, status=404)


class HTTPBadRequest(JSONError):
    def __init__(self, errors):
        super(HTTPBadRequest, self).__init__(errors, status=400)
