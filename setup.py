#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages
import warnings
#warnings.resetwarnings()
#warnings.simplefilter('error')
warnings.filterwarnings("ignore", '.+', PendingDeprecationWarning,
                                'django\.test\..*')
warnings.filterwarnings("ignore", '.+', PendingDeprecationWarning,
                                'django\.template\.base')
try:
    from setuptest import test
    test_config = {
        'cmdclass': {'test': test}
    }
except ImportError:
    test_config = {
    'tests_require': (
        'django-setuptest',
        ),
    'test_suite': 'setuptest.setuptest.SetupTestSuite'
    }
    for argument in ('--failfast', '--autoreload', '--label'):
        if argument in sys.argv:
            sys.argv.remove(argument)


HERE = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(HERE, 'README.rst'), mode='r') as f:
    README = f.read()


with open(os.path.join(HERE, 'LICENSE'), mode='r') as f:
    LICENSE = f.read()


with open(os.path.join(HERE, 'CHANGELOG'), mode='r') as f:
    CHANGELOG = f.read()


with open(os.path.join(HERE, 'CONTRIBUTORS'), mode='r') as f:
    CONTRIBUTORS = f.read()

TRANSITION = "\r\n\r\n----\r\n\r\n"

LONG_DESCRIPTION = (README + TRANSITION + CHANGELOG + TRANSITION + LICENSE +
                    TRANSITION + CONTRIBUTORS)

setup(
    name="django-editregions",
    version="0.1.0",
    packages=find_packages(),
    author="Keryn Knight",
    author_email='python-package@kerynknight.com',
    description="",
    long_description=LONG_DESCRIPTION,
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
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Natural Language :: English',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
        'Topic :: Text Processing :: Markup :: HTML',
        'License :: OSI Approved :: BSD License',
    ],
    platforms=['OS Independent'],
    **test_config
)
