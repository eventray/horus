# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid.view           import view_config
from pyramid.url            import route_url
from pyramid.security       import remember
from pyramid.security       import forget
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.settings       import asbool

from pyramid_mailer         import get_mailer
from pyramid_mailer.message import Message

from horus.interfaces       import IHorusUserClass
from horus.interfaces       import IHorusActivationClass
from horus.interfaces       import IHorusLoginForm
from horus.interfaces       import IHorusLoginSchema
from horus.interfaces       import IHorusRegisterForm
from horus.interfaces       import IHorusRegisterSchema
from horus.interfaces       import IHorusForgotPasswordForm
from horus.interfaces       import IHorusForgotPasswordSchema
from horus.interfaces       import IHorusResetPasswordForm
from horus.interfaces       import IHorusResetPasswordSchema
from horus.interfaces       import IHorusProfileForm
from horus.interfaces       import IHorusProfileSchema
from horus.events           import NewRegistrationEvent
from horus.events           import RegistrationActivatedEvent
from horus.events           import PasswordResetEvent
from horus.events           import ProfileUpdatedEvent
from horus.models import _
from hem.db                 import get_session

import deform
import pystache


def authenticated(request, pk):
    """Sets the auth cookies and redirects to the page defined
    in horus.login_redirect, which defaults to a view named 'index'.
    """
    settings = request.registry.settings
    headers = remember(request, pk)
    autologin = asbool(settings.get('horus.autologin', False))

    if not autologin:
        request.session.flash(_('Logged in successfully.'), 'success')

    login_redirect_view = route_url(settings.get('horus.login_redirect', 'index'), request)

    return HTTPFound(location=login_redirect_view, headers=headers)


def create_activation(request, user):
    db = get_session(request)
    Activation = request.registry.getUtility(IHorusActivationClass)
    activation = Activation()

    db.add(activation)
    user.activation = activation

    db.flush()

    body = pystache.render(_("Please activate your e-mail address by visiting {{ link }}"),
        {
            'link': request.route_url('horus_activate', user_pk=user.pk, code=user.activation.code)
        }
    )

    subject = _("Please activate your e-mail address!")

    message = Message(subject=subject, recipients=[user.email], body=body)

    mailer = get_mailer(request)
    mailer.send(message)


class BaseController(object):
    @property
    def request(self):
        # we defined this so that we can override the request in tests easily
        return self._request

    def __init__(self, request):
        self._request = request
        self.settings = request.registry.settings
        self.User = request.registry.getUtility(IHorusUserClass)
        self.Activation = request.registry.getUtility(IHorusActivationClass)
        self.db = get_session(request)


class AuthController(BaseController):
    def __init__(self, request):
        super(AuthController, self).__init__(request)

        schema = request.registry.getUtility(IHorusLoginSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(IHorusLoginForm)

        self.login_redirect_view = route_url(self.settings.get('horus.login_redirect', 'index'), request)
        self.logout_redirect_view = route_url(self.settings.get('horus.logout_redirect', 'index'), request)
        self.require_activation = asbool(self.settings.get('horus.require_activation', True))
        self.allow_inactive_login = asbool(self.settings.get('horus.allow_inactive_login', False))

        self.form = form(self.schema)

    @view_config(route_name='horus_login',
        renderer='horus:templates/login.mako')
    def login(self):
        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.login_redirect_view)

            return {'form': self.form.render()}
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = self.form.validate(controls)
            except deform.ValidationFailure as e:
                return {'form': e.render(), 'errors': e.error.children}

            username = captured['User_name']
            password = captured['Password']

            allow_email_auth = self.settings.get('horus.allow_email_auth', False)

            user = self.User.get_user(self.request, username, password)

            if allow_email_auth:
                if not user:
                    user = self.User.get_by_email_password(username,
                            password)

            if user:
                if not self.allow_inactive_login and self.require_activation \
                        and not user.is_activated:
                    self.request.session.flash(
                        _('Your account is not active, please check your e-mail.'),
                        'error')
                    return {'form': self.form.render()}

                return authenticated(self.request, user.pk)

            self.request.session.flash(_('Invalid username or password.'), 'error')

            return {'form': self.form.render(appstruct=captured)}

    @view_config(permission='view', route_name='horus_logout')
    def logout(self):
        """Removes the auth cookies and redirects to the view defined in
        horus.logout_redirect, which defaults to a view named 'index'.
        """
        self.request.session.invalidate()
        self.request.session.flash(_('Logged out successfully.'), 'success')
        headers = forget(self.request)

        return HTTPFound(location=self.logout_redirect_view, headers=headers)


