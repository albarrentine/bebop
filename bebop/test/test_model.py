'''
Created on Feb 14, 2011

@author: al
'''

from bebop import *
from unittest import TestCase

@Index('foo')
class Foo(object):
    id = DocumentId('id', Integer)
    name = Field('name', Title)
    
class TestModel(TestCase):

    def test_internals(self):
        self.assertEquals(Foo.__index__, 'foo')
        self.assertEquals(Foo.__fields__, ['id', 'name'])

    def test_equals(self):
        clause = Foo.name == 'blah'
        self.assertEquals(clause, "name: blah")

    def test_boolean_clause(self):
        clause = and_(Foo.id > 5, or_(Foo.name=='blah', Foo.name=='blee'))
        self.assertEquals(clause, "(id > 5 and (name: blah or name: blee))")