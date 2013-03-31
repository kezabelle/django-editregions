# -*- coding: utf-8 -*-
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from django.forms import Form, Media
from django.http import QueryDict
import re
from django.forms.fields import TypedMultipleChoiceField, TypedChoiceField
from editregions.models import EditRegionChunk
from editregions.utils.data import queryset_to_attr_map


class EditRegionInlineForm(object):
    media = Media()


class EditRegionInlineFormSet(object):
    initial_forms = []
    extra_forms = []
    media = Media(css={
        'screen': [
            'admin/css/editregions.css',
        ]
    })
    empty_form = EditRegionInlineForm()

    # used for constructing change messages
    new_objects = []
    changed_objects = []
    deleted_objects = []

    @classmethod
    def get_default_prefix(cls):
        return 'edit_region_chunk_formset'

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def get_queryset(self, *args, **kwargs):
        return self.kwargs['queryset']

    def is_valid(self, *args, **kwargs):
        return True

    def save(self, *args, **kwargs):
        return True


class ReorderChunksForm(Form):
    model = EditRegionChunk
    items = TypedMultipleChoiceField(coerce=int, choices=())

    def __init__(self, content_type, obj_id, *args, **kwargs):
        super(ReorderChunksForm, self).__init__(*args, **kwargs)
        self.fields['items'].choices = ((x.pk, unicode(x.pk))
            for x in self.model.objects.filter(content_type=content_type,
                content_id=obj_id).only('id'))

        # Fix the stupid incoming data format.
        incoming_data = self.data.copy()
        # jQuery uses an underscore to avoid browser caching.
        uncache = u'_'
        if uncache in incoming_data:
            del incoming_data[uncache]
        # this should probably be in validation.
        assert len(incoming_data) == 1, "Unexpected data received"
        data_values = incoming_data.popitem()[1]
        nondigits = re.compile(r'[^\d]+')
        data_for_binding = ['items=%d' % int(nondigits.sub('', x))
                            for x in data_values if x]
        self.data = QueryDict('&'.join(data_for_binding), mutable=False)

    def save(self):
        items = self.cleaned_data['items']
        chunks_affected = self.model.objects.filter(pk__in=items)
        chunk_map = queryset_to_attr_map(chunks_affected, 'pk')
        for new_position, chunk in enumerate(self.cleaned_data['items']):
            real_obj = chunk_map[chunk]
            real_obj.position = new_position
            real_obj.save()
        return True


class MovementForm(Form):
    model = EditRegionChunk
    region = TypedChoiceField(coerce=unicode, choices=())

    def __init__(self, region, *args, **kwargs):
        super(MovementForm, self).__init__(*args, **kwargs)
        self.fields['region'].choices = ((1, 1,), (2, 2),)
