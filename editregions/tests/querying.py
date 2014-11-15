# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type


class EditRegionChunkManagerTestCase(DjangoTestCase):
    def setUp(self):
        user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(User)

        for x in range(0, 9):
            obj = EditRegionChunk(region='test', position=x,
                                  content_id=user.pk, content_type=user_ct)
            obj.full_clean()
            obj.save()
        self.user = user
        self.content_type = user_ct

    def test_moving_within_same_region(self):
        to_move = EditRegionChunk.objects.get(pk=1)
        with self.assertNumQueries(11):
            EditRegionChunk.objects.move(obj=to_move, from_position=0,
                                         to_position=2,
                                         from_region='test',
                                         to_region='test')
        after_move = EditRegionChunk.objects.get(pk=1)
        self.assertEqual(after_move.position, 2)

    def test_moving_invalid_position(self):
        """
        Can't go past minimum position
        """
        to_move = EditRegionChunk.objects.get(pk=1)
        with self.assertNumQueries(0):
            with self.assertRaises(ValueError):
                EditRegionChunk.objects.move(obj=to_move, from_position=0,
                                             to_position=-1,
                                             from_region='test',
                                             to_region='test')

    def test_moving_pointless_move(self):
        """
        This shouldn't do any queries because there's nothing to move.
        """
        to_move = EditRegionChunk.objects.get(pk=1)
        with self.assertNumQueries(0):
            with self.assertRaises(ValueError):
                EditRegionChunk.objects.move(obj=to_move, from_position=0,
                                             to_position=0,
                                             from_region='test',
                                             to_region='test')
