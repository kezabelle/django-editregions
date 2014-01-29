#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from setuptools.command.test import test
#from setuptest import test

HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, 'README.rst'), mode='r') as f:
    README = f.read()

setup(
    name="django-editregions",
    version="0.1.0",
    packages=find_packages(),
    tests_require=(
        'django-setuptest',
    ),
    #test_suite='runtests.runtests',
    test_suite='setuptest.setuptest.SetupTestSuite',
    #cmdclass={'test': lazy_test_cmd},
    author="Keryn Knight",
    author_email='python-package@kerynknight.com',
    description="",
    long_description=README,
    keywords="django editable regions",
    license="BSD License",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Text Processing :: Markup :: HTML',
        'License :: OSI Approved :: BSD License',
    ],
    platforms=['OS Independent'],
)
