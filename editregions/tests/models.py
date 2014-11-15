# -*- coding: utf-8 -*-
from uuid import uuid4
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.core.exceptions import ImproperlyConfigured
from django.template import Template, TemplateDoesNotExist
from django.test.utils import override_settings
from editregions.utils.versioning import is_django_17plus

try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from model_utils.managers import (PassThroughManager, InheritanceManager,
                                  InheritanceQuerySet)
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk, EditRegionConfiguration
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
        blank_conf = EditRegionConfiguration()
        blank_conf.configure(obj=user)
        self.assertEqual(blank_conf.obj, user)
        self.assertTrue(blank_conf.has_configuration)
        self.assertEqual(blank_conf.config, {})

    def test_configure_template_not_discovered(self):
        user = self.model_dependencies['user']
        blank_conf = EditRegionConfiguration()

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestBadUserAdmin)

        with self.settings(DEBUG=True):
            with self.assertRaises(TemplateDoesNotExist):
                blank_conf.configure(obj=user)

        with self.settings(DEBUG=False):
            blank_conf.configure(obj=user)
            self.assertFalse(blank_conf.has_configuration)

    def test_configure_template_discovered(self):
        """
        We can't test for the Template instance directly, as it's no longer
        exposed on the object.
        Given the template `sample_editregion_template.html` has nothing in it,
        the config should become an empty dict.
        """
        user = self.model_dependencies['user']
        blank_conf = EditRegionConfiguration()
        blank_conf.configure(obj=user)
        self.assertEqual({}, blank_conf.config)

    def test_get_first_valid_template(self):
        blank_conf = EditRegionConfiguration()
        templates = ['sample_editregion_template.html']
        received = blank_conf.get_first_valid_template(
            possible_templates=templates)
        self.assertIsInstance(received, Template)

    def test_get_first_valid_template_failed(self):
        blank_conf = EditRegionConfiguration()
        templates = ['zzzzzz.html']
        received = blank_conf.get_first_valid_template(
            possible_templates=templates)
        self.assertIsNone(received)

    def test_get_first_valid_template_string_input(self):
        blank_conf = EditRegionConfiguration()
        templates = 'sample_editregion_template.html'
        received = blank_conf.get_first_valid_template(
            possible_templates=templates)
        self.assertIsInstance(received, Template)

    def test_get_template_region_configuration(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        result = blank_conf.get_template_region_configuration(
            template_instance=template)
        self.assertEqual(result, {
            'x': {'name': 'test'},
        })

    def test_get_template_region_configuration_no_names_fallback(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {}
        }''')
        result = blank_conf.get_template_region_configuration(
            template_instance=template)
        self.assertEqual(result, {
            'x': {'name': 'x'},
        })

    def test_get_template_region_configuration_failed_json_decoding(self):
        blank_conf = EditRegionConfiguration()
        template = Template("xyz")
        with self.assertRaisesRegexp(ValueError,
                                     r'No JSON object could be decoded'):
            blank_conf.get_template_region_configuration(
                template_instance=template)

    def test_get_enabled_chunks_for_region_empty(self):
        blank_conf = EditRegionConfiguration()
        expected = {}
        received = blank_conf.get_enabled_chunks_for_region({})
        self.assertEqual(expected, received)

    def test_get_enabled_chunks_for_region(self):
        blank_conf = EditRegionConfiguration()
        expected = {User: 1, Group: None}
        received = blank_conf.get_enabled_chunks_for_region({
            'auth.User': 1,
            'auth.Group': None
        })
        self.assertEqual(expected, received)

    @override_settings(DEBUG=False)
    def test_get_enabled_chunks_for_region_bad_models_silent_fail(self):
        blank_conf = EditRegionConfiguration()
        expected = {User: 1, Group: None}
        received = blank_conf.get_enabled_chunks_for_region({
            'auth.User': 1,
            'auth.Group': None,
            'x.Y': 1,
        })
        self.assertEqual(expected, received)

    @override_settings(DEBUG=True)
    def test_get_enabled_chunks_for_region_bad_models_loud_fail(self):
        blank_conf = EditRegionConfiguration()
        error = ImproperlyConfigured
        if is_django_17plus():
            error = LookupError
        with self.assertRaises(error):
            blank_conf.get_enabled_chunks_for_region({
                'x.Y': 1,
            })

    @override_settings(DEBUG=True)
    def test_get_enabled_chunks_for_region_bad_models_loud_fail2(self):
        blank_conf = EditRegionConfiguration()
        with self.assertRaisesRegexp(ImproperlyConfigured,
                                     r'Unable to load model "Y" from app "auth"'):  # noqa
            blank_conf.get_enabled_chunks_for_region({
                'auth.Y': 1,
            })

    def test_get_limits_for_no_models(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        result = blank_conf.get_limits_for(region='x', chunk=User)
        self.assertEqual(0, result)

    def test_get_limits_for(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {
                "name": "test",
                "models": {
                    "auth.User": 1,
                    "auth.Group": 0,
                    "auth.Permission": null
                }
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        result = blank_conf.get_limits_for(region='x', chunk=User)
        self.assertEqual(1, result)
        # 0 means don't show up!
        result = blank_conf.get_limits_for(region='x', chunk=Group)
        self.assertEqual(0, result)
        result = blank_conf.get_limits_for(region='x', chunk=Permission)
        self.assertEqual(None, result)

    def test_fetch_chunks_for_no_obj_debug_false(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        with self.settings(DEBUG=False):
            result = blank_conf.fetch_chunks_for(region='x')
            self.assertEqual([], result)

    def test_fetch_chunks_for_no_obj_debug_true(self):
        blank_conf = EditRegionConfiguration()
        template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)

        with self.settings(DEBUG=True):
            with self.assertRaises(ImproperlyConfigured):
                blank_conf.fetch_chunks_for(region='x')

    def test_fetch_chunks_for_obj(self):
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user)
        template = Template('''{
            "x": {
                "name": "test"
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        results = blank_conf.fetch_chunks_for(region='x')
        self.assertEqual([], results)

    def test_fetch_chunks_for_obj_noregions(self):
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user)
        template = Template('''{
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        results = blank_conf.fetch_chunks_for(region='x')
        self.assertEqual((), results)

    def test_fetch_chunks_for_obj_manyregions(self):
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user)
        template = Template('''{
            "x": {},
            "y": {},
            "z": {}
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        results = blank_conf.fetch_chunks_for(region='x')
        self.assertEqual([], results)

    def test_fetch_chunks(self):
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user)
        template = Template('''{
            "x": {},
            "y": {},
            "z": {}
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        results = blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {u'y': [], u'x': [], u'z': []})

    def test_json_serializer(self):
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user, decoder='json')
        template = Template('''{
            "test": {
                "name": "whee!",
                "models": {
                    "embeds.Iframe": 2
                }
            },
            "test2": {
                "name": "oh my goodness, another test region",
                "models": {
                    "embeds.Iframe": 1
                }
            },
            "test3": {
                "name": "oh my goodness, yet another test region",
                "models": {
                    "embeds.Iframe": null
                }
            }
        }''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        self.assertEqual(dict(blank_conf.config), {
            'test': {
                'models': {
                    Iframe: 2
                },
                'name': 'whee!'
            },
            'test2': {
                'models': {
                    Iframe: 1
                },
                'name': 'oh my goodness, another test region'
            },
            'test3': {
                'models': {
                    Iframe: None,
                },
                'name': 'oh my goodness, yet another test region'
            }
        })
        results = blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {'test': [], 'test3': [], 'test2': []})

    def test_yaml_serializer(self):
        try:
            import yaml
        except ImportError:
            self.skipTest("YAML not available ...")
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user, decoder='yaml')
        template = Template('''---
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
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        self.assertEqual(dict(blank_conf.config), {
            'test': {
                'models': {
                    Iframe: 2
                },
                'name': 'whee!'
            },
            'test2': {
                'models': {
                    Iframe: 1
                },
                'name': 'oh my goodness, another test region'
            },
            'test3': {
                'models': {
                    Iframe: None,
                },
                'name': 'oh my goodness, yet another test region'
            }
        })
        results = blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {'test': [], 'test3': [], 'test2': []})

    def test_toml_serializer(self):
        try:
            import toml
        except ImportError:
            self.skipTest("toml not available ...")
        user, created = User.objects.get_or_create(username='test')
        blank_conf = EditRegionConfiguration(obj=user, decoder='toml')
        template = Template('''
        [test]
        name = "whee!"
        [test.models]
        embeds.Iframe = 2

        [test2]
        name = "oh my goodness, another test region"
        [test2.models]
        embeds.Iframe = 1

        [test3]
        name = "oh my goodness, yet another test region"
        [test3.models]
        embeds.Iframe = false
        ''')
        blank_conf.config = blank_conf.get_template_region_configuration(
            template_instance=template)
        self.assertEqual(dict(blank_conf.config), {
            'test': {
                'models': {
                    Iframe: 2
                },
                'name': 'whee!'
            },
            'test2': {
                'models': {
                    Iframe: 1
                },
                'name': 'oh my goodness, another test region'
            },
            'test3': {
                'models': {
                    Iframe: None,
                },
                'name': 'oh my goodness, yet another test region'
            }
        })
        results = blank_conf.fetch_chunks()
        self.assertEqual(dict(results), {'test': [], 'test3': [], 'test2': []})

    def test_bad_serializer_serializer(self):
        with self.assertRaises(ImproperlyConfigured):
            EditRegionConfiguration(decoder='ghost')

    def test_dissecting_subclasses(self):
        args = (
            'zzz__yyy__xxx',
            'a',
            'b',
            'zzz__yyy',
            'c',
            'zzz',
            'e',
            'f',
            'c__d',
            'g',
            'h',
            'i',
            'j',
            'k',
        )
        expected = (
            ('c', 'c__d'),
            ('zzz', 'zzz__yyy', 'zzz__yyy__xxx'),
            ('a', 'b', 'e', 'f', 'g', 'h', 'i'),
            ('j', 'k'),
        )
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=7)
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_not_enough(self):
        args = ('a', 'b', 'c', 'd', 'e', 'f')
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=7)
        self.assertEqual(result, (args,))

    def test_dissecting_subclasses_one_leftover(self):
        args = ('a', 'b', 'c', 'd', 'e', 'f', 'g')
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=3)
        expected = (('a', 'b', 'c'), ('d', 'e', 'f', 'g'))
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_one_leftover_crossing_relations(self):
        args = ('a', 'b', 'c', 'a__b', 'd', 'e', 'f', 'g')
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=5)
        expected = (('a', 'a__b'), ('b', 'c', 'd', 'e', 'f', 'g'))
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_with_stupid_skip(self):
        """
        with a split of 1, don't conjoin the last relation with the previous
        eg, don't do: ('a', ('b', 'c')), instead do: (('a',), ('b',), ('c',))

        grandparents and stuff are still all selected at once, you cretin.
        """
        args = ('a', 'b', 'c', 'a__b', 'd', 'e', 'f', 'g')
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=1)
        expected = (
            ('a', 'a__b'),
            ('b',),
            ('c',),
            ('d',),
            ('e',),
            ('f',),
            ('g',)
        )
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_with_short_items(self):
        args = ('a',)
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=7)
        expected = (args,)
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_with_no_items(self):
        args = ()
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=7)
        expected = ()
        self.assertEqual(result, expected)

    def test_dissecting_subclasses_with_only_deep_descendants(self):
        args = ('a', 'b', 'a__c', 'b__d', 'b__d__e', 'a__e')
        blank_conf = EditRegionConfiguration()
        result = blank_conf._dissect_subclasses(args, split_after=7)
        expected = (('a', 'a__c', 'a__e'), ('b', 'b__d', 'b__d__e'))
        self.assertEqual(result, expected)


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
