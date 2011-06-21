'''
Created on Feb 14, 2011

@author: al
'''

from bebop import *
import bebop.test
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
    id = DocumentId('id', Integer, model_attr='id')
    name = Field('name', Title, model_attr='name')

@SearchIndex('bar', config=DismaxSolrConfig)
class Bar(object):
    id = DocumentId('id', Integer, model_attr='id')
    name = Field('name', Title, model_attr='name')

class TestModel(TestCase):

    def test_internals(self):
        self.assertEquals(Foo.__solr_index__, 'foo')
        self.assertEquals(Foo._solr_fields, ['id', 'name'])

    def test_equals(self):
        clause = Foo.name == 'blah'
        self.assertEquals(clause, "name:blah")

    def test_boolean_clause(self):
        clause = and_(Foo.id > 5, or_(Foo.name=='blah', Foo.name=='blee'))
        self.assertEquals(clause, "(id:[5 TO *] AND (name:blah OR name:blee))")

    def test_search_url(self):
        solr = Solr()
        solr.autodiscover_indexes(bebop.test)
        q = solr.search(Bar).query('baz').filter(Bar.id>10).fields(Bar.name).limit(10).offset(5)
        self.assertEquals(q.params.items(), [('q', 'baz'),('fq', 'id:[10 TO *]'),('fl', ['name']),('rows',10),('start',5)] )