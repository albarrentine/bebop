'''
Created on Jan 21, 2011

@author: al
'''

from schema import SolrSchema, SolrSchemaFields, SolrFieldTypes
from model import Field
from config import StandardSolrConfig

def has_own_constructor(cls):
    # There's also this awesome black magic-ish statement:
    # sum([cls.__init__ == base.__init__ for base in cls.__mro__[1:]]) == 0
    # but I'm not going to mess around with people's inheritance
    return hasattr(cls, '__init__') and cls.__init__ != object.__init__

def SearchIndex(name, config=StandardSolrConfig, generate_schema=True):
    def _to_dict(self):
        return dict([(v, getattr(self, k)) for k, v in self._models_to_solr.iteritems()])

    def _create_target_model(self):
        return self._target(**dict([(k, v) for k,v in self._solr_to_models.iteritems()]))

    def default_constructor(self, obj=None, **kw):
        arg_dict = obj if hasattr(obj, 'iteritems') else obj.__dict__
        arg_dict.update(kw)
        for attr, value in arg_dict.iteritems():
            if attr in self._solr_fields:
                setattr(self, attr, value)

    def _Index(cls):
        cls.__solr_index__ = name
        #if not hasattr(cls, '_target') or cls._target is None:
        #    raise Exception('Class "%s" must have attribute _target' % cls.__name__)
        fields = filter(lambda attr: isinstance(getattr(cls,attr), Field), dir(cls))
        cls._solr_fields = fields
        cls._models_to_solr = dict([(field, getattr(cls, field).solr_field_name) for field in fields])
        cls._solr_to_models = dict([(v,k) for k,v in cls._models_to_solr.iteritems()])

        cls.solr_schema=None
        if generate_schema:
            field_types=set()
            schema_fields=[]
            for attr in fields:
                schema_fields.append(getattr(cls, attr))
                field_types.add(getattr(cls,attr)._solr_field_type)

        cls.solr_schema=SolrSchema(name=name,
                                  fields=SolrSchemaFields(*schema_fields),
                                  field_types=SolrFieldTypes(*field_types)
                                  )
        cls.solr_config=config

        cls._to_dict = _to_dict
        cls._create_target_model = _create_target_model

        if not has_own_constructor(cls) :
            cls.__init__ = default_constructor
        return cls
    return _Index
