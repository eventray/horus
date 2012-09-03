# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.resources import UserFactory


def includeme(config):
    """Add routes to the config."""
    config.add_route('horus_login', 'login')
    config.add_route('horus_logout', 'logout')
    config.add_route('horus_register', '/register')
    config.add_route('horus_activate', '/activate/{user_pk}/{code}',
        factory=UserFactory)
    config.add_route('horus_forgot_password', '/forgot_password')
    config.add_route('horus_reset_password', '/reset_password/{code}')
    config.add_route('horus_profile', '/profile/{user_pk}',
        factory=UserFactory, traverse="/{user_pk}")
    config.add_route('horus_edit_profile', '/profile/{user_pk}/edit',
        factory=UserFactory, traverse="/{user_pk}")

    config.add_route('horus_admin', '/admin')
    config.add_route('horus_admin_users_index', '/admin/users')
    config.add_route('horus_admin_users_create', '/admin/users/new')
    config.add_route('horus_admin_users_edit',
        '/admin/users/{user_pk}/edit',
        factory=UserFactory,
        traverse="/{user_pk}",
    )
