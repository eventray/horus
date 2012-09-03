# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
from horus.tests import UnitTestBase


class TestInterfaces(UnitTestBase):
    def test_suloginschema(self):
        """ Shouldn't be able to instantiate the interface """
        from horus.interfaces import IHorusLoginSchema

        def make_session():
            IHorusLoginSchema('1')

        self.assertRaises(TypeError, make_session)

    def test_suloginform(self):
        """ Shouldn't be able to instantiate the interface """
        from horus.interfaces import IHorusLoginForm

        def make_session():
            IHorusLoginForm('1')

        self.assertRaises(TypeError, make_session)
