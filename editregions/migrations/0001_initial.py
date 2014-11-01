# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import editregions.utils.regions


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EditRegionChunk',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('content_id', models.CharField(max_length=255, db_index=True)),
                ('region', models.CharField(max_length=75, validators=[editregions.utils.regions.validate_region_name])),
                ('position', models.PositiveIntegerField(default=None, db_index=True)),
                ('content_type', models.ForeignKey(related_name='+', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ['position'],
                'abstract': False,
                'db_table': 'editregions_editregionchunk',
                'verbose_name': 'content block',
                'verbose_name_plural': 'content blocks',
            },
            bases=(models.Model,),
        ),
    ]
