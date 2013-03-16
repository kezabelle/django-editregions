# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group, User
from django.contrib.contenttypes.models import ContentType
from django.utils.unittest.case import TestCase
from editregions.models import EditRegionChunk

class EditRegionChunkTestCase(TestCase):
    def test_repr(self):
        obj = EditRegionChunk.objects.create(
            region='test',
            position=1,
            content_type=ContentType.objects.get_for_model(User),
            content_id=1,
            chunk_content_type=ContentType.objects.get_for_model(Group)
        )
        me = "%s attached to None via region test" % obj.__class__
        self.assertEqual(repr(obj), me)
