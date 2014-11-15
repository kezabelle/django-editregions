# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='File',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('data', models.FileField(upload_to='editregions/files', verbose_name='file')),
                ('title', models.CharField(help_text='Optional text to display instead of the filename', max_length=255, null=True, verbose_name='title', blank=True)),
            ],
            options={
                'verbose_name': 'File',
                'verbose_name_plural': 'Files',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
    ]
