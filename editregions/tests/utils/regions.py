# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from editregions.utils.regions import validate_region_name


class ValidateRegionNameTestCase(TestCase):
    def test_ok(self):
        validate_region_name('xyz')

    def test_startswith_underscore(self):
        with self.assertRaisesRegexp(ValidationError, r'Region names may not '
                                                      r'begin with "_"'):
            validate_region_name('_x')

    def test_endswith_underscore(self):
        with self.assertRaisesRegexp(ValidationError, r'Region names may not '
                                                      r'end with "_"'):
            validate_region_name('x_')

    def test_too_long(self):
        with self.assertRaises(ValidationError):
            name = 'x' * 100
            validate_region_name(name)

    def test_bad_regex(self):
        error_str = ('Enter a valid region name consisting of letters, '
                     'numbers, underscores and hyphens.')
        with self.assertRaisesRegexp(ValidationError, error_str):
            name = 'x$y'
            validate_region_name(name)