class ForgotPasswordController(BaseController):
    def __init__(self, request):
        super(ForgotPasswordController, self).__init__(request)

        self.forgot_password_redirect_view = route_url(self.settings.get('horus.forgot_password_redirect', 'index'), request)
        self.reset_password_redirect_view = route_url(self.settings.get('horus.reset_password_redirect', 'index'), request)

    @view_config(route_name='horus_forgot_password', renderer='horus:templates/forgot_password.mako')
    def forgot_password(self):
        schema = self.request.registry.getUtility(IHorusForgotPasswordSchema)
        schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IHorusForgotPasswordForm)
        form = form(schema)

        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.forgot_password_redirect_view)

            return {'form': form.render()}

        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = form.validate(controls)
            except deform.ValidationFailure as e:
                return {'form': e.render(), 'errors': e.error.children}

            email = captured['Email']

            user = self.User.get_by_email(self.request, email)
            activation = self.Activation()
            self.db.add(activation)

            user.activation = activation

            if user:
                mailer = get_mailer(self.request)
                body = pystache.render(_("Someone has tried to reset your password, if this was you click here: {{ link }}"),
                    {
                        'link': route_url('horus_reset_password', self.request, code=user.activation.code)
                    }
                )

                subject = _("Do you want to reset your password?")

                message = Message(subject=subject, recipients=[user.email], body=body)
                mailer.send(message)

        # we don't want to say "E-mail not registered" or anything like that
        # because it gives spammers context
        self.request.session.flash(_('Please check your e-mail to reset your password.'), 'success')
        return HTTPFound(location=self.reset_password_redirect_view)

    @view_config(route_name='horus_reset_password', renderer='horus:templates/reset_password.mako')
    def reset_password(self):
        schema = self.request.registry.getUtility(IHorusResetPasswordSchema)
        schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IHorusResetPasswordForm)
        form = form(schema)

        code = self.request.matchdict.get('code', None)

        activation = self.Activation.get_by_code(self.request, code)

        if activation:
            user = self.User.get_by_activation(self.request, activation)

            if user:
                if self.request.method == 'GET':
                        return {
                            'form': form.render(
                                appstruct=dict(
                                    User_name=user.user_name
                                )
                            )
                        }

                elif self.request.method == 'POST':
                    try:
                        controls = self.request.POST.items()
                        captured = form.validate(controls)
                    except deform.ValidationFailure as e:
                        return {'form': e.render(), 'errors': e.error.children}

                    password = captured['Password']

                    user.password = password
                    self.db.add(user)
                    self.db.delete(activation)

                    self.request.registry.notify(
                        PasswordResetEvent(self.request, user, password)
                    )

                    self.request.session.flash(_('Your password has been reset!'), 'success')

                    return HTTPFound(location=self.reset_password_redirect_view)

        return HTTPNotFound()


