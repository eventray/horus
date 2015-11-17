# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.tests import UnitTestBase
from horus.schemas import LoginSchema
from colander import Invalid


class TestSchemas(UnitTestBase):
    def test_valid_login_schema(self):
        request = self.get_csrf_request(post={
            'username': 'sontek',
            'password': 'password',
            })

        schema = LoginSchema().bind(request=request)

        result = schema.deserialize(request.POST)

        assert result['username'] == 'sontek'
        assert result['password'] == 'password'
        assert result['csrf_token'] != None

    def test_invalid_login_schema(self):
        request = self.get_csrf_request()
        schema = LoginSchema().bind(request=request)

        def deserialize_empty():
            try:
                schema.deserialize({})
            except Invalid as exc:
                assert len(exc.children) == 3
                errors = ['csrf_token', 'username', 'password']
                for child in exc.children:
                    assert child.node.name in errors
                    assert child.msg == 'Required'
                raise
        self.assertRaises(Invalid, deserialize_empty)
