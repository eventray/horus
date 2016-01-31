# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging

from pyramid.view import view_config
from pyramid.url import route_url
from pyramid.security import remember
from pyramid.security import forget
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPNotFound
from pyramid.settings import asbool

from pyramid_mailer import get_mailer
from pyramid_mailer.message import Message

from hem.db import get_session
from ..interfaces import (
    IUserClass, IActivationClass, IUIStrings, ILoginForm, ILoginSchema,
    IRegisterForm, IRegisterSchema, IForgotPasswordForm, IForgotPasswordSchema,
    IResetPasswordForm, IResetPasswordSchema, IProfileForm, IProfileSchema)
from ..events import (NewRegistrationEvent, RegistrationActivatedEvent,
                      PasswordResetEvent, ProfileUpdatedEvent)
from ..lib import FlashMessage
from ..models import _
from ..exceptions import AuthenticationFailure, FormValidationFailure
from ..httpexceptions import HTTPBadRequest

import colander
import deform
import pystache


LOG = logging.getLogger(__name__)


def get_config_route(request, config_key):
    settings = request.registry.settings
    try:
        return request.route_url(settings[config_key])
    except KeyError:
        return settings[config_key]


def authenticated(request, userid):
    """Sets the auth cookies and redirects either to the URL indicated in
    the "next" parameter, or to the page defined in
    horus.login_redirect, which defaults to a view named 'index'.
    """
    settings = request.registry.settings
    headers = remember(request, userid)
    autologin = asbool(settings.get('horus.autologin', False))

    if not autologin:
        Str = request.registry.getUtility(IUIStrings)
        FlashMessage(request, Str.authenticated, kind='success')

    location = request.params.get('next') or get_config_route(
        request, 'horus.login_redirect')

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


def render_form(request, form, appstruct=None, **kw):
    settings = request.registry.settings
    retail = asbool(settings.get('horus.deform_retail', False))

    if appstruct is not None:
        form.set_appstruct(appstruct)

    if not retail:
        form = form.render()

    result = {'form': form}
    result.update(kw)
    return result


def validate_form(controls, form):
    try:
        captured = form.validate(controls)
    except deform.ValidationFailure as e:
        # NOTE(jkoelker) normally this is superfluous, but if the app is
        #                debug logging, then log that we "ate" the exception
        LOG.debug('Form validation failed', exc_info=True)
        raise FormValidationFailure(form, e)
    return captured


class BaseController(object):
    @property
    def request(self):
        # we defined this so that we can override the request in tests easily
        return self._request

    def __init__(self, request):
        self._request = request
        self.settings = request.registry.settings
        getUtility = request.registry.getUtility
        self.User = getUtility(IUserClass)
        self.Activation = getUtility(IActivationClass)
        self.Str = getUtility(IUIStrings)
        self.db = get_session(request)


