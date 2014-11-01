# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import editregions.contrib.textfiles.utils


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Markdown',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('filepath', models.CharField(max_length=255, verbose_name='filename', validators=[editregions.contrib.textfiles.utils.valid_md_file])),
            ],
            options={
                'verbose_name': 'Markdown file',
                'verbose_name_plural': 'Markdown files',
            },
            bases=('editregions.editregionchunk',),
        ),
    ]
