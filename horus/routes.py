# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.resources import UserFactory


def includeme(config):
    """Add routes to the config."""
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')
    config.add_route('activate', '/activate/{user_id}/{code}',
                     factory=UserFactory)
    config.add_route('forgot_password', '/forgot_password')
    config.add_route('reset_password', '/reset_password/{code}')
    config.add_route('profile', '/profile/{user_id}',
                     factory=UserFactory,
                     traverse="/{user_id}")
    config.add_route('edit_profile', '/profile/{user_id}/edit',
                     factory=UserFactory,
                     traverse="/{user_id}")

    config.add_route('admin', '/admin')
    config.add_route('admin_users_index', '/admin/users')
    config.add_route('admin_users_create', '/admin/users/new')
    config.add_route('admin_users_edit',
                     '/admin/users/{user_id}/edit',
                     factory=UserFactory,
                     traverse="/{user_id}")
