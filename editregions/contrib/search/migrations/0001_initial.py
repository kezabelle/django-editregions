# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators
import editregions.contrib.search.models


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MoreLikeThis',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('max_num', models.PositiveIntegerField(default=3, help_text='maximum number of items to render.', verbose_name='display', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1000)])),
                ('connection', models.CharField(default='default', help_text='which of the available search connections to use', max_length=50, verbose_name='connection', validators=[editregions.contrib.search.models.configured_haystack_connection])),
                ('request_objects', models.BooleanField(default=False, help_text='if the template requires access to the database objects, tick this to efficiently fetch the objects up front.', verbose_name='fetch objects')),
            ],
            options={
                'verbose_name': 'More like this',
                'verbose_name_plural': 'More like this',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='SearchResults',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('max_num', models.PositiveIntegerField(default=3, help_text='maximum number of items to render.', verbose_name='display', validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(1000)])),
                ('connection', models.CharField(default='default', help_text='which of the available search connections to use', max_length=50, verbose_name='connection', validators=[editregions.contrib.search.models.configured_haystack_connection])),
                ('request_objects', models.BooleanField(default=False, help_text='if the template requires access to the database objects, tick this to efficiently fetch the objects up front.', verbose_name='fetch objects')),
                ('query', models.CharField(help_text='the search terms (or complex query) to use when finding the best matches.', max_length=255, verbose_name='search for')),
                ('boost', models.CharField(blank=True, help_text='comma separated list of words which should be considered more important, when sorting the best matches.', max_length=255, verbose_name='prioritise', validators=[editregions.contrib.search.models.csv_validator])),
            ],
            options={
                'verbose_name': 'Search results',
                'verbose_name_plural': 'Search results',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
    ]
