Introduction to *horus*
~~~~~~~~~~~~~~~~~~~~~~~

*horus* provides generic user registration for the Pyramid web framework,
if your web app uses sqlalchemy.

It is a pluggable web application that provides user registration,
login, logout and change password functionality. *horus* follows a policy of
minimal interference, so your app can mostly keep its existing models.


Minimal integration
===================

- Create a virtualenv and activate it. Install pyramid and create
  your pyramid project.

- Edit your *setup.py* to add "horus" to the dependencies in the
  *install_requires* list.

- Run ``python setup.py develop`` on your project to install all dependencies
  into your virtualenv.

- Create your SQLAlchemy declarative initialization.

- Create models inheriting from horus' abstract models. Find an example in the
  file `horus/tests/models.py
  <https://github.com/eventray/horus/blob/master/horus/tests/models.py>`_.

  Alternatively, use the horus scaffold script::

    horus_scaffold development.ini > your_app/auth_models.py

  Then all you need to do is tell the class where to find your declarative
  base you and are good to go!

- Include horus inside your ``main()`` function like this::

    # Tell horus which SQLAlchemy scoped session to use:
    from hem.interfaces import IDBSession
    registry = config.registry
    registry.registerUtility(my_sqlalchemy_scoped_session, IDBSession)

    config.include('horus')
    config.scan_horus(auth_models_package_or_module)

  With the above ``config.scan_horus()`` call, you need to edit your .ini
  configuration file and tell horus which model classes to use like this:

      horus.user_class = my_app.models:User
      horus.activation_class = my_app.models:Activation

  As an alternative to ``config.scan_horus()`` plus that configuration,
  you can register the classes explicitly if you so prefer. This must be
  done above ``config.include('horus')``::

    # Tell horus which models to use:
    from horus.interfaces import IUserClass, IActivationClass
    registry.registerUtility(User, IUserClass)
    registry.registerUtility(Activation, IActivationClass)

    config.include('horus')

- Configure ``horus.login_redirect`` and ``horus.logout_redirect``
  (in your .ini configuration file) to set the redirection routes.

- If you haven't done so yet, configure an HTTP session factory according to
  the Sessions chapter of the Pyramid documentation.

- Create your database and tables. Maybe even an initial user.

- Be sure to pass an ``authentication_policy`` argument in the
  ``config = Configurator(...)`` call. Refer to Pyramid docs for details.

- By now the login form should appear at /login, but /register shouldn't.

- Include the package pyramid_mailer for the validation e-mail and
  "forgot password" e-mail::

    config.include('pyramid_mailer')

- The /register form should appear, though ugly. Now you have a choice
  regarding user activation by email:

  - You may just disable it by setting, in your .ini file::

        horus.require_activation = False

  - Otherwise, configure pyramid_mailer `according to its documentation
    <http://docs.pylonsproject.org/projects/pyramid_mailer/en/latest/>`_
    and test the registration page.

- If you are using pyramid_tm or the ZopeTransactionManager, your minimal
  integration is done. (The pages are ugly, but working. Keep reading...)


Need to session.commit()?
=========================

*horus* does not require pyramid_tm or the ZopeTransactionManager with your
session but if you do not use them you do have to take one extra step.
We don't commit transactions for you because that just wouldn't be nice!

All you have to do is subscribe to the extension events and
commit the session yourself. This also gives you the chance to
do some extra processing::

    from horus.events import (
        PasswordResetEvent, NewRegistrationEvent,
        RegistrationActivatedEvent, ProfileUpdatedEvent)

    def handle_request(event):
        request = event.request
        session = request.registry.getUtility(IDBSession)
        session.commit()

    self.config.add_subscriber(handle_request, PasswordResetEvent)
    self.config.add_subscriber(handle_request, NewRegistrationEvent)
    self.config.add_subscriber(handle_request, RegistrationActivatedEvent)
    self.config.add_subscriber(handle_request, ProfileUpdatedEvent)


Whether or not to have a "username" field
=========================================

It is important that you analyze the characteristics of your web application and decide whether you need a ``username`` field for users to log in with. horus provides 2 modes of operation:

- **email + username:** The user chooses a username when registering and later she can log in by providing either the username or the email address. Therefore, usernames may NOT contain the @ character. **This mode is the default.** It is expressed by the configuration setting ``horus.handle = usermail``
- **email only:** There is no ``username`` field and users only provide their email address. You enable this mode by:
    - Making your User model subclass NoUsernameMixin instead of UsernameMixin;
    - Adding this configuration setting: ``horus.handle = email``, which will make horus default to schemas that contain email fields instead of username fields.

If you make this change and want to keep your data you must deal with the existing (or missing) "username" column yourself.


Changing the forms
==================

If you would like to modify any of the forms, you just need
to register the new deform class to be used.

The interfaces you have available to override from horus.interfaces are:

- IHorusLoginForm
- IHorusRegisterForm
- IHorusForgotPasswordForm
- IHorusResetPasswordForm
- IHorusProfileForm

This is how you would do it (*MyForm* being a custom deform Form class)::

    config.registry.registerUtility(MyForm, IHorusLoginForm)


Changing the templates
======================

If you would like to substitute the templates you can use pyramid's
`override_asset <http://pyramid.readthedocs.org/en/latest/narr/assets.html#overriding-assets-section>`_::

    config.override_asset(to_override='horus:templates/template.mako',
        override_with='your_package:templates/anothertemplate.mako')

The templates you have available to override are:

- login.mako
- register.mako
- forgot_password.mako
- reset_password.mako
- profile.mako

If you would like to override the templates with Jinja2, or any other
templating language, just override the view configuration::

    config.add_view('horus.views.AuthController', attr='login',
        route_name='login', renderer='yourapp:templates/login.jinja2')
    config.add_view('horus.views.ForgotPasswordController',
        attr='forgot_password', route_name='forgot_password',
        renderer='yourapp:templates/forgot_password.jinja2')
    config.add_view('horus.views.ForgotPasswordController',
        attr='reset_password', route_name='reset_password',
        renderer='yourapp:templates/reset_password.jinja2')
    config.add_view('horus.views.RegisterController', attr='register',
        route_name='register', renderer='yourapp:templates/register.jinja2')
    config.add_view('horus.views.ProfileController', attr='profile',
        route_name='profile', renderer='yourapp:templates/profile.jinja2')


Changing strings
================

Take a look at `this class
<https://github.com/eventray/horus/blob/master/horus/strings.py>`_.
This is where we store all the strings in horus.
If you'd like to change one or two messages, simply subclass this, then do::

    from horus.interfaces import IUIStrings
    config.registry.registerUtility(MyStringsClass, IUIStrings)


Changing the primary key column name
====================================

If you wish to override the primary key attribute name, you can do so
by creating a new mixin class::

    class NullPkMixin(Base):
        abstract = True
        _idAttribute = 'pk'

        @declared_attr
        def pk(self):
            return Base.pk

        @declared_attr
        def id(self):
            return None

    class User(NullPkMixin, UserMixin):
        pass


horus development
=================

See https://github.com/eventray/horus

If you would like to help make any changes to horus, you can run its
unit tests with py.test:

    py.test

To check test coverage::

    py.test --cov-report term-missing --cov horus

The tests can also be run in parallel::

    py.test -n4

We are using this build server: http://travis-ci.org/#!/eventray/horus
