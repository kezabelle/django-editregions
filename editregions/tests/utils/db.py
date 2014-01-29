# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
try:
    from unittest.case import TestCase
except ImportError:
    from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type
from editregions.utils.db import (get_maximum_pk, set_new_position,
                                  get_chunks_in_region_count)
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text


class GetMaximumPKTestCase(DjangoTestCase):
    def test_getting_max_pk(self):
        for x in range(0, 10):
            y = User(username=x)
            y.set_password(force_text(x))
            y.full_clean()
            y.save()
        self.assertEqual(10, get_maximum_pk(User))

    def test_getting_max_pk_for_no_objects(self):
        self.assertEqual(1, get_maximum_pk(Group))


class SetNewPositionTestCase(DjangoTestCase):
    def test_setting_new_position(self):
        sample_user, created = User.objects.get_or_create(username='test')
        for x in range(0, 10):
            user_ct = get_content_type(User)
            base = EditRegionChunk(region='test', position=x,
                                   content_id=sample_user.pk,
                                   content_type=user_ct)
            base.full_clean()
            base.save()

        existing = list(EditRegionChunk.objects.all().order_by('position')
                        .values_list('pk', flat=True))
        self.assertEqual(existing, list(range(1, 11)))

        last = existing[-1]
        self.assertEqual(last, 10)

        set_new_position(EditRegionChunk, last, 0)
        existing = list(EditRegionChunk.objects.all().order_by('position')
                        .values_list('pk', flat=True))
        self.assertEqual(existing, [10, 1, 2, 3, 4, 5, 6, 7, 8, 9])


class GetChunksInRegionCountTestCase(DjangoTestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        self.user = sample_user
        self.content_type = user_ct

    def test_count(self):
        for x in range(1, 10):
            obj = EditRegionChunk(region='test', position=x,
                                  content_id=self.user.pk,
                                  content_type=self.content_type)
            obj.full_clean()
            obj.save()
        count = get_chunks_in_region_count(EditRegionChunk,
                                           content_type=self.content_type,
                                           obj_id=self.user.pk, region='test')
        self.assertEqual(9, count)

    def test_nothing(self):
        count = get_chunks_in_region_count(EditRegionChunk,
                                           content_type=self.content_type,
                                           obj_id=self.user.pk, region='test')
        self.assertEqual(0, count)
