# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.models import User
from django.template import Context
from django.test import TestCase
from editregions.contrib.text.admin import WYMAdmin, MCEAdmin
from editregions.contrib.text.models import WYM, MCE
from editregions.utils.data import get_modeladmin, get_content_type


class WYMAdminTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        self.obj = WYM(position=1, content_type=user_ct,
                       content_id=sample_user.pk, region='test',
                       content='<b><em> hi there!   </em></b>')
        try:
            admin.site.unregister(WYM)
        except NotRegistered:
            pass
        admin.site.register(WYM, WYMAdmin)

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.obj)
        out = theadmin.render_into_region(obj=self.obj, context=Context({
            'chunkloop': {'object': self.obj}
        }))
        self.assertIn('<b><em> hi there!   </em></b>', out)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.obj)
        out = theadmin.render_into_summary(obj=self.obj, context=Context({
            'chunkloop': {'object': self.obj}
        }))
        self.assertEqual('hi there!', out)


class MCEAdminTestCase(TestCase):
    def setUp(self):
        sample_user, created = User.objects.get_or_create(username='test')
        user_ct = get_content_type(sample_user)
        self.obj = MCE(position=1, content_type=user_ct,
                       content_id=sample_user.pk, region='test',
                       content='<b><em> hi there!   </em></b>')
        try:
            admin.site.unregister(MCE)
        except NotRegistered:
            pass
        admin.site.register(MCE, MCEAdmin)

    def test_render_into_region(self):
        theadmin = get_modeladmin(self.obj)
        out = theadmin.render_into_region(obj=self.obj, context=Context({
            'chunkloop': {'object': self.obj}
        }))
        self.assertIn('<b><em> hi there!   </em></b>', out)

    def test_render_into_summary(self):
        theadmin = get_modeladmin(self.obj)
        out = theadmin.render_into_summary(obj=self.obj, context=Context({
            'chunkloop': {'object': self.obj}
        }))
        self.assertEqual('hi there!', out)

    def test_media(self):
        theadmin = get_modeladmin(self.obj)
        self.assertEqual({'screen': ['editregions/css/text.css']},
                         theadmin.media._css)
