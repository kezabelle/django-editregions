#! /usr/bin/env python
from __future__ import unicode_literals
import os
import sys
from importd import d

HERE = os.path.realpath(os.path.dirname(__file__))
PARENT = os.path.realpath(os.path.dirname(HERE))
sys.path.append(PARENT)

d(
    SITE_ID=1,
    DEBUG=True,
    TEMPLATE_DEBUG=True,
    LANGUAGES=[
        ('en', 'English'),
    ],
    INSTALLED_APPS=[
        "django.contrib.sites",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.staticfiles",
        "django.contrib.messages",
        "django.contrib.admin",
        "adminlinks",
        "editregions",
        "editregions.contrib.embeds",
        "editregions.contrib.text",
        "editregions.contrib.uploads",
        "editregions.contrib.search",
        "test_app",
    ],
    MIDDLEWARE_CLASSES=[
        "django.middleware.common.CommonMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "django.middleware.clickjacking.XFrameOptionsMiddleware",
    ],
    INTERNAL_IPS=[
        "127.0.0.1",
    ],
    TEMPLATE_CONTEXT_PROCESSORS=[
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.core.context_processors.request",
        "django.contrib.auth.context_processors.auth",
    ],
    SESSION_ENGINE="django.contrib.sessions.backends.file",
    STATIC_URL='/s/',
    MEDIA_URL='/m/',
    APPEND_SLASH=True,
    TEMPLATE_LOADERS=(
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    ),
    HAYSTACK_CONNECTIONS={
        'default': {
            'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
            'PATH': os.path.join(HERE, 'whoosh_index'),
            'TITLE': 'testing',
        },
    },
    admin="^admin/",
)

from django.conf.urls.static import static
d.urlpatterns += static(prefix='/m/', show_indexes=True,
                        document_root=d.dotslash('media'))


if __name__ == "__main__":
    d.do("syncdb", "--noinput")
    from django.contrib.auth.models import User
    admin_user, created = User.objects.get_or_create(username="admin",
                                                     is_active=True,
                                                     is_staff=True,
                                                     is_superuser=True)
    admin_user.set_password('admin')
    admin_user.save()
    d.main()
