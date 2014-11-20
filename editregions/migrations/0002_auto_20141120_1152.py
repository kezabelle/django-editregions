# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='editregionchunk',
            options={'verbose_name_plural': 'content blocks', 'verbose_name': 'content block', 'ordering': ['position', '-modified']},
        ),
        migrations.AlterIndexTogether(
            name='editregionchunk',
            index_together=set([('content_type', 'content_id', 'region')]),
        ),
    ]
