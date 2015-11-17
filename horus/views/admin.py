# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
#import deform
#import colander
from pyramid.view           import view_config, view_defaults
from pyramid.httpexceptions import HTTPFound
from horus.lib              import FlashMessage
from horus.views            import BaseController
from horus.views            import validate_form, render_form
from horus.exceptions import FormValidationFailure
from horus.interfaces       import IAdminEditUserSchema
from horus.interfaces       import IAdminEditUserForm
from horus.interfaces       import IAdminCreateUserSchema
from horus.interfaces       import IAdminCreateUserForm
from horus.events import ProfileUpdatedEvent
#from horus.forms            import HorusForm
#from horus.resources        import RootFactory

import logging
LOG = logging.getLogger()

@view_defaults(permission='group:admin')
class AdminController(BaseController):

    def __init__(self, request):
        super(AdminController, self).__init__(request)

        schema = request.registry.getUtility(IAdminEditUserSchema)
        self.edit_schema = schema().bind(request=self.request)
        schema = request.registry.getUtility(IAdminCreateUserSchema)
        self.create_schema = schema().bind(request=self.request)

        form = request.registry.getUtility(IAdminEditUserForm)
        self.edit_form = form(self.edit_schema)
        form = request.registry.getUtility(IAdminCreateUserForm)
        self.create_form = form(self.create_schema)


    @view_config(
        route_name='admin_users_edit',
        renderer='horus:templates/admin/edit_user.mako'
    )
    def edit_user(self):
        try:
            user_id = self.request.matchdict.get('user_id', False)
            if user_id:
                user = self.User.get_by_id(self.request, user_id)

                if self.request.method == 'GET':
                    appstruct = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                    }
                    return render_form(self.request, self.edit_form, appstruct)
                elif self.request.method == 'POST':
                    try:
                        controls = self.request.POST.items()
                        captured = validate_form(controls, self.edit_form)
                    except FormValidationFailure as e:
                        return e.result(self.request)

                    user.username = captured.get('username')
                    user.email = captured.get('email')
                    if captured.get('password'):
                        user.password = captured.get('password')

                    self.request.registry.notify(
                        ProfileUpdatedEvent(self.request, user, captured)
                    )

                    self.db.add(user)

                    FlashMessage(self.request,
                        self.Str.admin_edit_user_done.format(user.username),
                        kind='success')

            else:
                FlashMessage(self.request,
                    self.Str.admin_user_id_missing,
                    kind='error')

        except Exception as e:
            LOG.error('{}: {}'.format(__name__, e))
            FlashMessage(self.request,
                'There was an unexpected error! Check the logs.',
                kind='error')

        return HTTPFound(
            location=self.request.route_url('admin_users_index')
        )


    @view_config(
        route_name='admin_users_create',
        renderer='horus:templates/admin/create_user.mako'
    )
    def create_user(self):

        if self.request.method == 'GET':
            return render_form(self.request, self.create_form)
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = validate_form(controls, self.create_form)
            except FormValidationFailure as e:
                return e.result(self.request)

            username = captured.get('username')
            email = captured.get('email')
            password = captured.get('password')

            user = self.User(username=username,
                password=password, email=email)
            self.db.add(user)

            FlashMessage(self.request,
                self.Str.admin_create_user_done.format(username),
                kind='success')

            return HTTPFound(
                location=self.request.route_url('admin_users_index')
            )

    @view_config(
        route_name='admin',
        renderer='horus:templates/admin/index.mako'
    )
    def index(self):
        return {}

    @view_config(
        route_name='admin_users_index',
        renderer='horus:templates/admin/users_index.mako'
    )
    def users_index(self):
        return dict(users=self.User.get_all(self.request))

    @view_config(
        route_name='admin_users_deactivate',
    )
    def deactivate_user(self):
        try:
            user_id = self.request.matchdict.get('user_id', False)
            if user_id:
                user = self.User.get_by_id(self.request, user_id)

                user.activation = self.Activation()
                self.db.add(user)

                FlashMessage(self.request,
                    self.Str.admin_deactivate_user_done.format(user.username),
                    kind='success')
            else:
                FlashMessage(self.request,
                    self.Str.admin_user_id_missing,
                    kind='error')

        except Exception as e:
            LOG.error('{}: {}'.format(__name__, e))
            FlashMessage(self.request,
                'There was an unexpected error! Check the logs.',
                kind='error')


        return HTTPFound(
            location=self.request.route_url('admin_users_index')
        )

    @view_config(
        route_name='admin_users_activate',
    )
    def activate_user(self):
        try:
            user_id = self.request.matchdict.get('user_id', False)
            if user_id:
                user = self.User.get_by_id(self.request, user_id)

                self.db.delete(user.activation)

                FlashMessage(self.request,
                    self.Str.admin_activate_user_done.format(user.username),
                    kind='success')
            else:
                FlashMessage(self.request,
                    self.Str.admin_user_id_missing,
                    kind='error')

        except Exception as e:
            LOG.error('{}: {}'.format(__name__, e))
            FlashMessage(self.request,
                'There was an unexpected error! Check the logs.',
                kind='error')


        return HTTPFound(
            location=self.request.route_url('admin_users_index')
        )
