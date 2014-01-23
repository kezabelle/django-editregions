# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils.encoding import force_text
from editregions.contrib.uploads.models import File
from editregions.utils.data import get_content_type


class FileTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        user_ct = get_content_type(sample_user)
        self.file = File(position=1, content_type=user_ct,
                         content_id=sample_user.pk, region='test',
                         title='x', data='x/y/z.gif')

    def test_get_filename(self):
        self.assertEqual('z.gif', self.file.get_filename())

    def test_get_filetype(self):
        self.assertEqual('gif', self.file.get_filetype())

    def test_str_using_title(self):
        self.assertEqual('x', force_text(self.file))

    def test_str_using_filename(self):
        self.file.title = None
        self.assertEqual('z.gif', force_text(self.file))

    def test_str_no_title_no_filename(self):
        self.file.data = None
        self.file.title = None
        self.assertEqual('No file or title', force_text(self.file))
