# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MCE',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('content', models.TextField()),
            ],
            options={
                'verbose_name': 'HTML (TinyMCE)',
                'verbose_name_plural': 'HTML (TinyMCE)',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='WYM',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('content', models.TextField()),
            ],
            options={
                'verbose_name': 'HTML (WYM)',
                'verbose_name_plural': 'HTML (WYM)',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
    ]