class RegisterController(BaseController):
    def __init__(self, request):
        super(RegisterController, self).__init__(request)
        schema = request.registry.getUtility(IHorusRegisterSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(IHorusRegisterForm)
        self.form = form(self.schema)

        self.register_redirect_view = route_url(
            self.settings.get('horus.register_redirect', 'index'), request)
        self.activate_redirect_view = route_url(
            self.settings.get('horus.activate_redirect', 'index'), request)

        self.require_activation = asbool(
            self.settings.get('horus.require_activation', True))

        if self.require_activation:
            self.mailer = get_mailer(request)

    @view_config(route_name='horus_register',
        renderer='horus:templates/register.mako')
    def register(self):
        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.register_redirect_view)
            return {'form': self.form.render()}
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = self.form.validate(controls)
            except deform.ValidationFailure as e:
                return {'form': e.render(), 'errors': e.error.children}

            email = captured['Email']
            username = captured['User_name'].lower()
            password = captured['Password']

            user = self.User.get_by_user_name_or_email(self.request,
                    username, email
            )

            autologin = asbool(self.settings.get('horus.autologin', False))

            if user:
                if user.user_name == username:
                    self.request.session.flash(
                        _('That username is already used.'), 'error')
                elif user.email == email:
                    self.request.session.flash(
                        _('That e-mail is already used.'), 'error')
                return {'form': self.form.render(self.request.POST)}

            activation = None

            try:
                user = self.User(user_name=username, email=email)
                user.set_password(password)

                self.db.add(user)

                if self.require_activation:
                    # SEND EMAIL ACTIVATION
                    create_activation(self.request, user)
                    self.request.session.flash(
                        _('Please check your e-mail for an activation link.'),
                        'success')
                else:
                    if not autologin:
                        self.request.session.flash(
                            _('You have been registered, you may log in now!'),
                            'success')
            except Exception as exc:  # TODO Catch finer-grained exceptions
                self.request.session.flash(exc.args[0], 'error')
                return {'form': self.form.render()}

            self.request.registry.notify(
                NewRegistrationEvent(self.request, user, activation,
                    captured)
            )
            if autologin:
                self.db.flush()  # in order to get the pk
                return authenticated(self.request, user.pk)
            else:  # not autologin: User must log in just after registering.
                return HTTPFound(location=self.register_redirect_view)

    @view_config(route_name='horus_activate')
    def activate(self):
        code = self.request.matchdict.get('code', None)
        user_pk = self.request.matchdict.get('user_pk', None)

        activation = self.Activation.get_by_code(self.request, code)

        if activation:
            user = self.User.get_by_pk(self.request, user_pk)

            if user.activation != activation:
                return HTTPNotFound()

            if user:
                self.db.delete(activation)
                self.db.add(user)
                self.db.flush()

                self.request.registry.notify(
                    RegistrationActivatedEvent(self.request, user, activation)
                )

                self.request.session.flash(_('Your e-mail address has been verified.'), 'success')
                return HTTPFound(location=self.activate_redirect_view)

        return HTTPNotFound()


class ProfileController(BaseController):
    def __init__(self, request):
        super(ProfileController, self).__init__(request)

        schema = self.request.registry.getUtility(IHorusProfileSchema)
        self.schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IHorusProfileForm)
        self.form = form(self.schema)

    @view_config(route_name='horus_profile',
        renderer='horus:templates/profile.mako')
    def profile(self):
        pk = self.request.matchdict.get('user_pk', None)

        user = self.User.get_by_pk(self.request, pk)

        if not user:
            return HTTPNotFound()

        return {'user': user}

    @view_config(permission='access_user', route_name='horus_edit_profile',
        renderer='horus:templates/edit_profile.mako')
    def edit_profile(self):
        user = self.request.context

        if not user:
            return HTTPNotFound()

        if self.request.method == 'GET':
            username = user.user_name
            email = user.email

            return {
                    'form': self.form.render(
                        appstruct=dict(
                            User_name=username,
                            Email=email if email else '',
                        )
                    )
                }
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = self.form.validate(controls)
            except deform.ValidationFailure as e:
                # We pre-populate username
                e.cstruct['User_name'] = user.user_name
                return {'form': e.render(), 'errors': e.error.children}

            email = captured.get('Email', None)

            if email:
                email_user = self.User.get_by_email(self.request, email)
                if email_user:
                    if email_user.pk != user.pk:
                        self.request.session.flash(
                            _('That e-mail is already used.'), 'error')
                        return HTTPFound(location=self.request.url)
                user.email = email

            password = captured.get('Password')

            if password:
                user.set_password(password)

            self.request.session.flash(_('Profile successfully updated.'),
                'success')

            self.db.add(user)

            self.request.registry.notify(
                ProfileUpdatedEvent(self.request, user, captured)
            )
            return HTTPFound(location=self.request.url)
