# -*- coding: utf-8 -*-
from django.contrib.admin.sites import site
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test.client import RequestFactory
from django.utils.unittest.case import TestCase
from editregions.admin.modeladmins import (OneToOneStackedInline, OneToOneTabularInline,
                                           RegionAdmin)
from editregions.admin.utils import RequiredInlineFormSet


class SubclassedInlinesTestCase(TestCase):

    def test_our_stacked_inline(self):
        """Just make sure I've not changed functionality at some point"""
        class TestInline(OneToOneStackedInline):
            model = User
        o2o = TestInline(ContentType, site)
        self.assertEqual(o2o.extra, 1)
        self.assertEqual(o2o.max_num, 1)
        self.assertEqual(o2o.can_delete, False)
        self.assertEqual(o2o.formset, RequiredInlineFormSet)

    def test_our_tabular_inline(self):
        """Just make sure I've not changed functionality at some point"""
        class TestInline(OneToOneTabularInline):
            model = User
        o2o = TestInline(ContentType, site)
        self.assertEqual(o2o.extra, 1)
        self.assertEqual(o2o.max_num, 1)
        self.assertEqual(o2o.can_delete, False)
        self.assertEqual(o2o.formset, RequiredInlineFormSet)


class RegionAdminTestCase(TestCase):

    def setUp(self):
        self.region_admin = RegionAdmin()
        self.region_admin.edit_regions = ['test1', 'test-2', 'test_3']

    def test_get_regions(self):
        """Our list of regions should be the same as those bound to `edit_regions`"""
        req = RequestFactory().get('/')
        actual = self.region_admin.get_regions(request=req, obj=True)
        expected = ['test1', 'test-2', 'test_3']
        self.assertEqual(expected, actual)

    def test_get_regions_gone_bad(self):
        """Should throw a ValidationError for having stupid named regions"""
        self.region_admin.edit_regions = ['te!st1', 't/est-2', 'test_3']
        req = RequestFactory().get('/')
        with self.assertRaises(ValidationError):
            self.region_admin.get_regions(request=req, obj=True)

    def test_get_region_name(self):
        """Get the pretty region name"""
        req = RequestFactory().get('/')
        for region in self.region_admin.get_regions(request=req, obj=True):
            self.region_admin.get_region_name(region)

    def test_get_region_name_bad(self):
        """Bad region names"""
        with self.assertRaises(ValidationError):
            self.region_admin.get_region_name('te!st1')

        with self.assertRaises(ValidationError):
            self.region_admin.get_region_name('t/est-2')

        with self.assertRaises(ValidationError):
            self.region_admin.get_region_name('t\est-2')


    def test_get_region_widget(self):
        result = self.region_admin.get_region_widget(User, 'test1')
        self.assertEqual('admin/editregions/widgets/chunk_list.html', result.template)
        self.assertFalse(result.is_required)
        self.assertTrue(result.attrs['show_add'])
        self.assertTrue(result.attrs['show_plugins'])
        self.assertEqual('test1', result.attrs['region']['name'])
        self.assertEqual('wtf', result.attrs['region']['verbose_name'])
        self.assertTrue(result.render(name='test', value=1, attrs=None))
