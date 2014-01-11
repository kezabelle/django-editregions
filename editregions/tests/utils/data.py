# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.test.utils import override_settings
from django.utils.functional import SimpleLazyObject
from django.utils.unittest import TestCase
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User, Permission
from editregions.models import EditRegionConfiguration
from editregions.utils.data import get_content_type, get_model_class, get_modeladmin, attach_configuration, get_configuration


class GetContentTypeTestCase(DjangoTestCase):
    def setUp(self):
        self.user_ct = ContentType.objects.get_for_model(User)
        self.test_func = get_content_type

    def test_get_for_model_class(self):
        self.assertEqual(self.user_ct, self.test_func(User))

    def test_get_for_model_instance(self):
        self.assertEqual(self.user_ct, self.test_func(User()))

    def test_get_by_natural_key_string(self):
        self.assertEqual(self.user_ct, self.test_func('auth.User'))
        self.assertEqual(self.user_ct, self.test_func('auth.user'))

    def test_get_by_id(self):
        ct = ContentType.objects.get(app_label='auth', model='user')
        self.assertEqual(self.user_ct, self.test_func(ct.pk))

    def test_get_by_natural_key_invalid(self):
        with self.assertRaises(ContentType.DoesNotExist):
            self.test_func('x.Y')


class GetModelClassTestCase(GetContentTypeTestCase):
    def setUp(self):
        self.user_ct = User
        self.test_func = get_model_class


class GetModelAdminTestCase(GetContentTypeTestCase):
    def setUp(self):
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, UserAdmin)
        self.test_func = get_modeladmin
        self.user_ct = admin.site._registry[User]

    @override_settings(DEBUG=True)
    def test_class_not_in_admin(self):
        with self.assertRaises(ImproperlyConfigured): 
            get_modeladmin(Permission)

    @override_settings(DEBUG=False)
    def test_class_not_in_admin(self):
        with self.assertRaises(KeyError):
            get_modeladmin(Permission)


class AttachConfigurationTestCase(TestCase):
    def test_attaching(self):
        user = User()
        obj, created = attach_configuration(user, EditRegionConfiguration)
        self.assertTrue(hasattr(user, '__editregion_config'))
        self.assertTrue(created)
        self.assertIsInstance(getattr(user, '__editregion_config'),
                              SimpleLazyObject)

    def test_reattaching(self):
        user = User()
        obj, created1 = attach_configuration(user, EditRegionConfiguration)
        obj, created2 = attach_configuration(user, EditRegionConfiguration)
        self.assertTrue(hasattr(user, '__editregion_config'))
        self.assertFalse(created2)


class GetConfigurationTestCase(TestCase):
    def test_getting(self):
        user = User()
        obj, created = attach_configuration(user, EditRegionConfiguration)
        self.assertIsInstance(get_configuration(user), SimpleLazyObject)

    def test_getting_without_having_attached(self):
        user = User()
        self.assertNotIsInstance(get_configuration(user), SimpleLazyObject)
        self.assertIsNone(get_configuration(user))