class AuthController(BaseController):
    def __init__(self, request):
        super(AuthController, self).__init__(request)

        schema = request.registry.getUtility(ILoginSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(ILoginForm)

        self.login_redirect_view = get_config_route(
            request,
            'horus.login_redirect'
        )

        self.logout_redirect_view = get_config_route(
            request,
            'horus.logout_redirect'
        )

        self.require_activation = asbool(
            self.settings.get('horus.require_activation', True)
        )
        self.allow_inactive_login = asbool(
            self.settings.get('horus.allow_inactive_login', False)
        )
        self.form = form(self.schema, buttons=(self.Str.login_button,))

    def check_credentials(self, handle, password):
        user = self.User.get_user(self.request, handle, password)
        if not user:
            raise AuthenticationFailure(_('Invalid username or password.'))

        if not self.allow_inactive_login and self.require_activation \
                and not user.is_activated:
            raise AuthenticationFailure(
                _('Your account is not active, please check your e-mail.'))
        return user

    @view_config(route_name='login', xhr=True, accept="application/json",
                 renderer='json')
    def login_ajax(self):
        try:
            cstruct = self.request.json_body
        except ValueError as e:
            raise HTTPBadRequest({'invalid': str(e)})

        try:
            captured = self.schema.deserialize(cstruct)
        except colander.Invalid as e:
            raise HTTPBadRequest({'invalid': e.asdict()})

        handle = captured['handle']
        password = captured['password']

        try:
            user = self.check_credentials(handle, password)
        except AuthenticationFailure as e:
            raise HTTPBadRequest({
                'status': 'failure',
                'reason': e.message,
            })

        # We pass the user back as well so the authentication
        # can use its security code or any other information stored
        # on the user
        user_json = user.__json__(self.request)

        return {'status': 'okay',
                'user': user_json}

    @view_config(route_name='login', renderer='horus:templates/login.mako')
    def login(self):
        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.login_redirect_view)
            return render_form(self.request, self.form)

        elif self.request.method == 'POST':
            controls = self.request.POST.items()
            try:
                captured = validate_form(controls, self.form)
            except FormValidationFailure as e:
                return e.result(self.request)

            handle = captured['handle']
            password = captured['password']

            try:
                user = self.check_credentials(handle, password)
            except AuthenticationFailure as e:
                FlashMessage(self.request, str(e), kind='error')
                return render_form(self.request, self.form, captured,
                                   errors=[e])

            self.request.user = user  # Please keep this line, my app needs it
            return authenticated(self.request, user.id_value)

    @view_config(permission='view', route_name='logout')
    def logout(self):
        """Removes the auth cookies and redirects to the view defined in
        horus.logout_redirect, which defaults to a view named 'index'.
        """
        self.request.session.invalidate()
        headers = forget(self.request)
        FlashMessage(self.request, self.Str.logout, kind='success')
        return HTTPFound(location=self.logout_redirect_view, headers=headers)


class ForgotPasswordController(BaseController):
    def __init__(self, request):
        super(ForgotPasswordController, self).__init__(request)

        self.forgot_password_redirect_view = route_url(
            self.settings.get('horus.forgot_password_redirect', 'index'),
            request)
        self.reset_password_redirect_view = route_url(
            self.settings.get('horus.reset_password_redirect', 'index'),
            request)

    @view_config(route_name='forgot_password',
                 renderer='horus:templates/forgot_password.mako')
    def forgot_password(self):
        req = self.request
        schema = req.registry.getUtility(IForgotPasswordSchema)
        schema = schema().bind(request=req)

        form = req.registry.getUtility(IForgotPasswordForm)
        form = form(schema)

        if req.method == 'GET':
            if req.user:
                return HTTPFound(location=self.forgot_password_redirect_view)
            else:
                return render_form(req, form)

        # From here on, we know it's a POST. Let's validate the form
        controls = req.POST.items()

        try:
            captured = validate_form(controls, form)
        except FormValidationFailure as e:
            return e.result(req)

        user = self.User.get_by_email(req, captured['email'])
        activation = self.Activation()
        self.db.add(activation)
        user.activation = activation
        self.db.flush() # initialize activation.code

        Str = self.Str

        # TODO: Generate msg in a separate method so subclasses can override
        mailer = get_mailer(req)
        username = getattr(user, 'short_name', '') or \
            getattr(user, 'full_name', '') or \
            getattr(user, 'username', '') or user.email
        body = Str.reset_password_email_body.format(
            link=route_url('reset_password', req, code=user.activation.code),
            username=username, domain=req.application_url)
        subject = Str.reset_password_email_subject
        message = Message(subject=subject, recipients=[user.email], body=body)
        mailer.send(message)

        FlashMessage(self.request, Str.reset_password_email_sent,
            kind='success')
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
        if not activation:
            return HTTPNotFound()

        user = self.User.get_by_activation(self.request, activation)

        if user:
            if self.request.method == 'GET':
                appstruct = {'username': user.username} if hasattr(
                    user, 'username') else {'email': user.email}
                return render_form(self.request, form, appstruct)

            elif self.request.method == 'POST':
                controls = self.request.POST.items()
                try:
                    captured = validate_form(controls, form)
                except FormValidationFailure as e:
                    return e.result(self.request)

                password = captured['password']

                user.password = password
                self.db.add(user)
                self.db.delete(activation)

                FlashMessage(self.request, self.Str.reset_password_done,
                             kind='success')
                self.request.registry.notify(PasswordResetEvent(
                    self.request, user, password))
                location = self.reset_password_redirect_view
                return HTTPFound(location=location)


