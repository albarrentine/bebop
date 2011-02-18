'''
Created on Jan 21, 2011

@author: al
'''

from connection import *

def Index(name):
    def _Index(cls):
        cls.__index__ = name
        fields = filter(lambda attr: isinstance(getattr(cls,attr), Field), dir(cls))
        cls._fields = fields
        cls._models_to_solr = dict([(field, getattr(cls, field).name) for field in fields])
        cls._solr_to_models = dict([(v,k) for k,v in cls._models_to_solr.iteritems()])
        return cls
    return _Index

class SolrModel(object):
    def __init__(self, **kw):
        self._dict = kw
        for k,v in kw.iteritems():
            setattr(self, k, v)

class Field(object):
    def __init__(self, name, type, doc_id=False):
        self.name = name
        self.type = type
    
    def _op(self, *components):
        # TODO: probably need some serialization crap in here
        components = [self.name,':'] + [unicode(component) for component in components]
        return ''.join(components)
    
    def __gt__(self, other):
        return self._op('[',other,' TO *]')

    def __lt__(self, other):
        return self._op('[* TO ',other,']')
    
    def __gte__(self, other):
        return self.__gt__(self, other)
    
    def __lte__(self, other):
        return self.__lt__(other)
    
    def __eq__(self, other):
        return self._op(other)

    def between(self, lower, upper):
        return self._op('[', lower, ' TO ', upper, ']')

    def exists(self):
        return self._op('[* TO *]')

def and_(*args):
    return '(' + ' AND '.join(args) + ')'

def or_(*args):
    return '(' + ' OR '.join(args) + ')' 

class DocumentId(Field):
    def __init__(self, name, type):
        return super(DocumentId, self).__init__(name, type, doc_id = True)    