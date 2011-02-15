'''
Created on Jan 21, 2011

@author: al
'''

def Index(name):
    def _Index(cls):
        cls.__index__ = name
        cls.__fields__ = filter(lambda attr: isinstance(getattr(cls,attr), Field), dir(cls))
        return cls
    return _Index

class Model(object):
    __columns__ = {}
    
    def __init__(self):
        self.values = {}    

class Field(object):
    def __init__(self, name, type, doc_id=False):
        self.name = name
        self.type = type
    
    def _op(self, operator, other):
        return ''.join([self.name, operator, unicode(other)])
    
    def __gt__(self, other):
        return self._op(' > ', other)

    def __lt__(self, other):
        return self._op(' < ', other)
    
    def __gte__(self, other):
        return self._op(' >= ', other)
    
    def __lte__(self, other):
        return self._op(' <= ', other)
    
    def __eq__(self, other):
        return self._op(': ', other)

def and_(*args):
    return '(' + ' and '.join(args) + ')'

def or_(*args):
    return '(' + ' or '.join(args) + ')' 
    
class DocumentId(Field):
    def __init__(self, name, type):
        return super(DocumentId, self).__init__(name, type, doc_id = True)