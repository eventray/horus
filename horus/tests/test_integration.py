# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.tests import IntegrationTestBase
from pyramid import testing
from mock import patch
from mock import Mock


class TestViews(IntegrationTestBase):
    def test_index(self):
        """ Call the index view, make sure routes are working """
        res = self.app.get('/')
        assert res.status_int == 200

    def test_get_register(self):
        """ Call the register view, make sure routes are working """
        res = self.app.get('/register')
        assert res.status_int == 200

    def test_get_login(self):
        """ Call the login view, make sure routes are working """
        res = self.app.get('/login')
        self.assertEqual(res.status_int, 200)

    def test_login_redirects_if_logged_in(self):
        request = testing.DummyRequest()
        from horus.views import AuthController
        with patch.object(AuthController, 'request', request) as request:
            request.user = Mock()
            res = self.app.get('/login').follow()
            #TODO: Patch index request as well so that it redirects to dashboard
            assert b'index' in res.body

    def test_empty_login(self):
        """ Empty login fails """
        res = self.app.post(str('/login'), {'submit': True})

        assert b"There was a problem with your submission" in res.body
        assert b"Required" in res.body
        assert res.status_int == 200

    def test_valid_login(self):
        """ Call the login view, make sure routes are working """
        from horus.tests.models import User
        admin = User(user_name='sontek', email='sontek@gmail.com')
        admin.set_password('temp')
        self.session.add(admin)
        self.session.flush()

        res = self.app.get('/login')

        csrf = res.form.fields['csrf_token'][0].value

        res = self.app.post(str('/login'),
            {
                'submit': True,
                'User_name': 'sontek',
                'Password': 'temp',
                'csrf_token': csrf
            }
        )

        assert res.status_int == 302

    def test_inactive_login(self):
        """Make sure inactive users can't sign in."""
        from horus.tests.models import User
        from horus.tests.models import Activation
        admin = User(user_name='sontek', email='sontek@gmail.com')
        admin.activation = Activation()
        admin.set_password('temp')
        self.session.add(admin)
        self.session.flush()

        res = self.app.get('/login')

        csrf = res.form.fields['csrf_token'][0].value

        res = self.app.post(str('/login'),
            {
                'submit': True,
                'User_name': 'sontek',
                'Password': 'temp',
                'csrf_token': csrf
            }
        )

        assert b'Your account is not active, please check your e-mail.' \
            in res.body
