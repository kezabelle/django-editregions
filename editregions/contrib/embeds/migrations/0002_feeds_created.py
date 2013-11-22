# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Feed'
        db.create_table(u'embeds_feed', (
            (u'editregionchunk_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['editregions.EditRegionChunk'], unique=True, primary_key=True)),
            ('max_num', self.gf('django.db.models.fields.PositiveIntegerField')(default=5)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2048)),
            ('cache_for', self.gf('django.db.models.fields.PositiveIntegerField')(default=86400)),
        ))
        db.send_create_signal(u'embeds', ['Feed'])


    def backwards(self, orm):
        # Deleting model 'Feed'
        db.delete_table(u'embeds_feed')


    models = {
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'editregions.editregionchunk': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'EditRegionChunk'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': u"orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'db_index': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '75'})
        },
        u'embeds.feed': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'Feed', '_ormbases': [u'editregions.EditRegionChunk']},
            'cache_for': ('django.db.models.fields.PositiveIntegerField', [], {'default': '86400'}),
            u'editregionchunk_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['editregions.EditRegionChunk']", 'unique': 'True', 'primary_key': 'True'}),
            'max_num': ('django.db.models.fields.PositiveIntegerField', [], {'default': '5'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'})
        },
        u'embeds.iframe': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'Iframe', '_ormbases': [u'editregions.EditRegionChunk']},
            u'editregionchunk_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['editregions.EditRegionChunk']", 'unique': 'True', 'primary_key': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['embeds']