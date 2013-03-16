# -*- coding: utf-8 -*-
from django.forms.widgets import Widget
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

class ChunkList(Widget):
    template = 'admin/editregions/widgets/chunk_list.html'
    def render(self, name, value, attrs=None):
        import pdb; pdb.set_trace()
        self.attrs.update(attrs or {})
        return mark_safe(render_to_string(self.template, self.attrs))

class ReadOnlyChunkList(ChunkList):
    """
    For when you need to display non-editable regions.
    """
    template = 'admin/editregions/widgets/chunk_list_readonly.html'
