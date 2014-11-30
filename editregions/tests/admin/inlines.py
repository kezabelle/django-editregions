# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase, RequestFactory
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.inlines import EditRegionInline
from editregions.contrib.embeds.models import Iframe
from editregions.utils.data import get_content_type


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['fillable_editregion_template.html']


class EditRegionInlineTestCase(DjangoTestCase):
    def test_fieldsets(self):
        inline = EditRegionInline(parent_model=User, admin_site=admin.site)
        self.assertEqual(inline.get_fieldsets(), [
            (None, {'fields': ['region', 'position']})
        ])

    def test_formset_no_obj(self):
        inline = EditRegionInline(parent_model=User, admin_site=admin.site)
        request = RequestFactory().get('/')
        formset = inline.get_formset(request=request)
        self.assertEqual(formset.region_changelists, [])

    def test_formset_has_obj(self):
        inline = EditRegionInline(parent_model=User, admin_site=admin.site)
        request = RequestFactory().post('/')

        user = User(username='user')
        user.set_password('user')
        user.full_clean()
        user.save()

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

        formset = inline.get_formset(request=request, obj=user)
        self.assertEqual(len(formset.region_changelists), 1)
        self.assertIsInstance(formset.region_changelists[0],
                              EditRegionChangeList)
        self.assertEqual(formset.region_changelists[0].region, 'test')
