# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid.security   import unauthenticated_userid
from horus.interfaces   import IUserClass


def get_user(request):
    userid = unauthenticated_userid(request)
    user_class = request.registry.queryUtility(IUserClass)

    if userid is not None:
        return user_class.get_by_id(request, userid)

    return None
