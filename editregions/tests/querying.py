# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type


class EditRegionChunkQuerySetTestCase(DjangoTestCase):
    def setUp(self):
        user, created = User.objects.get_or_create()
        user_ct = get_content_type(User)

        for x in range(1, 10):
            obj = EditRegionChunk(region='test', position=x,
                                  content_id=user.pk, content_type=user_ct)
            obj.full_clean()
            obj.save()
        self.user = user
        self.content_type = user_ct

    def test_moving(self):
        data = EditRegionChunk.objects.move(target=1, position=2,
                                            region='test')
        self.assertEqual(data, EditRegionChunk(region='test', pk=1,
                                               content_type=self.content_type,
                                               content_id=self.user.pk,
                                               position=2))

    def test_moving_invalid_pk(self):
        data = EditRegionChunk.objects.move(target=-1, position=2,
                                            region='')
        self.assertEqual(data, {'pk': 'content block does not exist'})

    def test_moving_invalid_position(self):
        data = EditRegionChunk.objects.move(target=1, position=-1,
                                            region='')
        self.assertEqual(data, {'position': [u'Ensure this value is greater '
                                             u'than or equal to 1.']})
