Horus step-by-step integration checklist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*Horus* is a Pyramid web application that provides user registration,
login, logout and change password functionality. You can easily plug it
into your own Pyramid web app. Here is how.

Minimal integration
===================

- Create a virtualenv and activate it. Install pyramid and create
  a new pyramid project.

- Edit your *setup.py* to add "horus" to the dependencies in the
  *install_requires* list.

- Run ``python setup.py develop`` on your project to install all dependencies
  into your virtualenv.

- Create your SQLAlchemy declarative initialization.

- Create models inheriting from horus' abstract models. Find an example in the
  file `horus/tests/models.py
  <https://github.com/eventray/horus/blob/master/horus/tests/models.py>`_.

- Include horus inside your ``main()`` function like this::

    # Include horus
    from hem.interfaces import IDBSession
    from horus.interfaces import IHorusUserClass, IHorusActivationClass
    # Tell horus which SQLAlchemy session to use:
    registry.registerUtility(my_sqlalchemy_scoped_session, IDBSession)
    registry.registerUtility(User, IHorusUserClass)
    registry.registerUtility(Activation, IHorusActivationClass)
    config.include('horus')

- Create tables. Maybe even run the console script to set up the database:

    $ su_setup <your app config.ini>

- Either configure ``horus.login_redirect`` and ``horus.logout_redirect``
  (in your .ini configuration file) to set the redirection routes or,
  easier even, just declare an *index* route like this::

    config.add_route('index', '/')

- By now the login form should appear at /login, but /register shouldn't.

- Include the package pyramid_mailer for the validation e-mail and
  "forgot password" e-mail::

    config.include('pyramid_mailer')

- The /register form should appear, though ugly. Now you have a choice
  regarding user activation by email:

  - You may just disable it by setting, in your .ini file:

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

    from horus.events import (PasswordResetEvent, NewRegistrationEvent,
        RegistrationActivatedEvent, ProfileUpdatedEvent)

    def handle_request(event):
        request = event.request
        session = request.registry.getUtility(IDBSession)
        session.commit()

    self.config.add_subscriber(handle_request, PasswordResetEvent)
    self.config.add_subscriber(handle_request, NewRegistrationEvent)
    self.config.add_subscriber(handle_request, RegistrationActivatedEvent)
    self.config.add_subscriber(handle_request, ProfileUpdatedEvent)

Changing the forms
==================

If you would like to modify any of the forms in pyramid signup, you just need
to register the new deform class to use in the registry.

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

horus development
=================

If you would like to help make any changes to horus, you can run its
unit tests with py.test:

    $ py.test

To check test coverage:

    $ py.test --cov-report term-missing --cov horus

The tests can also be run in parallel:

    $ py.test -n4

We are using this build server: http://travis-ci.org/#!/eventray/horus
