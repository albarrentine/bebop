'''
Created on Jun 16, 2011

@author: al
'''

from schema import SolrSchemaField, UniqueKey
from util import NotGiven, MultiDict
import itertools
from functools import partial

def join_with_separator(separators, param, separator):
    separators[param] = separator
    def _with_func(f):
        return f
    return _with_func


class SolrFunction(object):
    def __init__(self, name):
        self.name = name
        self.args = []

    def __unicode__(self):
        return ''.join([unicode(self.name), '(', ', '.join([unicode(arg) for arg in self.args]), ')'])

    def __pow__(self, power):
        return ''.join([unicode(self), '^', power])

    def __call__(self, *args, **kwargs):
        self.args = args
        return unicode(self)

class _SolrFunctionGenerator(object):
    """
    Inspired by SQLAlchemy

    Since Solr functions may be any random method you wrote
    in Java as well as the standard crop of Solr functions, bebop
    will not assume what the functions you're calling might be.

    End product for now is just a string, and it assumes that
    every argument to the function supports the __unicode__ method

    """
    def __getattr__(self, name):
        if name.startswith('_'):
            try:
                return self.__dict__[name]
            except KeyError:
                raise AttributeError
        # Use a trailing underscore for Python reserved words
        # contrived : func.class_(MyIndex.foo)
        elif name.endswith('_'):
            name = name[:-1]
        return SolrFunction(name)

# func.div(func.log(MyIndex.field), func.log(2)) becomes 'div(log(field), log(2))'
func = _SolrFunctionGenerator()

class SolrResult(object):
    """ Currently just a wrapper for pysolr result """
    def __init__(self, res, handler):
        self.docs = res.docs
        self.hits = res.hits
        self.highlighting = res.highlighting
        self.facets = res.facets
        self.spellcheck = res.spellcheck
        self.stats = res.stats

        self.handle_row = handler

    def __iter__(self):
        return (self.handle_row(doc) for doc in self.docs)

class LuceneQuery(object):
    MANDATORY = 'mandatory'
    PROHIBITED = 'prohibited'
    OPTIONAL = 'optional'

    required_modifiers = {MANDATORY: '+',
                          PROHIBITED: '-',
                          OPTIONAL: ''}

    def __init__(self, *args, **kw):
        first_arg = args[0]
        if hasattr(first_arg, 'solr_field_name'):
            self.field, args = first_arg, args[1:]
        elif isinstance(first_arg, LuceneQuery):
            # Only pass LuceneQuery if all the other args are LuceneQueries
            self.field = None
            self.components = itertools.chain([query.components for query in args])
        else:
            self.field = None

        self.components = list(args)
        self.local_params = MultiDict()
        self.required = LuceneQuery.OPTIONAL
        self.boost_factor = None

    def __pow__(self, power):
        self.boost_factor = power
        return self

    def tag(self, tag):
        self.local_params.add('tag', tag)
        return self

    def require(self):
        self.required = LuceneQuery.MANDATORY
        return self

    def negate(self):
        self.required = LuceneQuery.PROHIBITED
        return self

    def fuzzy(self, factor=NotGiven):
        self.components.append('~')
        if factor != NotGiven:
            self.components.append(factor)
        return self

    def __unicode__(self):
        modifier = self.required_modifiers[self.required]
        field_clause = '' if not self.field else unicode(self.field) + ':'
        local_params = ''
        if self.local_params:
            local_params = '{!' + ' '.join(['%s=%s' % (key, unicode(val)) for key, val in self.local_params.iteritems() ]) + '}'
        component_clause = ''.join([unicode(component) for component in self.components])
        boost_factor = '^%s' % self.boost_factor if self.boost_factor else ''
        return u''.join([local_params, modifier, field_clause, component_clause, boost_factor])

Q = LuceneQuery

def asc(*fields):
    return ','.join([unicode(field) + '+asc' for field in fields])

def desc(*fields):
    return ','.join([unicode(field) + '+desc' for field in fields])

