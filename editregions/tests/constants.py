# -*- coding: utf-8 -*-
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from editregions.constants import (REQUEST_VAR_ID, REQUEST_VAR_REGION,
                                   REQUEST_VAR_CT)


class ConstantsSanityTestCase(TestCase):
    def test_incase_we_try_and_change_them(self):
        self.assertEqual(REQUEST_VAR_REGION, 'region')
        self.assertEqual(REQUEST_VAR_CT, 'content_type')
        self.assertEqual(REQUEST_VAR_ID, 'content_id')
