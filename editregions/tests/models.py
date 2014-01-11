# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from model_utils.managers import (PassThroughManager, InheritanceManager,
                                  InheritanceQuerySet)
from editregions.models import EditRegionChunk
from editregions.querying import EditRegionChunkQuerySet
from editregions.utils.data import get_content_type
from django.contrib.auth.models import User
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['x/y.html']


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

    def test_content_object(self):
        expected = self.model_dependencies['user']
        received = self.chunks['base'].content_object
        self.assertEqual(expected, received)
#
#
# class EditRegionConfigurationTestCase(TestCase):
#     def test_configure(self):
#         self.assertEqual(1, 2)
#
#     def test_get_first_valid_template(self):
#         self.assertEqual(1, 2)
#
#     def test_get_template_region_configuration(self):
#         self.assertEqual(1, 2)
#
#     def test_get_enabled_chunks_for_region(self):
#         self.assertEqual(1, 2)
#
#     def test_get_limits_for(self):
#         self.assertEqual(1, 2)
#
#     def test_fetch_chunks(self):
#         self.assertEqual(1, 2)
#
#     def test_fetch_chunks_for(self):
#         self.assertEqual(1, 2)
