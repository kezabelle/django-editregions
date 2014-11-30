# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
from django.template import Context
from django.test.utils import override_settings
from django.utils.functional import SimpleLazyObject
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from django.contrib.auth.models import User, Permission
from editregions.models import EditRegionConfiguration
from editregions.utils.data import get_content_type, get_model_class, get_modeladmin, attach_configuration, get_configuration, healed_context, RegionMedia
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
    @override_settings(DEBUG=True)
    def test_class_not_in_admin_debug(self):
        with self.assertRaises(ImproperlyConfigured):
            get_modeladmin(Permission)

    @override_settings(DEBUG=False)
    def test_class_not_in_admin_production(self):
        with self.assertRaises(KeyError):
            get_modeladmin(Permission)


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['sample_editregion_template.html']


class AttachConfigurationTestCase(TestCase):
    def setUp(cls):
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

    def test_attaching(self):
        user = User()
        obj, created = attach_configuration(user, EditRegionConfiguration)
        self.assertTrue(hasattr(user, '__editregionconfig__'))
        self.assertTrue(created)
        self.assertIsInstance(getattr(user, '__editregionconfig__'),
                              EditRegionConfiguration)

    def test_reattaching(self):
        user = User()
        obj, created1 = attach_configuration(user, EditRegionConfiguration)
        obj, created2 = attach_configuration(user, EditRegionConfiguration)
        self.assertTrue(hasattr(user, '__editregionconfig__'))
        self.assertFalse(created2)


class GetConfigurationTestCase(TestCase):
    def test_getting(self):
        user = User()
        obj, created = attach_configuration(user, EditRegionConfiguration)
        self.assertIsInstance(get_configuration(user), EditRegionConfiguration)

    def test_getting_without_having_attached(self):
        user = User()
        self.assertNotIsInstance(get_configuration(user),
                                 EditRegionConfiguration)
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


class RegionMediaTestCase(TestCase):
    def test_getitem(self):
        media = RegionMedia()
        media.add_to_top('<style></style>')
        media.add_to_top('<style type="text/css"></style>')
        media.add_to_top('   <style type="text/css"></style>       ')
        only_top = media['top']
        self.assertEqual(only_top.top, ['<style></style>',
                                        '<style type="text/css"></style>'])

        self.assertEqual(only_top.bottom, [])
        only_bottom = media['bottom']
        self.assertEqual(only_bottom.top, [])
        self.assertEqual(only_bottom.bottom, [])

    def test_getitem_keyerror(self):
        media = RegionMedia()
        with self.assertRaises(KeyError):
            media['xyz']

    def test_asdict(self):
        media = RegionMedia()
        media.add_to_top('<style></style>')
        media.add_to_bottom('<script></script>')
        self.assertEqual(media._asdict(), {
            'top': ['<style></style>'],
            'bottom': ['<script></script>']
        })

    def test_deduplicate_on_add(self):
        media = RegionMedia()
        for x in range(0, 5):
            media.add_to_top('<style></style>')
        self.assertEqual(len(media.top), 1)
        self.assertEqual(media.top, ['<style></style>'])

        for x in range(0, 5):
            media.add_to_bottom('<script></script>')
        self.assertEqual(len(media.bottom), 1)
        self.assertEqual(media.bottom, ['<script></script>'])

    def test_remove(self):
        media = RegionMedia()
        for x in range(0, 5):
            media.add_to_top('<style></style>')
        media.remove_from_top('<style></style>')
        self.assertEqual(len(media.top), 0)

    def test_magicadd(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        media.add_to_top(2)
        media.add_to_bottom(4)
        media.add_to_bottom(3)

        other_media = RegionMedia()
        other_media.add_to_top(6)
        other_media.add_to_bottom(7)

        and_another_media = RegionMedia()
        and_another_media.add_to_top('x')
        and_another_media.add_to_top('x')

        new_media = media + other_media + and_another_media
        self.assertEqual(new_media.top, ['<style type="text/css"></style>',
                                         '2', '6', 'x'])
        self.assertEqual(new_media.bottom, ['4', '3', '7'])
        self.assertEqual(new_media._asdict(), {
            'top': ['<style type="text/css"></style>', '2', '6', 'x'],
            'bottom': ['4', '3', '7']
        })

    def test_contains(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        self.assertIn('<style type="text/css"></style>', media)

    def test_equality(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        media2 = RegionMedia()
        media2.add_to_top('<style type="text/css"></style>')
        self.assertEqual(media, media2)

    def test_inequality(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        media2 = RegionMedia()
        media2.add_to_top(2)
        self.assertNotEqual(media, media2)

    def test_truthiness(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        self.assertTrue(media)
        self.assertFalse(RegionMedia())

    def test_make(self):
        media = RegionMedia._make([
            ['<style type="text/css"></style>'],  # offset 0 is top
            ['<script></script>']  # offset 1 is bottom
        ])
        self.assertEqual(media.top, ['<style type="text/css"></style>'])
        self.assertEqual(media.bottom, ['<script></script>'])

    def test_length(self):
        media = RegionMedia()
        media.add_to_top('<style type="text/css"></style>')
        media.add_to_bottom('<script></script>')
        self.assertEqual(len(media), 2)
        self.assertEqual(len(media['top']), 1)
        self.assertEqual(len(media['bottom']), 1)

    def test_init(self):
        media = RegionMedia(top=['b', 'a', 'c', 'a'], bottom=['d', 'd', 'd'])
        self.assertEqual(media.top, ['b', 'a', 'c'])
        self.assertEqual(media.bottom, ['d'])
