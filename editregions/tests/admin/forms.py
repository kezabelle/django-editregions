# -*- coding: utf-8 -*-
from django.contrib.auth.models import User
from django.forms import Media
from django.forms.util import ErrorList
from django.utils.unittest.case import TestCase
from django.test import TestCase as DjangoTestCase, RequestFactory
from editregions.admin.forms import EditRegionInlineForm, EditRegionInlineFormSet, MovementForm
from editregions.models import EditRegionChunk


class EditRegionInlineFormTestCase(TestCase):
    def test_basic(self):
        form = EditRegionInlineForm()
        self.assertEqual(form.media.render(), Media().render())


class EditRegionInlineFormSetTestCase(DjangoTestCase):
    def test_basic(self):
        formset = EditRegionInlineFormSet(queryset=User.objects.none())
        self.assertEqual(EditRegionInlineFormSet.get_default_prefix(),
                         'edit_region_chunk_formset')
        self.assertQuerysetEqual(formset.get_queryset(),
                                 User.objects.none())
        with self.assertNumQueries(0):
            self.assertTrue(formset.save())
        self.assertEqual(formset.non_form_errors(), ErrorList())
        self.assertTrue(formset.is_valid())


class MovementFormTestCase(DjangoTestCase):
    def setUp(self):
        for x in range(0, 10):
            chunk = EditRegionChunk(position=x, region='test', content_id=1,
                                    content_type_id=1)
            chunk.full_clean()
            chunk.save()

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
