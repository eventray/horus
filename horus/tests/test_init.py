# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid import testing
from horus.tests import UnitTestBase

from mock import patch
from mock import Mock


class TestInitCase(UnitTestBase):
    def test_root_factory(self):
        from horus import RootFactory
        from pyramid.security import Authenticated
        from pyramid.security import Allow
        from pyramid.security import ALL_PERMISSIONS

        root_factory = RootFactory(testing.DummyRequest())

        assert len(root_factory.__acl__) == 2

        for ace in root_factory.__acl__:
            assert ace[0] == Allow

            if ace[1] == 'group:admin':
                assert ace[2] == ALL_PERMISSIONS
            elif ace[1] == Authenticated:
                assert ace[2] == 'view'

#    def test_request_factory(self):
#        from horus import SignUpRequestFactory
#        from horus.tests.models import User
#
#        user1 = User(username='sontek', email='sontek@gmail.com')
#        user1.password = 'foo'
#        self.session.add(user1)
#        self.session.flush()
#
#        with patch('horus.unauthenticated_userid') as unauth:
#            unauth.return_value = 1
#            request = SignUpRequestFactory({})
#            request.registry = Mock()
#
#            getUtility = Mock()
#            getUtility.return_value = self.session
#
#            request.registry.getUtility = getUtility
#
#            user = request.user
#
#            assert user == user1

    def test_group_finder(self):
        from horus import groupfinder
        from horus.tests.models import User
        from horus.tests.models import Group

        group = Group(name='foo', description='bar')
        user1 = User(username='sontek', email='sontek@gmail.com')
        user1.password = 'foo'
        group.users.append(user1)

        self.session.add(group)
        self.session.add(user1)
        self.session.flush()

        request = Mock()
        request.user = user1

        results = groupfinder(1, request)

        assert 'group:foo' in results
        assert 'user:%s' % (user1.id) in results
        assert len(results) == 2

    def test_group_finder_no_groups(self):
        from horus import groupfinder
        from horus.tests.models import User
        from horus.tests.models import Group

        group = Group(name='foo', description='bar')
        user1 = User(username='sontek', email='sontek@gmail.com')
        user2 = User(username='sontek2', email='sontek2@gmail.com')
        user1.password = 'foo'
        user2.password = 'foo'
        group.users.append(user1)

        self.session.add(group)
        self.session.add(user1)
        self.session.add(user2)
        self.session.flush()

        request = Mock()
        request.user = user2

        results = groupfinder(2, request)

        assert len(results) == 1
        assert 'user:%s' % (user2.id) in results
