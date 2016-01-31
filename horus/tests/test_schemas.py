# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
from horus.tests import UnitTestBase
from horus.schemas import UsernameLoginSchema, UsernameRegisterSchema
from colander import Invalid


class TestSchemas(UnitTestBase):
    def test_valid_login_schema(self):
        request = self.get_csrf_request(post={
            'handle': 'sontek',
            'password': 'password',
            })
        schema = UsernameLoginSchema().bind(request=request)

        result = schema.deserialize(request.POST)

        assert result['handle'] == 'sontek'
        assert result['password'] == 'password'
        assert result['csrf_token'] is not None

    def test_invalid_login_schema(self):
        request = self.get_csrf_request()
        schema = UsernameLoginSchema().bind(request=request)

        def deserialize_empty():
            try:
                schema.deserialize({})
            except Invalid as exc:
                assert len(exc.children) == 3
                errors = ['csrf_token', 'handle', 'password']
                for child in exc.children:
                    assert child.node.name in errors
                    assert child.msg == 'Required'
                raise
        self.assertRaises(Invalid, deserialize_empty)

    def test_usernames_may_not_contain_at(self):
        POST = dict(username='bru@haha', email='bru@haha.com', password='pass')
        request = self.get_csrf_request(post=POST)
        schema = UsernameRegisterSchema().bind(request=request)

        def run():
            try:
                schema.deserialize(POST)
            except Invalid as exc:
                assert len(exc.children) == 1
                the_error = exc.children[0]
                assert the_error.node.name == 'username'
                assert the_error.msg == ['May not contain this character: @']
                raise
        self.assertRaises(Invalid, run)
