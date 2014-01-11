# -*- coding: utf-8 -*-
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = (
    # dependencies
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'adminlinks',
    'helpfulfields',
    # main app in test
    'editregions',
)

SOUTH_TESTS_MIGRATE = False # To disable migrations and use syncdb instead
SKIP_SOUTH_TESTS = True # To disable South's own unit tests

BASE_DIR = os.path.realpath(os.path.dirname(__file__))

TEMPLATE_DIRS = (
    os.path.realpath(os.path.join(BASE_DIR, 'editregions', 'tests', 'templates')),
)
