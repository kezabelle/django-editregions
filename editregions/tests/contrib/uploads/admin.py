# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.template import Context
from django.test import TestCase
from django.utils.timezone import now
from editregions.contrib.uploads.admin import FileAdmin
from editregions.contrib.uploads.models import File
from editregions.utils.data import get_content_type, get_modeladmin


class FileAdminTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create()
        user_ct = get_content_type(sample_user)
        self.file = File(position=1, content_type=user_ct,
                         content_id=sample_user.pk, region='test',
                         title='x', data='x/y/z.gif', modified=now())
        try:
            admin.site.unregister(File)
        except NotRegistered:
            pass
        admin.site.register(File, FileAdmin)

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.file)
        out = theadmin.render_into_region(obj=self.file, context=Context({
            'chunkloop': {'object': self.file}
        }))
        self.assertIn('a href="x/y/z.gif?t=', out)
        self.assertIn('>x</a>', out)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.file)
        out = theadmin.render_into_summary(obj=self.file, context=Context())
        self.assertEqual(out, 'x (z.gif)')

    def test_render_into_summary_no_data(self):
        self.file.data = None
        theadmin = get_modeladmin(self.file)
        out = theadmin.render_into_summary(obj=self.file, context=Context())
        self.assertEqual(out, 'x')