class RegisterController(BaseController):
    def __init__(self, request):
        super(RegisterController, self).__init__(request)
        schema = request.registry.getUtility(IRegisterSchema)
        self.schema = schema().bind(request=self.request)

        form = request.registry.getUtility(IRegisterForm)
        self.form = form(self.schema)

        self.after_register_url = route_url(
            self.settings.get('horus.register_redirect', 'index'), request)
        self.after_activate_url = route_url(
            self.settings.get('horus.activate_redirect', 'index'), request)

        self.require_activation = asbool(
            self.settings.get('horus.require_activation', True))

        if self.require_activation:
            self.mailer = get_mailer(request)

    @view_config(route_name='register',
                 renderer='horus:templates/register.mako')
    def register(self):
        if self.request.method == 'GET':
            if self.request.user:
                return HTTPFound(location=self.after_register_url)

            return render_form(self.request, self.form)

        elif self.request.method != 'POST':
            return

        # If the request is a POST:
        controls = self.request.POST.items()

        try:
            captured = validate_form(controls, self.form)
        except FormValidationFailure as e:
            return e.result(self.request)

        # With the form validated, we know email and username are unique.
        del captured['csrf_token']
        user = self.persist_user(captured)

        autologin = asbool(self.settings.get('horus.autologin', False))

        if self.require_activation:
            # SEND EMAIL ACTIVATION
            create_activation(self.request, user)
            FlashMessage(self.request, self.Str.activation_check_email,
                         kind='success')
        elif not autologin:
            FlashMessage(self.request, self.Str.registration_done,
                         kind='success')

        self.request.registry.notify(NewRegistrationEvent(
            self.request, user, None, controls))
        if autologin:
            self.db.flush()  # in order to get the id
            return authenticated(self.request, user.id)
        else:  # not autologin: user must log in just after registering.
            return HTTPFound(location=self.after_register_url)

    def persist_user(self, controls):
        '''To change how the user is stored, override this method.'''
        # This generic method must work with any custom User class and any
        # custom registration form:
        user = self.User(**controls)
        self.db.add(user)
        return user

    @view_config(route_name='activate')
    def activate(self):
        code = self.request.matchdict.get('code', None)
        user_id = self.request.matchdict.get('user_id', None)

        activation = self.Activation.get_by_code(self.request, code)
        if not activation:
            return HTTPNotFound()

        user = self.User.get_by_id(self.request, user_id)
        if not user:
            return HTTPNotFound()

        if user.activation is not activation:
            return HTTPNotFound()

        self.db.delete(activation)
        FlashMessage(self.request, self.Str.activation_email_verified,
                     kind='success')
        self.request.registry.notify(
            RegistrationActivatedEvent(self.request, user, activation))
        # If an exception is raised in an event subscriber, this never runs:
        return HTTPFound(location=self.after_activate_url)


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
            appstruct = {'email': user.email or ''}
            if hasattr(user, 'username'):
                appstruct['username'] = user.username
            return render_form(self.request, self.form, appstruct)

        elif self.request.method == 'POST':
            controls = self.request.POST.items()

            try:
                captured = validate_form(controls, self.form)
            except FormValidationFailure as e:
                if hasattr(user, 'username'):
                    # We pre-populate username
                    return e.result(self.request, username=user.username)
                else:
                    return e.result(self.request)

            changed = False
            email = captured.get('email', None)
            if email:
                email_user = self.User.get_by_email(self.request, email)
                if email_user and email_user.id != user.id:
                    FlashMessage(self.request,
                                 _('That e-mail is already used.'),
                                 kind='error')
                    return HTTPFound(location=self.request.url)
                if email != user.email:
                    user.email = email
                    changed = True

            password = captured.get('password')
            if password:
                user.password = password
                changed = True

            if changed:
                FlashMessage(self.request, self.Str.edit_profile_done,
                             kind='success')
                self.request.registry.notify(
                    ProfileUpdatedEvent(self.request, user, captured)
                )
            return HTTPFound(location=self.request.url)
