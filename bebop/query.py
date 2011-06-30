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
        #self.conn = self.connections[conn]
        if not self.params_joined:
            self.params=MultiDict((k,self.separators[k].join(v) if k in self.separators else v) for k,v in self.params.iteritems())
            self.params_joined = True
        return [handler(self, obj) for obj in self._execute_search()]

    def query(self, query):
        self.params.update(q=query)
        return self

    def filter(self, filters):
        if hasattr(filters, '__iter__'):
            [self.params.update(fq=filter) for filter in filters]
        else:
            self.params.update(fq=filters)
        return self

    def default_field(self, field):
        self.params['df'] = field
        return self

    def def_type(self, type):
        self.params['defType'] = type
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

    def boost(self, field):
        self.params['bf'] = SolrQuery._name_or_val(field)
        return self

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
        self.def_type('dismax')
        self.queried_fields(*fields)
        return self

    @join_with_separator(separators, 'fl', ',')
    def fields(self, *args):
        self._add_items_to_key('fl', *args)
        return self

    @join_with_separator(separators, 'sort', ',')
    def sort_by(self, *args):
        self._add_items_to_key('sort', *args)
        return self



    #def response_format(self, format):
    #    self.params['wt'] = format

    def target_model(self, model, proxy):
        pass

    def _execute_search(self):
        return self.conn.search(self)