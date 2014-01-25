# -*- coding: utf-8 -*-
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.forms import Media
from django.forms.util import ErrorList
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase, RequestFactory
from editregions.admin.forms import EditRegionInlineForm, EditRegionInlineFormSet, MovementForm
from editregions.models import EditRegionChunk
from editregions.utils.data import get_content_type


class TestUserAdmin(UserAdmin):
    def get_editregions_templates(self, obj):
        return ['movable_editregion_template.html']


class EditRegionInlineFormTestCase(TestCase):
    def test_basic(self):
        form = EditRegionInlineForm()
        self.assertEqual(form.media.render(), Media().render())


class EditRegionInlineFormSetTestCase(DjangoTestCase):
    def test_basic(self):
        formset = EditRegionInlineFormSet(queryset=User.objects.none())
        self.assertEqual(EditRegionInlineFormSet.get_default_prefix(),
                         'edit_region_chunk_formset')
        self.assertEqual(list(formset.get_queryset()),
                         list(User.objects.none()))
        with self.assertNumQueries(0):
            self.assertTrue(formset.save())
        self.assertEqual(formset.non_form_errors(), ErrorList())
        self.assertTrue(formset.is_valid())


class MovementFormTestCase(DjangoTestCase):
    def setUp(self):
        user = User(username='test')
        user.set_password('test')
        user.full_clean()
        user.save()
        user_ct = get_content_type(User)
        for x in range(0, 10):
            chunk = EditRegionChunk(position=x, region='test',
                                    content_id=user.pk, content_type=user_ct)
            chunk.full_clean()
            chunk.save()
        self.user = user

    def test_usage(self):
        form = MovementForm()
        self.assertEqual(10, form.fields['pk'].max_value)

    def test_cleaning_no_pk(self):
        request = RequestFactory().post('/', {'position': 3})
        form = MovementForm(data=request.POST)
        form.is_valid()
        self.assertEqual(form._errors, {'pk': 'content block does not exist'})
        self.assertEqual(form.cleaned_data, {'pk': None,
                                             'position': 3,
                                             'region': u''})

    def test_cleaning_with_pk(self):
        obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().post('/', {'position': 3, 'pk': obj.pk})
        form = MovementForm(data=request.POST)
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        form.is_valid()
        self.assertEqual(form._errors, {})
        self.assertEqual(form.cleaned_data, {'pk': obj,
                                             'position': 3,
                                             'region': 'test'})

    def test_moving_position_only(self):
        obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().post('/', {'position': 3, 'pk': obj.pk})
        form = MovementForm(data=request.POST)
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        form.is_valid()
        with self.assertNumQueries(4):
            result = form.save()
            self.assertEqual(result.pk, obj.pk)
            self.assertNotEqual(result.position, obj.position)
            self.assertEqual(result.position, 3)

    def test_moving_position_and_region(self):
        obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().post('/', {'position': 3, 'pk': obj.pk,
                                              'region': 'test2'})
        form = MovementForm(data=request.POST)
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        form.is_valid()
        with self.assertNumQueries(6):
            result = form.save()
            self.assertEqual(result.pk, obj.pk)
            self.assertNotEqual(result.position, obj.position)
            self.assertEqual(result.position, 3)
            self.assertNotEqual(result.region, obj.region)
            self.assertEqual(result.region, 'test2')

    def test_moving_to_invalid_region(self):
        obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().post('/', {'position': 1, 'pk': obj.pk,
                                              'region': 'NOPE'})
        form = MovementForm(data=request.POST)
        try:
            admin.site.unregister(User)
        except NotRegistered:
            pass
        admin.site.register(User, TestUserAdmin)
        form.is_valid()

        # no-op to DB
        with self.assertNumQueries(0):
            result = form.save()
            self.assertEqual(result.pk, obj.pk)
            self.assertEqual(result.position, obj.position)
            self.assertEqual(result.position, 1)
            self.assertEqual(result.region, obj.region)
            self.assertEqual(result.region, 'test')

    def test_messages(self):
        obj = EditRegionChunk.objects.all()[0]
        request = RequestFactory().post('/', {'position': 3, 'pk': obj.pk,
                                              'region': 'test'})
        form = MovementForm(data=request.POST)
        form.is_valid()
        obj2, message = form.change_message()
        self.assertEqual(message, 'Moved to position 1 in region "test"')
        self.assertEqual(obj2, obj)

        obj2, message = form.parent_change_message()
        self.assertEqual(message, 'Moved content block (pk: 1) to position 1 '
                                  'in region "test"')
        self.assertEqual(obj2, self.user)
