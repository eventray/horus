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

from horus.interfaces       import IUserClass
from horus.interfaces       import IActivationClass
from horus.interfaces       import ILoginForm
from horus.interfaces       import ILoginSchema
from horus.interfaces       import IRegisterForm
from horus.interfaces       import IRegisterSchema
from horus.interfaces       import IForgotPasswordForm
from horus.interfaces       import IForgotPasswordSchema
from horus.interfaces       import IResetPasswordForm
from horus.interfaces       import IResetPasswordSchema
from horus.interfaces       import IProfileForm
from horus.interfaces       import IProfileSchema
from horus.events           import NewRegistrationEvent
from horus.events           import RegistrationActivatedEvent
from horus.events           import PasswordResetEvent
from horus.events           import ProfileUpdatedEvent
from horus.models           import _
from horus.exceptions       import AuthenticationFailure
from horus.exceptions       import RegistrationFailure
from horus.httpexceptions   import HTTPBadRequest
from hem.db                 import get_session

import colander
import deform
import pystache


def authenticated(request, userid):
    """Sets the auth cookies and redirects to the page defined
    in horus.login_redirect, which defaults to a view named 'index'.
    """
    settings = request.registry.settings
    headers = remember(request, userid)
    autologin = asbool(settings.get('horus.autologin', False))

    if not autologin:
        request.session.flash(_('You are now logged in.'), 'success')

    login_redirect_route = settings.get('horus.login_redirect', 'index')
    location = route_url(login_redirect_route, request)

    return HTTPFound(location=location, headers=headers)


def create_activation(request, user):
    db = get_session(request)
    Activation = request.registry.getUtility(IActivationClass)
    activation = Activation()

    db.add(activation)
    user.activation = activation

    db.flush()

    # TODO Create a hook for the app to give us body and subject!
    # TODO We don't need pystache just for this!
    body = pystache.render(
        _("Please validate your email and activate your account by visiting:\n"
            "{{ link }}"),
        {
            'link': request.route_url('activate', user_id=user.id,
                                      code=user.activation.code)
        }
    )
    subject = _("Please activate your account!")

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
        self.User = request.registry.getUtility(IUserClass)
        self.Activation = request.registry.getUtility(IActivationClass)
        self.db = get_session(request)


