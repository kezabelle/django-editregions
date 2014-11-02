# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MetaElement',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('name', models.CharField(max_length=50, choices=[(b'title', b'Title'), (b'description', b'Description'), (b'keywords', b'Keywords')])),
                ('content', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=('editregions.editregionchunk',),
        ),
    ]
