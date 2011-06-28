'''
Created on Mar 7, 2011

@author: al
'''

from util import NotGiven

import logging

log = logging.getLogger('bebop')

class BatchIndexer(object):
    COMMIT_PER_BATCH = 'batch'
    COMMIT_PER_INDEX = 'index'
    COMMIT_MANUALLY = 'manual'

    _query = None
    setup_func = None
    setup_func_args = None
    setup_func_kwargs = None
    _batch_size = 1000
    _solr_conn = None
    _commit_interval = COMMIT_PER_BATCH

    def __init__(self, solr_conn, solr_index):
        self.solr_conn = solr_conn
        self.solr_index = solr_index

    def setup(self, func, *args, **kw):
        self.setup_func = func
        self.setup_func_args = args
        self.setup_func_kwargs = kw
        return self

    def query(self, q):
        self._query = q
        return self

    def batch_size(self, size):
        self._batch_size = size
        return self

    # Template for _batch_getter function, can be set in batch_getter method
    def get_batch(self, limit=NotGiven, offset=NotGiven):
        raise NotImplementedError

    def batch_getter(self, f):
        """
        @param f: function object which takes two parameters, limit and offset
        """
        self._batch_getter = f
        return self

    def handle_row(self, row):
        return self.solr_index(row)

    def row_handler(self, f):
        """
        @param f: function object which takes one parameters "row", the row returned
        """
        self.handle_row = f
        return self

    def commit_interval(self, commit_interval):
        self._commit_interval = commit_interval
        return self

    def execute(self):
        raise NotImplementedError

    def index_batch(self, batch):
        self.solr_conn.add_all(batch)

    def index_all(self):
        docs = []
        self.offset = 0
        while True:
            batch = [self.handle_row(row) for row in self.get_batch(self._batch_size, self.offset)]
            if not batch:
                break
            self.offset += self._batch_size
            log.info("Indexing documents %d - %d" % (self.offset, self.offset+self._batch_size - 1))
            self.index_batch(batch)
            if self._commit_interval == BatchIndexer.COMMIT_PER_BATCH:
                self.solr_conn.commit()

        if self._commit_interval == BatchIndexer.COMMIT_PER_INDEX:
            self.solr_conn.commit()
        return self

class DBAPIBatchIndexer(BatchIndexer):
    def cursor(self, cur):
        self.db_cursor = cur
        return self

    def get_batch(self, limit, offset):
        return self.db_cursor.fetchmany(limit)

    def execute(self, query):
        self.db_cursor.execute(query)
        return self

if __name__ == '__main__':
    import MySQLdb
    from MySQLdb import cursors
    import pysolr
    from bebop.test.test_model import Foo

    solr_conn = pysolr.Solr('http://localhost:8983/solr')
    solr_conn.delete(q="*:*")

    db_conn = MySQLdb.connect(host='localhost', user='root', db='test',
                              cursorclass=cursors.SSDictCursor
                              )

    indexer = DBAPIBatchIndexer(solr_conn, Foo).cursor(db_conn.cursor()).batch_size(1000)
    print "Executing query..."
    indexer.execute("select * from solr_test")
    print "Running indexer..."
    indexer.index_all()