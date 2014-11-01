# -*- coding: utf-8 -*-
import logging
from django.db.models import BLANK_CHOICE_DASH
from django.forms.models import ModelForm
from django.forms import ChoiceField
from django.forms.widgets import Select
from django.utils.translation import ugettext_lazy as _
from .utils import get_markdown_files
from .models import Markdown


logger = logging.getLogger(__name__)


def wrapped_get_markdown_files():
    return [(x, x) for x in get_markdown_files()]


class MarkdownSelectionForm(ModelForm):
    filepath = ChoiceField(choices=(), label=_('filename'))

    def __init__(self, *args, **kwargs):
        super(MarkdownSelectionForm, self).__init__(*args, **kwargs)
        # doing it this way is dynamic, rather than static when the form
        # is instantiated because of the way modules work.
        if 'filepath' in self.fields:
            # we may get an AdminTextInputWidget if no choices are defined
            files = wrapped_get_markdown_files()
            if len(files) < 1:
                logger.debug('No markdown files found by {cls!r}'.format(
                    cls=self))
            choices = BLANK_CHOICE_DASH + files
            self.fields['filepath'].choices = choices
            self.fields['filepath'].widget = Select(choices=choices)

    class Meta:
        model = Markdown
        fields = ['filepath']
