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

requires = [
    'sqlalchemy',
    'zope.sqlalchemy',
    'transaction',
    'cryptacular',
    'deform',
    'pystache',
    'hem',
    'beaker',
    'pyramid',
    'pyramid_mailer',
    'pyramid_beaker',
    'pyramid_deform',
    'bag>=0.3.3',
]

setup(name='horus',
    version='0.9.14dev',
    description='Generic user registration for pyramid',
    long_description=README + '\n\n' + CHANGES,
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
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
    tests_require=requires + ['pytest', 'mock', 'webtest', 'pytest-cov',
        'psycopg2'],
    cmdclass={'test': PyTest},
    test_suite='horus',
)
