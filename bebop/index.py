'''
Created on Jan 21, 2011

@author: al
'''

from connection import *
from schema import *
from query import *
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
        cls._solr_fields = fields
        cls._models_to_solr = dict([(field, getattr(cls, field).name) for field in fields])
        cls._solr_to_models = dict([(v,k) for k,v in cls._models_to_solr.iteritems()])

        cls.solr_schema=None
        if generate_schema:
            field_types=set()
            schema_fields=[]
            for attr in fields:
                schema_fields.append(getattr(cls, attr))
                field_types.add(getattr(cls,attr)._type)

        cls.solr_schema=SolrSchema(name=name,
                                  fields=SolrSchemaFields(*schema_fields),
                                  field_types=SolrFieldTypes(*field_types)
                                  )
        cls.solr_config=config

        cls._to_solr_doc = _to_solr_doc
        cls._create_target_model = _create_target_model
        return cls
    return _Index
