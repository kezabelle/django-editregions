# -*- coding: utf-8 -*-
from distutils.version import LooseVersion
from django import get_version as django_version


def is_django_15plus():
    """
    allows us to apply functionality only in recent versions of Django.

    .. testcase:: VersionsTestCase
    """
    return LooseVersion(django_version()) >= LooseVersion('1.5')


def is_django_16plus():
    """
    allows us to apply functionality only in recent versions of Django.

    .. testcase:: VersionsTestCase
    """
    return LooseVersion(django_version()) >= LooseVersion('1.6')


def is_django_17plus():
    """
    allows us to apply functionality only in recent versions of Django.

    .. testcase:: VersionsTestCase
    """
    return LooseVersion(django_version()) >= LooseVersion('1.7')
