# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.schemas          import LoginSchema
from horus.schemas          import RegisterSchema
from horus.schemas          import ForgotPasswordSchema
from horus.schemas          import ResetPasswordSchema
from horus.schemas          import ProfileSchema
from horus.forms            import SubmitForm
from horus.resources        import RootFactory
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
from horus.lib              import get_user
from hem.config             import get_class_from_config


def groupfinder(userid, request):
    user = request.user
    groups = None
    if user:
        groups = []
        for group in user.groups:
            groups.append('group:%s' % group.name)
        groups.append('user:%s' % user.pk)
    return groups


def includeme(config):
    settings = config.registry.settings
    # str('user') returns a bytestring under Python 2 and a
    # unicode string under Python 3, which is what we need:
    config.set_request_property(get_user, str('user'), reify=True)
    config.set_root_factory(RootFactory)
    if not config.registry.queryUtility(IHorusUserClass):
        user_class = get_class_from_config(settings, 'horus.user_class')
        config.registry.registerUtility(user_class, IHorusUserClass)
    if not config.registry.queryUtility(IHorusActivationClass):
        activation_class = get_class_from_config(settings,
                'horus.activation_class')
        config.registry.registerUtility(activation_class,
                IHorusActivationClass)
    schemas = [
        (IHorusLoginSchema, LoginSchema),
        (IHorusRegisterSchema, RegisterSchema),
        (IHorusForgotPasswordSchema, ForgotPasswordSchema),
        (IHorusResetPasswordSchema, ResetPasswordSchema),
        (IHorusProfileSchema, ProfileSchema)
    ]
    forms = [
        IHorusLoginForm, IHorusRegisterForm, IHorusForgotPasswordForm,
        IHorusResetPasswordForm, IHorusProfileForm
    ]
    for iface, schema in schemas:
        if not config.registry.queryUtility(iface):
            config.registry.registerUtility(schema, iface)
    for form in forms:
        if not config.registry.queryUtility(form):
            config.registry.registerUtility(SubmitForm, form)
    config.include('horus.routes')
    config.scan(ignore=str('horus.tests'))
