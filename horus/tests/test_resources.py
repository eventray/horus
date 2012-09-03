# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from pyramid import testing
from horus.tests import UnitTestBase


class TestResources(UnitTestBase):
    def test_user_factory(self):
        from horus.resources import UserFactory
        from horus.tests.models import User
        from horus.interfaces import IHorusUserClass
        self.config.registry.registerUtility(User, IHorusUserClass)

        user = User(user_name='sontek', email='sontek@gmail.com')
        user.set_password('foo')
        self.session.add(user)
        self.session.commit()

        request = testing.DummyRequest()
        factory = UserFactory(request)

        fact_user = factory[user.pk]

        assert factory.request == request
        assert user == fact_user
