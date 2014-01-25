# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.test.utils import override_settings
from django.utils.functional import SimpleLazyObject
from django.utils.unittest import TestCase
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User, Permission
from editregions.models import EditRegionConfiguration
from editregions.utils.data import get_content_type, get_model_class, get_modeladmin, attach_configuration, get_configuration, healed_context
from editregions.utils.versioning import is_django_15plus


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
    def test_class_not_in_admin_debug(self):
        with self.assertRaises(ImproperlyConfigured):
            get_modeladmin(Permission)

    @override_settings(DEBUG=False)
    def test_class_not_in_admin_production(self):
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


class HealedContextTestCase(TestCase):
    def test_healing(self):
        context = Context()
        length = len(context.dicts)
        with healed_context(context) as ctx:
            ctx.update({'a': 1})
            ctx.update({'b': 2})
            ctx.update({'c': 3})
        new_length = len(context.dicts)
        self.assertEqual(length, new_length)
        # 1.4 didn't hardcode an initial dict for special values.
        if is_django_15plus():
            self.assertIn('True', context)
            self.assertIn('False', context)
            self.assertIn('None', context)
        self.assertNotIn('b', context)
        is_same = Context()
        # comparing Context() to Context() doesn't work ;|
        self.assertEqual(is_same.dicts, context.dicts)

    def test_healing_prefilled(self):
        context = Context({'b': 2})
        length = len(context.dicts)
        with healed_context(context) as ctx:
            ctx.update({'a': 1})
        new_length = len(context.dicts)
        self.assertEqual(length, new_length)
        if is_django_15plus():
            self.assertIn('True', context)
            self.assertIn('False', context)
            self.assertIn('None', context)
        self.assertIn('b', context)
        self.assertNotIn('a', context)

    def test_healing_no_actions(self):
        context = Context()
        length = len(context.dicts)
        with healed_context(context) as ctx:
            pass
        new_length = len(context.dicts)
        self.assertEqual(length, new_length)
        if is_django_15plus():
            self.assertIn('True', context)
            self.assertIn('False', context)
            self.assertIn('None', context)

    def test_healing_via_dict(self):
        context = {'1': 2}
        with healed_context(context) as ctx:
            ctx.update({'3': 4})
            if is_django_15plus():
                self.assertEqual(len(ctx.dicts), 3)
                self.assertEqual(ctx.dicts, [
                    {'True': True, 'False': False, 'None': None},
                    {'1': 2},
                    {'3': 4},
                ])
        self.assertEqual(len(context), 1)
        self.assertEqual(context, {'1': 2})
