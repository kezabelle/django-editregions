# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
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
