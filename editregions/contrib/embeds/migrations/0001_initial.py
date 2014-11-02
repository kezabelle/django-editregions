# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editregions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('max_num', models.PositiveIntegerField(default=5, verbose_name='')),
                ('url', models.URLField(help_text='Required. The URL for the content you want to embed.', max_length=2048, verbose_name='web address')),
                ('cache_for', models.PositiveIntegerField(default=86400, help_text="Save the data into the server's cache for a period of time, allowing the page to respond faster. After the period has elapsed, the next page request will fetch any new data.", verbose_name='stale after', choices=[(86400, 'One day'), (43200, 'Twelve hours'), (24600, 'Six hours'), (3600, 'One hour')])),
            ],
            options={
                'verbose_name': 'web feed',
                'verbose_name_plural': 'web feeds',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='Iframe',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('url', models.URLField(help_text='Required. The URL for the content you want to embed.', max_length=2048, verbose_name='web address')),
                ('height', models.PositiveIntegerField(default=None, help_text='Optional. If the website allows for it, may beused to set the dimensions of this iframe.', null=True, blank=True)),
                ('width', models.PositiveIntegerField(default=None, help_text='Optional. If the website allows for it, may beused to set the dimensions of this iframe.', null=True, blank=True)),
                ('name', models.CharField(help_text='Optional. May be used to reference the element in JavaScript, or as the target for a link or form.', max_length=255, verbose_name='HTML name', blank=True)),
            ],
            options={
                'verbose_name': 'iframe',
                'verbose_name_plural': 'iframes',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='JavaScript',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('content', models.TextField()),
            ],
            options={
                'verbose_name': 'JavaScript',
                'verbose_name_plural': 'JavaScripts',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='JavascriptAsset',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('local', models.CharField(max_length=2048, blank=True)),
                ('external', models.CharField(max_length=2048, blank=True)),
            ],
            options={
                'verbose_name': 'javascript file',
                'verbose_name_plural': 'javascript files',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
        migrations.CreateModel(
            name='StylesheetAsset',
            fields=[
                ('editregionchunk_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='editregions.EditRegionChunk')),
                ('local', models.CharField(max_length=2048, blank=True)),
                ('external', models.CharField(max_length=2048, blank=True)),
            ],
            options={
                'verbose_name': 'stylesheet file',
                'verbose_name_plural': 'stylesheet files',
            },
            bases=('editregions.editregionchunk', models.Model),
        ),
    ]
