'''
Created on Feb 14, 2011

@author: al
'''

from solr_bebop import *
import solr_bebop.test
from unittest import TestCase

class FooDB(object):
    def __init__(self, **kw):
        for attr, val in kw.iteritems():
            setattr(self, attr, val)

class BarDB(object):
    def __init__(self, **kw):
        for attr, val in kw.iteritems():
            setattr(self, attr, val)

@SearchIndex('foo')
class Foo(object):
    id = model.IntegerField('id', model_attr='id', document_id=True)
    name = model.TitleField('name', model_attr='name')

@SearchIndex('bar', config=DismaxSolrConfig)
class Bar(object):
    id = model.IntegerField('id', model_attr='id', document_id=True)
    name = model.TitleField('name', model_attr='name')

class TestModel(TestCase):
    def test_internals(self):
        self.assertEquals(Foo.__solr_index__, 'foo')
        self.assertEquals(Foo._solr_fields, ['id', 'name'])

    def test_equals(self):
        clause = Foo.name == 'blah'
        self.assertEquals(unicode(clause), "name:blah")

    def test_boolean_clause(self):
        clause = and_(Foo.id > 5, or_(Foo.name=='blah', Foo.name=='blee'))
        self.assertEquals(unicode(clause), u"(id:{5 TO *} AND (name:blah OR name:blee))")

    def test_search_url(self):
        solr = Solr()
        solr.autodiscover_indexes(solr_bebop.test)
        q = solr.search(Bar).query('baz').filter(Bar.id>=10).fields(Bar.name).limit(10).offset(5)
        self.assertEquals(q.join_params().items(), [('q', u'baz'),('fq', u'id:[10 TO *]'),('fl', u'name'),('rows',u'10'),('start',u'5')] )
