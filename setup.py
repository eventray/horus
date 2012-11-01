#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division, print_function,
    unicode_literals)
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        result = pytest.main(self.test_args)
        sys.exit(result)

here = os.path.abspath(os.path.dirname(__file__))
README = ''  # open(os.path.join(here, 'README.md')).read()
CHANGES = ''  # open(os.path.join(here, 'CHANGES.txt')).read()

requires = 'pyramid sqlalchemy cryptacular deform pyramid_deform ' \
    'transaction zope.sqlalchemy pystache pyramid_mailer hem ' \
    'beaker pyramid_beaker'.split()

setup(name='horus',
    version='0.9.9',
    description='Generic user registration for pyramid',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    author='John Anderson',
    author_email='sontek@gmail.com',
    url='https://github.com/sontek/horus',
    keywords='pyramid',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=requires,
    tests_require=requires + ['pytest', 'mock', 'webtest', 'pytest-cov'],
    cmdclass={'test': PyTest},
    test_suite='horus',
    dependency_links=[
        'https://github.com/eventray/hem/tarball/master#egg=hem-dev',
    ]
)
