'''
Created on Jun 16, 2011

@author: al
'''

from schema import SolrSchemaField, UniqueKey
from util import NotGiven, MultiDict

class SolrQuery(object):
    def __init__(self, connections=None, index=None):
        self.params = MultiDict()
        self.connections = connections
        self.conn = self.connections.get('main', None)
        self.index = index

    def use_index(self, index):
        self.index = index

    def noop(self, response):
        return response

    def execute(self, handler=noop, conn='main'):
        #self.conn = self.connections[conn]
        return [handler(obj) for obj in self.conn.search(**self.params)]

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

    def paginate(self, start, rows):
        self.params['start'] = start
        self.params['rows'] = rows
        return self

    def limit(self, limit):
        self.params['rows'] = limit
        return self

    def offset(self, offset):
        self.params['offset'] = offset
        return self

    def queried_fields(self, *fields):
        [self.params.update(qf=field) for field in fields]
        return self

    def fields(self, *args):
        [self.params.update(fl=arg) for arg in args]
        return self

    def sort_by(self, *args):
        [self.params.update(sort=arg) for arg in args]
        return self

    #def response_format(self, format):
    #    self.params['wt'] = format

    def target_model(self, model, proxy):
        pass

    def _do_search(self):
        return self.connection.search(**self.params)

    def all(self):
        resp = self._do_search()

    def first(self):
        self.params['rows'] = 1
        resp = self._do_search()

    def scalar(self):
        self.params['rows'] = 1
        resp = self._do_search()

    def scalar_all(self):
        resp = self._do_search()
