'''
Created on Jun 16, 2011

@author: al
'''

from schema import SolrSchemaField, UniqueKey
from util import NotGiven, MultiDict

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
    pass

class LuceneQuery(object):
    MANDATORY = 'mandatory'
    PROHIBITED = 'prohibited'
    OPTIONAL = 'optional'

    def __init__(self, field=NotGiven, *args, **kw):
        if field is NotGiven:
            word, args = args[0], args[1:]
        else:
            self.field = field
        self.components = args
        self.required = LuceneQuery.OPTIONAL

    def __pow__(self, power):
        self.components.extend(['^', power])
        return self

    def require(self):
        self.required = LuceneQuery.MANDATORY

    def negate(self):
        self.required = LuceneQuery.PROHIBITED

    def fuzzy(self, factor=NotGiven):
        self.components.append('~')
        if factor != NotGiven:
            self.components.append(factor)

    def __unicode__(self):
        return u''.join([unicode(self.field), u':'] + [unicode(component) for component in self.components])


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

    def execute(self, handler=handle_row, conn='main'):
        if not self.params_joined:
            self.params=MultiDict((k,self.separators[k].join([unicode(v) for v in val]) if k in self.separators else unicode(val)) for k,val in self.params.iteritems())
            self.params_joined = True
        return [handler(self, obj) for obj in self._execute_search()]

    def query(self, query):
        self.params.update(q=unicode(query))
        return self

    def filter(self, filters):
        if hasattr(filters, '__iter__'):
            [self.params.update(fq=unicode(filter)) for filter in filters]
        else:
            self.params.update(fq=unicode(filters))
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

    def query_type(self, qt):
        self.params['qt'] = qt
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

    def boost_query(self, q):
        self.params.update(bq=unicode(q))

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


    #def response_format(self, format):
    #    self.params['wt'] = format

    #def target_model(self, model, proxy):
    #    pass

    def _execute_search(self):
        return self.conn.search(self)