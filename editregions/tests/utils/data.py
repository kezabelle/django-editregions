# -*- coding: utf-8 -*-
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User
from editregions.utils.data import get_content_type


class GetContentTypeTestCase(DjangoTestCase):
    def setUp(self):
        self.user_ct = ContentType.objects.get_for_model(User)

    def test_get_for_model_class(self):
        self.assertEqual(self.user_ct, get_content_type(User))

    def test_get_for_model_instance(self):
        self.assertEqual(self.user_ct, get_content_type(User()))

    def test_get_by_natural_key_string(self):
        self.assertEqual(self.user_ct, get_content_type('auth.User'))
        self.assertEqual(self.user_ct, get_content_type('auth.user'))

    def test_get_by_id(self):
        ct = ContentType.objects.get(app_label='auth', model='user')
        self.assertEqual(self.user_ct, get_content_type(ct.pk))

    def test_get_by_natural_key_invalid(self):
        with self.assertRaises(ContentType.DoesNotExist):
            get_content_type('x.Y')
