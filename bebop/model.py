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
    
    def _op(self, *components):
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

def and_(*args):
    return '(' + ' AND '.join(args) + ')'

def or_(*args):
    return '(' + ' OR '.join(args) + ')' 
    
class DocumentId(Field):
    def __init__(self, name, type):
        return super(DocumentId, self).__init__(name, type, doc_id = True)
    
    