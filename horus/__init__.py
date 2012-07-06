from horus.schemas      import LoginSchema
from horus.schemas      import RegisterSchema
from horus.schemas      import ForgotPasswordSchema
from horus.schemas      import ResetPasswordSchema
from horus.schemas      import ProfileSchema
from horus.forms        import SubmitForm
from horus.resources    import RootFactory
from horus.interfaces   import IHorusUserClass, IHorusUserAccountClass
from horus.interfaces   import IHorusActivationClass
from horus.interfaces   import IHorusLoginForm
from horus.interfaces   import IHorusLoginSchema
from horus.interfaces   import IHorusRegisterForm
from horus.interfaces   import IHorusRegisterSchema
from horus.interfaces   import IHorusForgotPasswordForm
from horus.interfaces   import IHorusForgotPasswordSchema
from horus.interfaces   import IHorusResetPasswordForm
from horus.interfaces   import IHorusResetPasswordSchema
from horus.interfaces   import IHorusProfileForm
from horus.interfaces   import IHorusProfileSchema
from horus.routes       import build_routes
from horus.lib          import get_user_account
from horus.lib          import get_class_from_config

def groupfinder(userid, request):
    user_account = request.user_account
    #user_account = get_user_account(request, userid)
    groups = []

    if user_account:
        request.user_account = user_account
        for group in user_account.user.groups:
            groups.append('group:%s' % group.name)

        groups.append('useraccount:%s' % user_account.id)

    return groups

def includeme(config):
    settings = config.registry.settings
    config.set_request_property(get_user_account, 'user_account', reify=True)

    config.set_root_factory(RootFactory)


    if not config.registry.queryUtility(IHorusUserClass):
        user_class = get_class_from_config(settings, 'horus.user_class')
        config.registry.registerUtility(user_class, IHorusUserClass)

    if not config.registry.queryUtility(IHorusUserAccountClass):
        user_account_class = get_class_from_config(settings, 'horus.user_account_class')
        config.registry.registerUtility(user_account_class, IHorusUserAccountClass)

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

    config.include(build_routes)
    config.scan('horus')
