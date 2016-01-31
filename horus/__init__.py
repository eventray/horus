# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import inspect
from hem.config import get_class_from_config
from pyramid.events import BeforeRender
from pyramid.path import DottedNameResolver
from .schemas import (
    ForgotPasswordSchema, UsernameLoginSchema, UsernameRegisterSchema,
    UsernameResetPasswordSchema, UsernameProfileSchema, EmailLoginSchema,
    EmailRegisterSchema, EmailResetPasswordSchema, EmailProfileSchema)
from .forms import SubmitForm
from .resources import RootFactory
from .interfaces import (
    IUIStrings, IUserClass, IActivationClass, ILoginForm, ILoginSchema,
    IRegisterForm, IRegisterSchema, IForgotPasswordForm, IForgotPasswordSchema,
    IResetPasswordForm, IResetPasswordSchema, IProfileForm, IProfileSchema)
from .lib import get_user, render_flash_messages_from_queues
from . import models
from .strings import UIStringsBase


def groupfinder(userid, request):
    user = request.user
    groups = None
    if user:
        groups = []
        for group in user.groups:
            groups.append('group:%s' % group.name)
        groups.append('user:%s' % user.id_value)
    return groups


def scan(config, module):
    r = DottedNameResolver()
    module = r.maybe_resolve(module)
    module = inspect.getmodule(module)

    model_mappings = {
        models.UserMixin: IUserClass,
        models.ActivationMixin: IActivationClass,
    }

    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj):
            # don't register the horus mixins
            if obj.__module__ == 'horus.models':
                continue

            for mixin, interface in model_mappings.items():
                if isinstance(obj, type) and issubclass(obj, mixin):
                    config.registry.registerUtility(obj, interface)


class BaseStrategy(object):
    defaults = [
        (IUIStrings, UIStringsBase),
        (IForgotPasswordSchema, ForgotPasswordSchema),
    ]

    @classmethod
    def set_up(cls, config):
        for iface, default in cls.defaults:
            if not config.registry.queryUtility(iface):
                config.registry.registerUtility(default, iface)


class UsernameStrategy(BaseStrategy):
    defaults = BaseStrategy.defaults + [
        (ILoginSchema, UsernameLoginSchema),
        (IRegisterSchema, UsernameRegisterSchema),
        (IResetPasswordSchema, UsernameResetPasswordSchema),
        (IProfileSchema, UsernameProfileSchema)
    ]


class EmailStrategy(BaseStrategy):
    defaults = BaseStrategy.defaults + [
        (ILoginSchema, EmailLoginSchema),
        (IRegisterSchema, EmailRegisterSchema),
        (IResetPasswordSchema, EmailResetPasswordSchema),
        (IProfileSchema, EmailProfileSchema)
    ]


def includeme(config):
    settings = config.registry.settings
    # str('user') returns a bytestring under Python 2 and a
    # unicode string under Python 3, which is what we need:
    config.add_request_method(get_user, str('user'), reify=True)
    config.set_root_factory(RootFactory)

    config.add_directive('scan_horus', scan)

    if not config.registry.queryUtility(IUserClass):
        try:
            user_class = get_class_from_config(settings, 'horus.user_class')
            config.registry.registerUtility(user_class, IUserClass)
        except:
            # maybe they are using scan?
            pass

    if not config.registry.queryUtility(IActivationClass):
        try:
            activation_class = get_class_from_config(settings,
                                                     'horus.activation_class')
            config.registry.registerUtility(activation_class,
                                            IActivationClass)
        except:
            # maybe they are using scan?
            pass

    # SubmitForm is the default for all our forms
    for form in (ILoginForm, IRegisterForm, IForgotPasswordForm,
                 IResetPasswordForm, IProfileForm):
        if not config.registry.queryUtility(form):
            config.registry.registerUtility(SubmitForm, form)

    # Default schemas depend on login handle configuration:
    handle_config = settings.get('horus.handle', 'username')
    if handle_config in ('username', 'username+email', 'email+username'):
        UsernameStrategy.set_up(config)
    elif handle_config == 'email':
        EmailStrategy.set_up(config)
    else:
        raise RuntimeError('Invalid config value for horus.handle: {}'.format(
            handle_config))

    def on_before_render(event):
        fn = render_flash_messages_from_queues
        event['render_flash_messages'] = lambda: fn(event['request'])

    config.add_subscriber(on_before_render, BeforeRender)

    config.include('horus.routes')
    config.scan(ignore=str('horus.tests'))
