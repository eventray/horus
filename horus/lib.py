# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid.security   import unauthenticated_userid
from horus.interfaces   import IHorusUserClass


def get_user(request):
    pk = unauthenticated_userid(request)
    user_class = request.registry.queryUtility(IHorusUserClass)

    if pk is not None:
        return user_class.get_by_pk(request, pk)