class SolrQuery(object):
    separators = {}

    def __init__(self, connections=None, index=None):
        self.params = MultiDict()
        self.connections = connections
        self.conn = self.connections.get('main', None)
        self.index = index
        self.params_joined = False

    def use_index(self, index):
        self.index = index

    def handle_row(self, row):
        return self.index(row)

    def join_params(self):
        return MultiDict((k,self.separators[k].join([unicode(v) for v in val]) if k in self.separators else unicode(val)) for k,val in self.params.iteritems())

    def execute(self, handler=handle_row, conn='main'):
        if not self.params_joined:
            self.params=self.join_params()
            self.params_joined = True
        return SolrResult(self._execute_search(), handler=partial(handler, self))


    def query(self, query):
        self.params.add('q', query)
        return self

    def filter(self, *filters):
        [self.params.add('fq', filter) for filter in filters]
        return self

    def facet(self, field, method=NotGiven, missing_facet=NotGiven, prefix=NotGiven):
        self.params['facet'] = True
        field_name = SolrQuery._name_or_val(field)
        self.params.add('facet.field', field_name)
        if method != NotGiven:
            self.params['f.%s.facet.method' % field_name] = method
        if missing_facet != NotGiven:
            self.params['f.%s.facet.missing' % field_name] = missing_facet
        if prefix != NotGiven:
            self.params['facet.prefix'] = prefix
        return self

    def facet_date(self, date_field, start_date=NotGiven, end_date=NotGiven,
                   gap=NotGiven, hard_end=NotGiven, other=NotGiven):
        field_name = SolrQuery._name_or_val(date_field)
        self.params.add('facet.date', field_name)

        if start_date != NotGiven:
            self.params['f.%s.facet.date.start' % field_name] = start_date

        if end_date != NotGiven:
            self.params['f.%s.facet.date.end' % field_name] = end_date

        if gap != NotGiven:
            self.params['f.%s.facet.date.gap' % field_name] = gap

        if hard_end != NotGiven:
            self.params['f.%s.facet.date.hardend' % field_name] = hard_end

        if other != NotGiven:
            self.params['f.%s.facet.date.other' % field_name] = other

        return self

    def facet_query(self, query):
        self.params.add('facet.query', query)
        return self

    def facet_prefix(self, field, prefix):
        self.facet(field)
        self.params['facet.prefix'] = prefix
        return self

    def default_operator(self, op):
        self.params['q.op'] = op
        return self

    def default_field(self, field):
        self.params['df'] = field
        return self

    def def_type(self, type):
        self.params['defType'] = type
        return self

    def tie(self, tie):
        self.params['tie'] = tie
        return self

    def default_search(self, query):
        self.params['q.alt'] = query
        return self

    @join_with_separator(separators, 'mm', ' ')
    def min_should_match(self, *args):
        self._add_items_to_key('mm', *args)
        return self

    def query_type(self, query_type):
        self.params['qt'] = query_type
        return self

    def paginate(self, limit, offset):
        self.params['start'] = limit
        self.params['rows'] = offset
        return self

    def limit(self, limit):
        self.params['rows'] = limit
        return self

    def offset(self, offset):
        self.params['start'] = offset
        return self

    @join_with_separator(separators, 'bf', ' ')
    def boost(self, *fields):
        self._add_items_to_key('bf', *fields)
        return self

    @join_with_separator(separators, 'pf', ' ')
    def phrase_boost(self, *fields):
        self._add_items_to_key('pf', *fields)
        return self

    def query_slop(self, slop):
        self.params['qs'] = slop
        return self

    def phrase_slop(self, slop):
        self.params['ps'] = slop
        return self

    def boost_query(self, query):
        self.params.add('bq', query)

    @staticmethod
    def _name_or_val(arg):
        return arg.solr_field_name if hasattr(arg, 'solr_field_name') else arg

    # Emulating defaultdict but on MultiDict
    def _add_items_to_key(self, param, *args):
        list_args = self.params.get(param, [])
        list_args.extend([SolrQuery._name_or_val(arg) for arg in args])
        self.params[param] = list_args

    @join_with_separator(separators, 'qf', ' ')
    def queried_fields(self, *fields):
        self._add_items_to_key('qf', *fields)
        return self

    def dismax_of(self, *fields):
        # Wrapper for queries using the dismax query parser
        self.def_type('dismax')
        self.queried_fields(*fields)
        self.tie(0.1)
        return self

    @join_with_separator(separators, 'fl', ',')
    def fields(self, *args):
        self._add_items_to_key('fl', *args)
        return self

    @join_with_separator(separators, 'sort', ',')
    def sort_by(self, *args):
        self._add_items_to_key('sort', *args)
        return self

    def indent(self, indent):
        self.params['indent']=indent
        return self

    def debug(self, debug):
        self.params['debugQuery'] = debug
        return self

    def echo_handler(self, echo):
        self.params['echoHandler'] = echo
        return self

    def echo_params(self, echo):
        self.params['echoParams'] = echo
        return self

    def _execute_search(self):
        return self.conn.search(self)