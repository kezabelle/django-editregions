# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ImproperlyConfigured
from django.template import Template
from django.test.utils import override_settings
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from model_utils.managers import (PassThroughManager, InheritanceManager,
                                  InheritanceQuerySet)
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.querying import EditRegionChunkQuerySet
from editregions.utils.data import get_content_type
from django.contrib.auth.models import User, Group, Permission

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['sample_editregion_template.html']

class TestBadUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['x/y/z.html']


class EditRegionChunkTestCase(DjangoTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        user_ct = get_content_type(sample_user)
        base = EditRegionChunk(region='test', position=0,
                               content_id=sample_user.pk, content_type=user_ct)
        base.full_clean()
        base.save()
        other = EditRegionChunk(region='test', position=1,
                                content_id=sample_user.pk, content_type=user_ct)
        other.full_clean()
        other.save()
        self.model_dependencies = {
            'user': sample_user,
        }
        self.chunks = {
            'base': base,
            'other': other,
        }

    def test_repr(self):
        user_ct = get_content_type(self.model_dependencies['user'])
        expected = ('<editregions.models.EditRegionChunk pk=1, region=test, '
                    'parent_type={USER.pk}, parent_id=1, '
                    'position=0>'.format(USER=user_ct))
        received = repr(self.chunks['base'])
        self.assertEqual(expected, received)

    def test_str(self):
        expected = 'pk=1, region=test, position=0'
        received = force_text(self.chunks['base'])
        self.assertEqual(expected, received)

    def test_move(self):
        expected = self.chunks['base']
        expected.position = 2

        # do the move
        received = self.chunks['base'].move(requested_position=2)
        self.assertEqual(expected, received)
        expected = (
            self.chunks['other'],
            self.chunks['base'],
        )
        received = tuple(EditRegionChunk.objects.all())
        self.assertEqual(expected, received)

        # move back to first position ...
        self.chunks['base'].move(requested_position=1)
        expected = (
            self.chunks['base'],
            self.chunks['other'],
        )
        received = tuple(EditRegionChunk.objects.all())
        self.assertEqual(expected, received)

    def test_has_managers(self):
        self.assertIsInstance(getattr(EditRegionChunk, 'objects', None),
                              PassThroughManager)

        self.assertIsInstance(EditRegionChunk.objects.all(),
                              EditRegionChunkQuerySet)

        self.assertIsInstance(getattr(EditRegionChunk, 'polymorphs', None),
                              InheritanceManager)

        self.assertIsInstance(EditRegionChunk.polymorphs.all(),
                              InheritanceQuerySet)

        self.assertIsInstance(EditRegionChunk.polymorphs.select_subclasses(),
                              InheritanceQuerySet)

    def test_content_object_was_bound(self):
        expected = self.model_dependencies['user']
        received = self.chunks['base'].content_object
        self.assertEqual(expected, received)


class EditRegionConfigurationTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        self.model_dependencies = {
            'user': sample_user,
        }

    def test_configure_basic(self):
        user = self.model_dependencies['user']
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.configure(obj=user)
        self.assertEqual(self.blank_conf.obj, user)
        self.assertEqual(self.blank_conf.modeladmin, admin.site._registry[User])
        matching_templates = (TestUserAdmin(model=User,
                                            admin_site=admin.site)
                              .get_editregions_templates(user))
        self.assertEqual(self.blank_conf.possible_templates, matching_templates)
        self.assertIsInstance(self.blank_conf.template, Template)
        self.assertTrue(self.blank_conf.has_configuration)
        self.assertEqual(self.blank_conf.config, {})

    def test_configure_template_not_discovered(self):
        user = self.model_dependencies['user']
        self.blank_conf = EditRegionConfiguration()

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestBadUserAdmin)

        self.blank_conf.configure(obj=user)
        self.assertEqual(self.blank_conf.template, None)

    def test_configure_template_discovered(self):
        user = self.model_dependencies['user']
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.configure(obj=user)
        self.assertIsInstance(self.blank_conf.template, Template)

    def test_get_first_valid_template(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.possible_templates = ['sample_editregion_template.html']
        received = self.blank_conf.get_first_valid_template()
        self.assertIsInstance(received, Template)

    def test_get_first_valid_template_failed(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.possible_templates = ['zzzzzz.html']
        received = self.blank_conf.get_first_valid_template()
        self.assertIsNone(received)

    def test_get_template_region_configuration(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        result = self.blank_conf.get_template_region_configuration()
        self.assertEqual(result, {
            'x': {'name': 'test'},
        })

    def test_get_template_region_configuration_failed(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template("xyz")
        with self.assertRaisesRegexp(ValueError,
                                     r'No JSON object could be decoded'):
            self.blank_conf.get_template_region_configuration()

    def test_get_enabled_chunks_for_region_empty(self):
        self.blank_conf = EditRegionConfiguration()
        expected = {}
        received = self.blank_conf.get_enabled_chunks_for_region({})
        self.assertEqual(expected, received)

    def test_get_enabled_chunks_for_region(self):
        self.blank_conf = EditRegionConfiguration()
        expected = {User: 1, Group: None}
        received = self.blank_conf.get_enabled_chunks_for_region({
            'auth.User': 1,
            'auth.Group': None
        })
        self.assertEqual(expected, received)

    def test_get_enabled_chunks_for_region_bad_models_silent_fail(self):
        self.blank_conf = EditRegionConfiguration()
        expected = {User: 1, Group: None}
        received = self.blank_conf.get_enabled_chunks_for_region({
            'auth.User': 1,
            'auth.Group': None,
            'x.Y': 1,
        })
        self.assertEqual(expected, received)

    @override_settings(DEBUG=True)
    def test_get_enabled_chunks_for_region_bad_models_loud_fail(self):
        self.blank_conf = EditRegionConfiguration()
        with self.assertRaises(ImproperlyConfigured):
            self.blank_conf.get_enabled_chunks_for_region({
                'auth.User': 1,
                'auth.Group': None,
                'x.Y': 1,
            })

    def test_get_limits_for_no_models(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        result = self.blank_conf.get_limits_for(region='x', chunk=User)
        self.assertEqual(0, result)

    def test_get_limits_for(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test",
                "models": {
                    "auth.User": 1,
                    "auth.Group": 0,
                    "auth.Permission": null
                }
            }
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        result = self.blank_conf.get_limits_for(region='x', chunk=User)
        self.assertEqual(1, result)
        # 0 means don't show up!
        result = self.blank_conf.get_limits_for(region='x', chunk=Group)
        self.assertEqual(0, result)
        result = self.blank_conf.get_limits_for(region='x', chunk=Permission)
        self.assertEqual(None, result)
#
#     def test_fetch_chunks(self):
#         self.assertEqual(1, 2)
#
#     def test_fetch_chunks_for(self):
#         self.assertEqual(1, 2)
