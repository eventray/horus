# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.tests import IntegrationTestBase
from pyramid import testing
from mock import patch
from mock import Mock
import re
import six


def clean_byte_string(string):
    regex = "^b'(.+)'$"
    match = re.search(regex, string)
    if match:
        return match.group(1)
    return string


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
            # TODO: Patch index request as well so that it redirects to the
            # dashboard
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
        admin = User(username='sontek', email='sontek@gmail.com')
        admin.password = 'temp'
        self.session.add(admin)
        self.session.flush()

        res = self.app.get('/login')

        csrf = res.form.fields['csrf_token'][0].value

        if six.PY3:
            csrf = clean_byte_string(csrf)

        res = self.app.post(
            str('/login'),
            {
                'submit': True,
                'username': 'sontek',
                'password': 'temp',
                'csrf_token': csrf
            }
        )
        assert res.status_int == 302

    def test_inactive_login(self):
        """Make sure inactive users can't sign in."""
        from horus.tests.models import User
        from horus.tests.models import Activation
        admin = User(username='sontek', email='sontek@gmail.com')
        admin.activation = Activation()
        admin.password = 'temp'
        self.session.add(admin)
        self.session.flush()

        res = self.app.get('/login')

        csrf = res.form.fields['csrf_token'][0].value

        if six.PY3:
            csrf = clean_byte_string(csrf)

        res = self.app.post(
            str('/login'),
            {
                'submit': True,
                'username': 'sontek',
                'password': 'temp',
                'csrf_token': csrf
            }
        )

        assert b'Your account is not active, please check your e-mail.' \
            in res.body
