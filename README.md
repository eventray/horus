Getting Started
===============

First, install the project and its dependencies:

>  $ python setup.py develop

Next, run our console script to set up the database:

> $ su_setup <your app config.ini>

Finally, to include horus in your project, in your apps configuration,
you should include the package pyramid_mailer for the validation e-mail and
"forgot password" e-mail and tell horus which session to use for
the database objects.

``` python
 config.include('pyramid_mailer')
 from hem.interfaces import IDBSession
 config.registry.registerUtility(DBSession, IDBSession)
 config.include('horus')
 ```

horus does not require pyramid_tm or the ZopeTransactionManager with your
session but if you do not use them you do have to take one extra step.
We don't commit transactions for you because that just wouldn't be nice!

All you have to do is to subscribe to the extension events and
commit the session yourself. This also gives you the chance to
do some extra processing:

``` python
from horus.events import PasswordResetEvent
from horus.events import NewRegistrationEvent
from horus.events import RegistrationActivatedEvent
from horus.events import ProfileUpdatedEvent

def handle_request(event):
  request = event.request
  session = request.registry.getUtility(IDBSession)
  session.commit()

self.config.add_subscriber(handle_request, PasswordResetEvent)
self.config.add_subscriber(handle_request, NewRegistrationEvent)
self.config.add_subscriber(handle_request, RegistrationActivatedEvent)
self.config.add_subscriber(handle_request, ProfileUpdatedEvent)
```

Extending horus
===============

If you would like to modify any of the forms in pyramid signup, you just need
to register the new deform class to use in the registry.

The interfaces you have available to override from horus.interfaces are:

>  IHorusLoginForm
>
>  IHorusRegisterForm
>
>  IHorusForgotPasswordForm
>
>  IHorusResetPasswordForm
>
>  IHorusProfileForm
>

This is how you would do it (uniform being a custom deform Form class):

>  config.registry.registerUtility(UNIForm, IHorusLoginForm)
>

If you would like to override the templates you can use pyramid's
override asset functionality:

>    config.override_asset(to_override='horus:templates/template.mako', override_with='your_package:templates/anothertemplate.mako')

The templates you have available to override are:

>  login.mako
>
>  register.mako
>
>  forgot_password.mako
>
>  reset_password.mako
>
>  profile.mako

If you would like to override the templates with Jinja2, you just have to
override the view configuration:

``` python

config.add_view('horus.views.AuthController', attr='login', route_name='login',
    renderer='yourapp:templates/login.jinja2')
config.add_view('horus.views.ForgotPasswordController', attr='forgot_password',
    route_name='forgot_password', renderer='yourapp:templates/forgot_password.jinja2')
config.add_view('horus.views.ForgotPasswordController', attr='reset_password',
    route_name='reset_password', renderer='yourapp:templates/reset_password.jinja2')
config.add_view('horus.views.RegisterController', attr='register',
    route_name='register', renderer='yourapp:templates/register.jinja2')
config.add_view('horus.views.ProfileController', attr='profile',
    route_name='profile', renderer='yourapp:templates/profile.jinja2')

```

Development
===========

If you would like to help make any changes to horus, you can run its
unit tests with py.test:

> $ py.test

and to check test coverage:

> $ py.test --cov-report term-missing --cov horus

you can also run the tests in parallel:

> $ py.test -n4


Build Server: http://travis-ci.org/#!/eventray/horus
