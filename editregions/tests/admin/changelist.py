# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.http import QueryDict
from django.template import Template, Context
from django.test import TestCase as DjangoTestCase, RequestFactory
from editregions.admin import EditRegionAdmin
from editregions.admin.changelist import EditRegionChangeList
from editregions.admin.utils import AdminChunkWrapper
from editregions.constants import (REQUEST_VAR_ID, REQUEST_VAR_CT,
                                   REQUEST_VAR_REGION)
from editregions.contrib.embeds.models import Iframe
from editregions.models import EditRegionChunk, EditRegionConfiguration
from editregions.utils.data import (attach_configuration, get_configuration,
                                    get_content_type)
try:
    import json
except ImportError:
    from django.utils import simplejson as json


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['fillable_editregion_template.html']


class ChangeListTestCase(DjangoTestCase):
    def setUp(self):
        request = RequestFactory().get('/')
        our_list_display = EditRegionAdmin.list_display
        our_list_links = (EditRegionAdmin(User, admin.site)
                          .get_list_display_links(request=request,
                                                  list_display=our_list_display))

        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        self.user = user

        user_content_type = get_content_type(User)

        attach_configuration(user, EditRegionConfiguration)
        config = get_configuration(user)
        request.GET = QueryDict('', mutable=True)
        request.GET.update({REQUEST_VAR_ID: user.pk,
                            REQUEST_VAR_CT: user_content_type.pk,
                            REQUEST_VAR_REGION: 'test'})

        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)

        cl = EditRegionChangeList(request=request, model=EditRegionChunk,
                                  list_display=our_list_display,
                                  list_display_links=our_list_links,
                                  list_filter=EditRegionAdmin.list_filter,
                                  date_hierarchy=None, search_fields=None,
                                  list_select_related=None, list_per_page=100,
                                  list_max_show_all=100, list_editable=None,
                                  model_admin=admin.site._registry[EditRegionChunk],  # noqa
                                  parent_obj=user, parent_conf=config)
        self.changelist = cl

        badconfig = EditRegionConfiguration()
        cl2 = EditRegionChangeList(request=request, model=EditRegionChunk,
                                   list_display=our_list_display,
                                   list_display_links=our_list_links,
                                   list_filter=EditRegionAdmin.list_filter,
                                   date_hierarchy=None, search_fields=None,
                                   list_select_related=None, list_per_page=100,
                                   list_max_show_all=100, list_editable=None,
                                   model_admin=admin.site._registry[EditRegionChunk],  # noqa
                                   parent_obj=user, parent_conf=badconfig)
        self.changelist2 = cl2

    def test_attrs(self):
        self.assertEqual('test', self.changelist.region)
        self.assertEqual(get_content_type(User).pk,
                         self.changelist.parent_content_type)
        self.assertEqual(self.user.pk, self.changelist.parent_content_id)

    def test_available_chunks(self):
        expected = [
            AdminChunkWrapper(opts=Iframe._meta, namespace='admin',
                              content_id=self.user.pk, region='test',
                              content_type=get_content_type(User))
        ]
        self.assertEqual(expected, self.changelist.available_chunks)

    def test_template(self):
        self.assertIsInstance(self.changelist.template, Template)
        render = self.changelist.template.render(Context())
        to_json = json.loads(render)
        self.assertEqual(to_json, {
            'test': {
                'name': 'whee!',
                'models': {
                    'embeds.Iframe': None,
                }
            }
        })

    def test_pretty_region_name(self):
        self.assertEqual('whee!', self.changelist.get_region_display)

    def test_empty_filters(self):
        self.assertEqual(self.changelist2.available_chunks, ())
