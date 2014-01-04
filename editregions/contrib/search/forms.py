# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.forms import ModelForm, TypedChoiceField
from django.forms.models import modelform_factory
from django.utils.text import capfirst
from editregions.contrib.search.models import MoreLikeThis, SearchResults


def get_haystack_connections():
    connections = getattr(settings, 'HAYSTACK_CONNECTIONS', {})
    for connection, config in connections.items():
        if 'TITLE' in config:
            yield (connection, config.get('TITLE'))
        else:
            yield (connection, capfirst(connection))


class ConnectionForm(ModelForm):
    connection = TypedChoiceField(choices=tuple(get_haystack_connections()),
                                  coerce=str)


MoreLikeThisForm = modelform_factory(model=MoreLikeThis, form=ConnectionForm)
SearchResultsForm = modelform_factory(model=SearchResults, form=ConnectionForm)
