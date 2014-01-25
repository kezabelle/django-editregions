# -*- coding: utf-8 -*-
from uuid import uuid4
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, TemplateDoesNotExist
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
        sample_user, created = User.objects.get_or_create(username='test')
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

    def test_cleaning(self):
        erc = EditRegionChunk(region='test', position=0,
                              content_id=str(uuid4()),
                              content_type=get_content_type(User))
        erc.full_clean()
        self.assertEqual(erc.position, 1)

    def test_repr(self):
        user_ct = get_content_type(self.model_dependencies['user'])
        expected = ('<editregions.models.EditRegionChunk pk=1, region=test, '
                    'parent_type={USER.pk}, parent_id=1, '
                    'position=1>'.format(USER=user_ct))
        received = repr(self.chunks['base'])
        self.assertEqual(expected, received)

    def test_str(self):
        expected = 'pk=1, region=test, position=1'
        received = force_text(self.chunks['base'])
        self.assertEqual(expected, received)

    def test_move(self):
        expected = self.chunks['base']
        expected.position = 2

        # do the move
        received = self.chunks['base'].move(requested_position=2)
        self.assertEqual(expected, received)
        expected = (self.chunks['other'], self.chunks['base'])
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

    def test_move_bad_position(self):
        expected = self.chunks['base']
        expected.position = 2
        errors = self.chunks['base'].move(requested_position=-1)
        self.assertEqual(errors, {
            'position': [u'Ensure this value is greater than or equal to 1.']
        })

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


class EditRegionConfigurationTestCase(DjangoTestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create(username='test')
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

        with self.settings(DEBUG=True):
            with self.assertRaises(TemplateDoesNotExist):
                self.blank_conf.configure(obj=user)

        with self.settings(DEBUG=False):
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

    def test_get_first_valid_template_string_input(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.possible_templates = 'sample_editregion_template.html'
        received = self.blank_conf.get_first_valid_template()
        self.assertIsInstance(received, Template)

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

    def test_get_template_region_configuration_no_names_fallback(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {}
        }''')
        result = self.blank_conf.get_template_region_configuration()
        self.assertEqual(result, {
            'x': {'name': 'x'},
        })

    def test_get_template_region_configuration_failed_json_decoding(self):
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

    @override_settings(DEBUG=False)
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
        with self.assertRaisesRegexp(ImproperlyConfigured,
                                     r'App with label x could not be found'):
            self.blank_conf.get_enabled_chunks_for_region({
                'x.Y': 1,
            })

    @override_settings(DEBUG=True)
    def test_get_enabled_chunks_for_region_bad_models_loud_fail2(self):
        self.blank_conf = EditRegionConfiguration()
        with self.assertRaisesRegexp(ImproperlyConfigured,
                                     r'Unable to load model "Y" from app "auth"'):  # noqa
            self.blank_conf.get_enabled_chunks_for_region({
                'auth.Y': 1,
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

    def test_fetch_chunks_for_no_obj_debug_false(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        with self.settings(DEBUG=False):
            result = self.blank_conf.fetch_chunks_for(region='x')
            self.assertEqual([], result)

    def test_fetch_chunks_for_no_obj_debug_true(self):
        self.blank_conf = EditRegionConfiguration()
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa

        with self.settings(DEBUG=True):
            with self.assertRaises(ImproperlyConfigured):
                self.blank_conf.fetch_chunks_for(region='x')

    def test_fetch_chunks_for_obj(self):
        user, created = User.objects.get_or_create(username='test')
        self.blank_conf = EditRegionConfiguration(obj=user)
        self.blank_conf.template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        results = self.blank_conf.fetch_chunks_for(region='x')
        self.assertEqual([], results)

    def test_fetch_chunks_for_obj_noregions(self):
        user, created = User.objects.get_or_create(username='test')
        self.blank_conf = EditRegionConfiguration(obj=user)
        self.blank_conf.template = Template('''{
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        results = self.blank_conf.fetch_chunks_for(region='x')
        self.assertEqual((), results)

    def test_fetch_chunks_for_obj_manyregions(self):
        user, created = User.objects.get_or_create(username='test')
        self.blank_conf = EditRegionConfiguration(obj=user)
        self.blank_conf.template = Template('''{
            "x": {},
            "y": {},
            "z": {}
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        results = self.blank_conf.fetch_chunks_for(region='x')
        self.assertEqual([], results)

    def test_fetch_chunks(self):
        user, created = User.objects.get_or_create(username='test')
        self.blank_conf = EditRegionConfiguration(obj=user)
        self.blank_conf.template = Template('''{
            "x": {},
            "y": {},
            "z": {}
        }''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        results = self.blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {u'y': [], u'x': [], u'z': []})

    def test_yaml_serializer(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("YAML not available ...")
        user, created = User.objects.get_or_create(username='test')
        self.blank_conf = EditRegionConfiguration(obj=user, decoder='yaml')
        self.blank_conf.template = Template('''---
          test:
            name: "whee!"
            models:
              embeds.Iframe: 2
          test2:
            name: "oh my goodness, another test region"
            models:
              embeds.Iframe: 1
          test3:
            name: "oh my goodness, yet another test region"
            models:
              embeds.Iframe: null
        ''')
        self.blank_conf.config = self.blank_conf.get_template_region_configuration()  # noqa
        results = self.blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {'test': [], 'test3': [], 'test2': []})

    def test_bad_serializer_serializer(self):
        with self.assertRaises(ImproperlyConfigured):
            EditRegionConfiguration(decoder='ghost')


class EditRegionConfigurationOperatorsTestCase(TestCase):
    def test_equality(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1, 'y': 2}
        self.assertEqual(blank_conf, blank_conf2)

    def test_inequality(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1}
        self.assertNotEqual(blank_conf, blank_conf2)

    def test_lessthan(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1}
        self.assertLess(blank_conf2, blank_conf)

    def test_lessthanequal(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1}
        self.assertLessEqual(blank_conf2, blank_conf)

    def test_greaterthan(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1}
        self.assertGreater(blank_conf, blank_conf2)

    def test_greaterthanequal(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1, 'y': 2}
        blank_conf2 = EditRegionConfiguration()
        blank_conf2.has_configuration = True
        blank_conf2.config = {'x': 1}
        self.assertGreaterEqual(blank_conf, blank_conf2)

    def test_bool(self):
        blank_conf = EditRegionConfiguration()
        blank_conf.has_configuration = True
        blank_conf.config = {'x': 1}
        self.assertTrue(blank_conf)

        blank_conf2 = EditRegionConfiguration()
        self.assertFalse(blank_conf2)
