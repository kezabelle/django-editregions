#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from setuptools import setup, find_packages
from setuptest import test

HERE = os.path.abspath(os.path.dirname(__file__))

setup(
    name="django-editregions",
    version="0.1.0",
    packages=find_packages(),
    #tests_require=(
    #    'django-setuptest',
    #),
    #test_suite='setuptest.setuptest.SetupTestSuite',
    cmdclass={'test': test},
    author="Keryn Knight",
    author_email='python-package@kerynknight.com',
    description="",
    long_description=open(os.path.join(HERE, 'README.rst')).read(),
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
