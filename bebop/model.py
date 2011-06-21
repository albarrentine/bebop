'''
Created on Jun 20, 2011

@author: al
'''

from schema import SolrSchemaField, UniqueKey

class Field(SolrSchemaField):
    def __init__(self, name, type, multi_valued=None, indexed=None, stored=None, model_attr=None):
        super(Field, self).__init__(solr_field_name=name, solr_field_type=type)
        self._solr_field_type = type
        if indexed is not None:
            self.indexed = indexed
        if stored is not None:
            self.stored = stored
        if multi_valued is not None:
            self.multi_valued = multi_valued
        if model_attr:
            self._model_attr = model_attr

    def _op(self, *components):
        # TODO: probably need some serialization crap in here
        components = [self.solr_field_name,':'] + [unicode(component) for component in components]
        return ''.join(components)

    def __gt__(self, other):
        return self._op('[',other,' TO *]')

    def __lt__(self, other):
        return self._op('[* TO ',other,']')

    def __gte__(self, other):
        return self._op('[',other,' TO *]')

    def __lte__(self, other):
        return self._op('[* TO ',other,']')

    def __eq__(self, other):
        return self._op(other)

    def __pow__(self, power):
        return '%s^%s' % (self.solr_field_name, power)

    def between(self, lower, upper):
        return self._op('[', lower, ' TO ', upper, ']')

    def exists(self):
        return self._op('[* TO *]')

def and_(*args):
    return '(' + ' AND '.join(args) + ')'

def or_(*args):
    return '(' + ' OR '.join(args) + ')'

class DocumentId(Field):
    def __init__(self, name, type, model_attr=None):
        self.unique_key = UniqueKey(name)
        return super(DocumentId, self).__init__(name, type, model_attr=model_attr)
