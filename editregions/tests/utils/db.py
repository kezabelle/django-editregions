# -*- coding: utf-8 -*-
from django.contrib.auth.models import User, Group
from django.db.models import Model, PositiveSmallIntegerField
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type
from editregions.utils.db import get_maximum_pk, set_new_position


class GetMaximumPKTestCase(DjangoTestCase):
    def test_getting_max_pk(self):
        for x in range(0, 10):
            y = User(username=x)
            y.save()
        self.assertEqual(11, get_maximum_pk(User))

    def test_getting_max_pk_for_no_objects(self):
        self.assertEqual(1, get_maximum_pk(Group))


class SetNewPositionTestCase(DjangoTestCase):
    def test_setting_new_position(self):
        for x in range(0, 10):
            sample_user, created = User.objects.get_or_create()
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
        self.assertEqual(existing, [1, 10, 2, 3, 4, 5, 6, 7, 8, 9])
