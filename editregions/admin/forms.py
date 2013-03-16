# -*- coding: utf-8 -*-
from django.contrib.contenttypes.generic import BaseGenericInlineFormSet
from django.forms import ModelForm, Textarea
from django.forms.util import ErrorList
from django.http import QueryDict
import re
from django.forms.fields import TypedMultipleChoiceField, TypedChoiceField, Field
from django.forms.forms import Form
from editregions.admin.widgets import ChunkList
from editregions.models import EditRegionChunk
from editregions.utils.data import queryset_to_attr_map


class EditRegionChunkForm(ModelForm):
    region = Field(widget=ChunkList)

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None, region=None):
        super(EditRegionChunkForm, self).__init__(data, files, auto_id, prefix,
            initial, error_class, label_suffix, empty_permitted, instance)

    class Meta:
        model = EditRegionChunk
        # Note; this is never used, because formsets are silly.
        exclude = [] #['content_type', 'content_id', 'subcontent_type', 'position']

class EditRegionChunkFormSet(BaseGenericInlineFormSet):
    pass

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