class AuthController(BaseController):
    def __init__(self, request):
        super(AuthController, self).__init__(request)

        schema = request.registry.getUtility(ILoginSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(ILoginForm)

        self.login_redirect_view = route_url(
            self.settings.get('horus.login_redirect', 'index'),
            request
        )
        self.logout_redirect_view = route_url(
            self.settings.get('horus.logout_redirect', 'index'),
            request
        )
        self.require_activation = asbool(
            self.settings.get('horus.require_activation', True)
        )
        self.allow_inactive_login = asbool(
            self.settings.get('horus.allow_inactive_login', False)
        )

        self.form = form(self.schema)

    def check_credentials(self, username, password):
        allow_email_auth = self.settings.get('horus.allow_email_auth', False)

        user = self.User.get_user(self.request, username, password)

        if allow_email_auth and not user:
            user = self.User.get_by_email_password(username, password)

        if not user:
            raise AuthenticationFailure(_('Invalid username or password.'))

        if not self.allow_inactive_login and self.require_activation \
                and not user.is_activated:
            raise AuthenticationFailure(
                _('Your account is not active, please check your e-mail.'))

        return user

    @view_config(
            route_name='login'
            , xhr=True
            , accept="application/json"
            , renderer='json'
        )
    def login_ajax(self):
        try:
            cstruct = self.request.json_body
        except ValueError as e:
            raise HTTPBadRequest({'invalid': str(e)})

        try:
            captured = self.schema.deserialize(cstruct)
        except colander.Invalid as e:
            raise HTTPBadRequest({'invalid': e.asdict()})

        username = captured['username']
        password = captured['password']

        try:
            user = self.check_credentials(username, password)
        except AuthenticationFailure as e:
            raise HTTPBadRequest({
                'status': 'failure',
                'reason': e.message,
            })

        # We pass the user back as well so the authentication
        # can use its security code or any other information stored
        # on the user
        user_json = user.__json__(self.request)

        return {
            'status': 'okay'
            , 'user': user_json
        }

    @view_config(route_name='login', renderer='horus:templates/login.mako')
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
                return {
                    'form': e.render(),
                    'errors': e.error.children
                }

            username = captured['username']
            password = captured['password']

            try:
                user = self.check_credentials(username, password)
            except AuthenticationFailure as e:
                self.request.session.flash(str(e), 'error')
                return {
                    'form': self.form.render(appstruct=captured),
                    'errors': [e]
                }

            return authenticated(self.request, user.id)

    @view_config(permission='view', route_name='logout')
    def logout(self):
        """Removes the auth cookies and redirects to the view defined in
        horus.logout_redirect, which defaults to a view named 'index'.
        """
        self.request.session.invalidate()
        self.request.session.flash(_('You have logged out.'), 'success')
        headers = forget(self.request)

        return HTTPFound(location=self.logout_redirect_view, headers=headers)


class ForgotPasswordController(BaseController):
    def __init__(self, request):
        super(ForgotPasswordController, self).__init__(request)

        self.forgot_password_redirect_view = route_url(
            self.settings.get('horus.forgot_password_redirect', 'index'),
            request
        )
        self.reset_password_redirect_view = route_url(
            self.settings.get('horus.reset_password_redirect', 'index'),
            request
        )

    @view_config(route_name='forgot_password',
                 renderer='horus:templates/forgot_password.mako')
    def forgot_password(self):
        schema = self.request.registry.getUtility(IForgotPasswordSchema)
        schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IForgotPasswordForm)
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

            email = captured['email']

            user = self.User.get_by_email(self.request, email)
            activation = self.Activation()
            self.db.add(activation)

            user.activation = activation

            if user:
                mailer = get_mailer(self.request)
                body = pystache.render(
                    _("Someone has tried to reset your password. "
                      "If it was you, click here:\n{{ link }}"),
                    {
                        'link': route_url('reset_password', self.request,
                                          code=user.activation.code)
                    }
                )

                subject = _("Reset your password")

                message = Message(subject=subject, recipients=[user.email],
                                  body=body)
                mailer.send(message)

        # we don't want to say "E-mail not registered" or anything like that
        # because it gives spammers context
        self.request.session.flash(_('Please check your e-mail to finish '
            'resetting your password.'), 'success')
        return HTTPFound(location=self.reset_password_redirect_view)

    @view_config(route_name='reset_password',
                 renderer='horus:templates/reset_password.mako')
    def reset_password(self):
        schema = self.request.registry.getUtility(IResetPasswordSchema)
        schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IResetPasswordForm)
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
                                username=user.username
                            )
                        )
                    }

                elif self.request.method == 'POST':
                    try:
                        controls = self.request.POST.items()
                        captured = form.validate(controls)
                    except deform.ValidationFailure as e:
                        return {'form': e.render(), 'errors': e.error.children}

                    password = captured['password']

                    user.password = password
                    self.db.add(user)
                    self.db.delete(activation)

                    self.request.registry.notify(
                        PasswordResetEvent(self.request, user, password)
                    )

                    self.request.session.flash(
                        _('Your password has been reset!'), 'success')

                    location = self.reset_password_redirect_view
                    return HTTPFound(location=location)

        return HTTPNotFound()


