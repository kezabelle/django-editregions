# -*- coding: utf-8 -*-
import django
try:
    from unittest.case import TestCase, skipUnless
except ImportError:
    from django.utils.unittest.case import TestCase, skipUnless
from editregions.utils.versioning import (is_django_15plus, is_django_16plus,
                                          is_django_17plus)


class VersionsTestCase(TestCase):

    @skipUnless(django.VERSION >= (1, 5, 0), "test only applies to Django 1.5+")
    def test_is_at_least_15(self):
        self.assertTrue(is_django_15plus())

    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_is_at_least_16(self):
        self.assertTrue(is_django_16plus())

    @skipUnless(django.VERSION >= (1, 7, 0), "test only applies to Django 1.7+")
    def test_is_at_least_17(self):
        self.assertTrue(is_django_17plus())

    @skipUnless(django.VERSION < (1, 5, 0), "test only applies to Django < 1.5")
    def test_is_less_than_15(self):
        self.assertFalse(is_django_15plus())

    @skipUnless(django.VERSION < (1, 5, 0), "test only applies to Django < 1.5")
    def test_is_less_than_16(self):
        self.assertFalse(is_django_16plus())

    @skipUnless(django.VERSION < (1, 5, 0), "test only applies to Django < 1.5")
    def test_is_less_than_17(self):
        self.assertFalse(is_django_17plus())
