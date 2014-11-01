# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from templatefinder import find_all_templates


def get_markdown_files():
    return find_all_templates(pattern='*.md')


def valid_md_file(value):
    if value not in get_markdown_files():
        raise ValidationError("Selected markdown file does not exist")
    return True