class RegisterController(BaseController):
    def __init__(self, request):
        super(RegisterController, self).__init__(request)
        schema = request.registry.getUtility(IRegisterSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(IRegisterForm)
        self.form = form(self.schema)

        self.register_redirect_view = route_url(
            self.settings.get('horus.register_redirect', 'index'), request)
        self.activate_redirect_view = route_url(
            self.settings.get('horus.activate_redirect', 'index'), request)

        self.require_activation = asbool(
            self.settings.get('horus.require_activation', True))

        if self.require_activation:
            self.mailer = get_mailer(request)

    def create_user(self, email, username, password):
        user = self.User.get_by_username_or_email(
            self.request,
            username,
            email
        )

        if user:
            # XXX offload this logic to the model
            if user.email.lower() == email.lower():
                raise RegistrationFailure(
                    _('That e-mail is already used.'))
            else:
                raise RegistrationFailure(
                    _('That username is already used.'))

        user = self.User(username=username, email=email, password=password)
        self.db.add(user)
        return user

    @view_config(route_name='register',
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

            email = captured['email']
            username = captured['username'].lower()
            password = captured['password']

            try:
                user = self.create_user(email, username, password)
            except RegistrationFailure as e:
                self.request.session.flash(str(e), 'error')
                return HTTPFound(location=self.request.url)

            autologin = asbool(self.settings.get('horus.autologin', False))

            activation = None
            if self.require_activation:
                # SEND EMAIL ACTIVATION
                create_activation(self.request, user)
                self.request.session.flash(
                    _('Please check your e-mail for an activation link.'),
                    'success')
            else:
                if not autologin:
                    self.request.session.flash(
                        _('You have been registered. You may log in now!'),
                        'success')

            self.request.registry.notify(
                NewRegistrationEvent(self.request, user, activation, captured)
            )

            if autologin:
                self.db.flush()  # in order to get the id
                return authenticated(self.request, user.id)
            else:  # not autologin: User must log in just after registering.
                return HTTPFound(location=self.register_redirect_view)

    @view_config(route_name='activate')
    def activate(self):
        code = self.request.matchdict.get('code', None)
        user_id = self.request.matchdict.get('user_id', None)

        activation = self.Activation.get_by_code(self.request, code)

        if activation:
            user = self.User.get_by_id(self.request, user_id)

            if user.activation != activation:
                return HTTPNotFound()

            if user:
                self.db.delete(activation)
                self.db.add(user)
                self.db.flush()

                self.request.registry.notify(
                    RegistrationActivatedEvent(self.request, user, activation)
                )

                self.request.session.flash(
                    _('Your e-mail address has been verified.'), 'success')
                return HTTPFound(location=self.activate_redirect_view)

        return HTTPNotFound()


class ProfileController(BaseController):
    def __init__(self, request):
        super(ProfileController, self).__init__(request)

        schema = self.request.registry.getUtility(IProfileSchema)
        self.schema = schema().bind(request=self.request)

        form = self.request.registry.getUtility(IProfileForm)
        self.form = form(self.schema)

    @view_config(route_name='profile', renderer='horus:templates/profile.mako')
    def profile(self):
        user_id = self.request.matchdict.get('user_id', None)

        user = self.User.get_by_id(self.request, user_id)

        if not user:
            return HTTPNotFound()

        return {'user': user}

    @view_config(permission='access_user', route_name='edit_profile',
                 renderer='horus:templates/edit_profile.mako')
    def edit_profile(self):
        user = self.request.context

        if not user:
            return HTTPNotFound()

        if self.request.method == 'GET':
            username = user.username
            email = user.email

            return {
                'form': self.form.render(
                    appstruct=dict(
                        username=username,
                        email=email if email else '',
                    )
                )
            }
        elif self.request.method == 'POST':
            try:
                controls = self.request.POST.items()
                captured = self.form.validate(controls)
            except deform.ValidationFailure as e:
                # We pre-populate username
                e.cstruct['username'] = user.username
                return {'form': e.render(), 'errors': e.error.children}

            email = captured.get('email', None)

            if email:
                email_user = self.User.get_by_email(self.request, email)

                if email_user:
                    if email_user.id != user.id:
                        self.request.session.flash(
                            _('That e-mail is already used.'), 'error')
                        return HTTPFound(location=self.request.url)

                user.email = email

            password = captured.get('password')

            if password:
                user.password = password

            self.request.session.flash(_('Profile successfully updated.'),
                                       'success')

            self.db.add(user)

            self.request.registry.notify(
                ProfileUpdatedEvent(self.request, user, captured)
            )
            return HTTPFound(location=self.request.url)
