# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'MoreLikeThis'
        db.create_table(u'search_morelikethis', (
            (u'editregionchunk_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['editregions.EditRegionChunk'], unique=True, primary_key=True)),
            ('max_num', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
            ('connection', self.gf('django.db.models.fields.CharField')(default=u'default', max_length=50)),
            ('request_objects', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'search', ['MoreLikeThis'])

        # Adding model 'SearchResults'
        db.create_table(u'search_searchresults', (
            (u'editregionchunk_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['editregions.EditRegionChunk'], unique=True, primary_key=True)),
            ('max_num', self.gf('django.db.models.fields.PositiveIntegerField')(default=3)),
            ('connection', self.gf('django.db.models.fields.CharField')(default=u'default', max_length=50)),
            ('request_objects', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('query', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('boost', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal(u'search', ['SearchResults'])


    def backwards(self, orm):
        # Deleting model 'MoreLikeThis'
        db.delete_table(u'search_morelikethis')

        # Deleting model 'SearchResults'
        db.delete_table(u'search_searchresults')


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
        u'search.morelikethis': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'MoreLikeThis', '_ormbases': [u'editregions.EditRegionChunk']},
            'connection': ('django.db.models.fields.CharField', [], {'default': "u'default'", 'max_length': '50'}),
            u'editregionchunk_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['editregions.EditRegionChunk']", 'unique': 'True', 'primary_key': 'True'}),
            'max_num': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'request_objects': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'search.searchresults': {
            'Meta': {'ordering': "[u'position']", 'object_name': 'SearchResults', '_ormbases': [u'editregions.EditRegionChunk']},
            'boost': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'connection': ('django.db.models.fields.CharField', [], {'default': "u'default'", 'max_length': '50'}),
            u'editregionchunk_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['editregions.EditRegionChunk']", 'unique': 'True', 'primary_key': 'True'}),
            'max_num': ('django.db.models.fields.PositiveIntegerField', [], {'default': '3'}),
            'query': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'request_objects': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        }
    }

    complete_apps = ['search']