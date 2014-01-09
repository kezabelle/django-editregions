# -*- coding: utf-8 -*-
from django.contrib.staticfiles.finders import get_finders
from django.contrib.staticfiles.utils import matches_patterns


def static_asset_choices(only_patterns):
    for finder in get_finders():
        for file, storage in finder.list(ignore_patterns=()):
            if matches_patterns(file, only_patterns):
                yield file, file
