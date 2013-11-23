# -*- coding: utf-8 -*-
from distutils.version import LooseVersion
from django import get_version as django_version


def is_django_15plus():
    return LooseVersion(django_version()) >= LooseVersion('1.5')


def is_django_16plus():
    return LooseVersion(django_version()) >= LooseVersion('1.6')