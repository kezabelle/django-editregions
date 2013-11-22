# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'Iframe'
        db.create_table('embeds_iframe', (
            ('editregionchunk_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['editregions.EditRegionChunk'], unique=True, primary_key=True)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=2048)),
            ('height', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('width', self.gf('django.db.models.fields.PositiveIntegerField')(default=None, null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('embeds', ['Iframe'])


    def backwards(self, orm):

        # Deleting model 'Iframe'
        db.delete_table('embeds_iframe')


    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'editregions.editregionchunk': {
            'Meta': {'ordering': "['position']", 'object_name': 'EditRegionChunk'},
            'content_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'position': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'db_index': 'True'}),
            'region': ('django.db.models.fields.CharField', [], {'max_length': '75'}),
            'subcontent_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'to': "orm['contenttypes.ContentType']"})
        },
        'embeds.iframe': {
            'Meta': {'ordering': "['position']", 'object_name': 'Iframe', '_ormbases': ['editregions.EditRegionChunk']},
            'editregionchunk_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['editregions.EditRegionChunk']", 'unique': 'True', 'primary_key': 'True'}),
            'height': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '2048'}),
            'width': ('django.db.models.fields.PositiveIntegerField', [], {'default': 'None', 'null': 'True'})
        }
    }

    complete_apps = ['embeds']
