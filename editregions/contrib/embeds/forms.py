# -*- coding: utf-8 -*-
import logging
from django.forms import ModelForm, TypedChoiceField
from django.db.models import BLANK_CHOICE_DASH
from django_ace import AceWidget
from .utils import static_asset_choices
from .models import JavascriptAsset, StylesheetAsset

logger = logging.getLogger(__name__)


class JavaScriptEditorForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(JavaScriptEditorForm, self).__init__(*args, **kwargs)
        self.fields['content'].widget = AceWidget(mode='javascript',
                                                  theme='chrome')


class AssetSourceForm(ModelForm):
    local = TypedChoiceField(choices=(), coerce=str, required=False)
    only_patterns = ()

    def __init__(self, *args, **kwargs):
        if 'only_patterns' in kwargs:
            self.only_patterns = kwargs.pop('only_patterns')
        super(AssetSourceForm, self).__init__(*args, **kwargs)
        found_assets = tuple(static_asset_choices(
            only_patterns=self.only_patterns))
        assets_count = len(found_assets)
        if self.fields['local']:
            self.fields['local'].choices = found_assets
            if assets_count == 0:
                self.fields['local'].choices = BLANK_CHOICE_DASH


class StylesheetAssetForm(AssetSourceForm):
    only_patterns = ('editregions/embeds/*.css',)

    class Meta:
        model = StylesheetAsset


class JavascriptAssetForm(AssetSourceForm):
    only_patterns = ('editregions/embeds/*.js',)

    class Meta:
        model = JavascriptAsset
