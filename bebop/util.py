'''
Created on Jan 19, 2011

@author: al
'''

from lxml import etree
from lxml import builder
from lxml import objectify
import os

E = objectify.ElementMaker(annotate=False)

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

    
def memoize(f):
    arg_cache = {}
    def _new_f(arg):
        cache_it = True
        try:
            cached = arg_cache.get(arg, None)
            if cached is not None:
                return cached
        except TypeError:
            cache_it = False
        uncached = f(arg)
        if cache_it:
            arg_cache[arg] = uncached
        return uncached
    return _new_f

class classproperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def _to_camelcase(s):
    return ''.join([token.title() if i > 0 else token.lower() 
                    for i, token in enumerate(s.split('_'))])
    
@memoize
def _stringify(obj):
    # TODO: write your own PyObject > string conversion
    # or find a better way to do this
    return E._dummy_node(obj).text

def _sorted_update(elem, d):
    elem.attrib.update(sorted(d.iteritems()))

def _to_xml(obj):
    definitions = {}
    options = {}
        
    element = etree.Element(obj.tag)

    for attr, transformed in obj.required.iteritems():
        definitions[transformed] = _stringify(getattr(obj, attr))
            
    for attr, value in obj.__dict__.iteritems():
        # Append children first (recursive, but we don't need many levels)
        # TODO: order this correctly, still using an unsorted dict
        if hasattr(value, 'to_xml'):
            element.append(value.to_xml())
        # Example: filters
        # TODO: are there any use cases where this is not the expected behavior?
        elif hasattr(value, '__iter__'):
            i = iter(value)
            first = i.next()
            del(i)
            if hasattr(first, 'to_xml'):
                [element.append(child.to_xml()) for child in value]
        elif attr in obj.required:
            definitions[obj.required[attr]] = _stringify(value)
        elif attr in obj.optional:
            options[obj.optional[attr]] = _stringify(value)
                    
    _sorted_update(element, definitions)
    _sorted_update(element, options)
                
    return element    

class BaseSolrXMLElement(object):
    required = {}
    options = []
    tag = None
        
    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)
            
        # So class.to_xml will return the 
        self.to_xml = self.instance_to_xml
    
    def instance_to_xml(self):
        return _to_xml(self)
    
    @classmethod
    def to_xml(cls):
        return _to_xml(cls)
    
    @classproperty
    @classmethod
    def optional(cls):
        return dict([(attr, _to_camelcase(attr))
                     for attr in cls.options])    

