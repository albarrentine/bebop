'''
Created on Jun 20, 2011

@author: al
'''

import schema
from query import LuceneQuery

class BaseField(schema.SolrSchemaField):
    def __init__(self, name, solr_field_type=None, multi_valued=None, document_id=False, indexed=None, stored=None, model_attr=None, **kw):
        if solr_field_type is not None:
            self.solr_field_type = solr_field_type

        self._solr_field_type = self.solr_field_type
        super(BaseField, self).__init__(solr_field_name=name, solr_field_type=self.solr_field_type, **kw)
        if document_id:
            self.unique_key = schema.UniqueKey(name)

        if indexed is not None:
            self.indexed = indexed
        if stored is not None:
            self.stored = stored
        if multi_valued is not None:
            self.multi_valued = multi_valued
        if model_attr:
            self._model_attr = model_attr

class Field(BaseField):
    def __gt__(self, other):
        return LuceneQuery(self, '{', other, ' TO *}')

    def __lt__(self, other):
        return LuceneQuery(self, '{* TO ', other, '}')

    def __ge__(self, other):
        return LuceneQuery(self, '[', other, ' TO *]')

    def __le__(self, other):
        return LuceneQuery(self, '[* TO ', other, ']')

    def __ne__(self, other):
        return LuceneQuery(self, other).negate()

    def __eq__(self, other):
        return LuceneQuery(self, other)

    def __pow__(self, power):
        return LuceneQuery(self) ** power

    def between(self, lower, upper, inclusive_lower=True, inclusive_upper=True):
        return LuceneQuery(self, '[' if inclusive_lower else '{', lower, ' TO ', upper, ']' if inclusive_upper else '}')

    def exists(self):
        return LuceneQuery(self, '[* TO *]')

    def __unicode__(self):
        return self.solr_field_name

class DynamicField(BaseField):
    tag = 'dynamicField'

def and_(*args):
    return '(' + ' AND '.join([unicode(arg) for arg in args]) + ')'

def or_(*args):
    return '(' + ' OR '.join([unicode(arg) for arg in args]) + ')'



class StrField(Field):
    solr_field_type = schema.String

class UUIDField(Field):
    solr_field_type = schema.UniqueId

class BooleanField(Field):
    solr_field_type = schema.Boolean

class DateField(Field):
    solr_field_type = schema.Date

class RandomField(Field):
    solr_field_type = schema.Random

class SortableOptionField(Field):
    def __init__(self, name, sortable=False, **kw):
        if sortable:
            self.solr_field_type = self._sortable_type
        else:
            self.solr_field_type = self._non_sortable_type
        super(SortableOptionField, self).__init__(name, **kw)

class IntegerField(SortableOptionField):
    _sortable_type = schema.SortableInteger
    _non_sortable_type = schema.Integer

class LongField(SortableOptionField):
    _sortable_type = schema.SortableLong
    _non_sortable_type = schema.Long

class FloatField(SortableOptionField):
    _sortable_type = schema.SortableLong
    _non_sortable_type = schema.Long

class DoubleField(SortableOptionField):
    _sortable_type = schema.SortableDouble
    _non_sortable_type = schema.Double



class TextField(Field):
    def __init__(self, name, type=schema.Text, **kw):
        self.solr_field_type = type
        super(TextField, self).__init__(name, **kw)

class TitleField(TextField):
    """ Use this for names """
    def __init__(self, name, **kw):
        super(TitleField, self).__init__(name, type=schema.Title, **kw)

class IgnoredField(Field):
    solr_field_type = schema.Ignored

class PointField(Field):
    solr_field_type = schema.Point
    def __init__(self, name, **kw):
        self.siblings = set([DynamicField("*%s" % self.solr_field_type.sub_field_suffix,
                                                    schema.TrieDouble, stored=False)])
        super(PointField, self).__init__(name, **kw)

class GeoPointField(Field):
    solr_field_type = schema.GeoPoint
    def __init__(self, name, **kw):
        self.siblings = set([DynamicField("*%s" % self.solr_field_type.sub_field_suffix,
                                                    schema.TrieDoubleRange, stored=False)])
        super(GeoPointField, self).__init__(name, **kw)

    def bounding_box(self, lat, lon, distance):
        pass

    def distance_from(self, lat, lon):
        pass

class GeoHashField(Field):
    solr_field_type = schema.GeoHash
