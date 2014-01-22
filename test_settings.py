# -*- coding: utf-8 -*-
import os

ROOT_URLCONF = 'test_urls'

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
    'editregions.contrib.embeds',
    'editregions.contrib.search',
    'editregions.contrib.text',
    'editregions.contrib.uploads',
)

SOUTH_TESTS_MIGRATE = False # To disable migrations and use syncdb instead
SKIP_SOUTH_TESTS = True # To disable South's own unit tests

BASE_DIR = os.path.realpath(os.path.dirname(__file__))

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.request",
    "django.core.context_processors.csrf",
)

TEMPLATE_DIRS = (
    os.path.realpath(os.path.join(BASE_DIR, 'editregions', 'tests', 'templates')),
)

STATICFILES_DIRS = (
    os.path.realpath(os.path.join(BASE_DIR, 'editregions', 'tests', 'static')),

)

# Use a fast hasher to speed up tests.
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

HAYSTACK_CONNECTIONS={
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'whoosh_index'),
        'TITLE': 'testing',
    },
}
