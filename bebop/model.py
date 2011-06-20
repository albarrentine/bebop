'''
Created on Jan 21, 2011

@author: al
'''

from connection import *
from schema import *
from config import *

def SearchIndex(name, config=StandardSolrConfig, generate_schema=True):
    def _to_solr_doc(self):
        return dict([(v, getattr(self, k)) for k, v in self._models_to_solr.iteritems()])

    def _create_target_model(self):
        return self._target(**dict([(k, v) for k,v in self._solr_to_models.iteritems()]))

    def _Index(cls):
        cls.__solr_index__ = name
        #if not hasattr(cls, '_target') or cls._target is None:
        #    raise Exception('Class "%s" must have attribute _target' % cls.__name__)
        fields = filter(lambda attr: isinstance(getattr(cls,attr), Field), dir(cls))
        cls._fields = fields
        cls._models_to_solr = dict([(field, getattr(cls, field).name) for field in fields])
        cls._solr_to_models = dict([(v,k) for k,v in cls._models_to_solr.iteritems()])

        cls.schema=None
        if generate_schema:
            field_types=set()
            schema_fields=[]
            for attr in fields:
                schema_fields.append(getattr(cls, attr))
                field_types.add(getattr(cls,attr)._type)

            cls.schema=SolrSchema(name=name,
                                  fields=SolrSchemaFields(*schema_fields),
                                  field_types=SolrFieldTypes(*field_types)
                                  )
        cls.config=config
        cls._to_solr_doc = _to_solr_doc
        cls._create_target_model = _create_target_model
        return cls
    return _Index

class Field(SolrSchemaField):
    def __init__(self, name, type, multi_valued=None, indexed=None, stored=None, model_attr=None):
        super(Field, self).__init__(name=name, type=type)
        self._type = type
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
    def __init__(self, name, type, model_attr=None):
        self.unique_key = UniqueKey(name)
        return super(DocumentId, self).__init__(name, type, model_attr=model_attr)