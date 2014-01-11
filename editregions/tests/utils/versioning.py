# -*- coding: utf-8 -*-
import django
from django.utils.unittest.case import TestCase, skipUnless
from editregions.utils.versioning import is_django_15plus, is_django_16plus


class VersionsTestCase(TestCase):

    @skipUnless(django.VERSION >= (1, 5, 0), "test only applies to Django 1.5+")
    def test_is_at_least_15(self):
        self.assertTrue(is_django_15plus())

    @skipUnless(django.VERSION >= (1, 6, 0), "test only applies to Django 1.6+")
    def test_is_at_least_16(self):
        self.assertTrue(is_django_16plus())

    @skipUnless(django.VERSION < (1, 5, 0), "test only applies to Django < 1.5")
    def test_is_at_least_15(self):
        self.assertFalse(is_django_15plus())

    @skipUnless(django.VERSION < (1, 5, 0), "test only applies to Django < 1.5")
    def test_is_at_least_16(self): 
        self.assertFalse(is_django_16plus())
