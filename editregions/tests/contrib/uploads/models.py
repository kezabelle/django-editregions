# -*- coding: utf-8 -*-
import os
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils.encoding import force_text
from editregions.contrib.uploads.models import File
from editregions.utils.data import get_content_type
from django.conf import settings


class FileTestCase(TestCase):
    def setUp(self):
        fakefile = SimpleUploadedFile('x/y/z.gif', b'xyz')
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        self.file = File(position=1, content_type=user_ct,
                         content_id=sample_user.pk, region='test',
                         title='x', data=fakefile)

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

    def test_is_not_image(self):
        self.assertFalse(self.file.is_image())

    def test_get_dimensions_not_image(self):
        self.assertIsNone(self.file.dimensions)

    def test_get_dimensionsstr_not_image(self):
        self.assertEqual('', self.file.dimensions_as_str())

    def test_is_image(self):
        file_ = os.path.join(settings.STATICFILES_DIRS[0], "test.png")
        with open(file_, mode='rb') as f:
            fakefile = SimpleUploadedFile('x/y/z.gif', f.read())
        self.file.data = fakefile
        self.assertTrue(self.file.is_image())

    def test_get_dimensions_image(self):
        file_ = os.path.join(settings.STATICFILES_DIRS[0], "test.png")
        with open(file_, mode='rb') as f:
            fakefile = SimpleUploadedFile('x/y/z.gif', f.read())
        self.file.data = fakefile
        self.assertEqual((16, 16), self.file.dimensions)

    def test_get_dimensionsstr_image(self):
        file_ = os.path.join(settings.STATICFILES_DIRS[0], "test.png")
        with open(file_, mode='rb') as f:
            fakefile = SimpleUploadedFile('x/y/z.gif', f.read())
        self.file.data = fakefile
        self.assertEqual('16x16', self.file.dimensions_as_str())
