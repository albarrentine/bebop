'''
Created on Feb 18, 2011

@author: al
'''

#@todo: rewrite pysolr
import pysolr
try:
    import gevent
    gevent.monkey.patch_all()
except ImportError:
    try:
        import eventlet
        eventlet.monkey_patch()
    except ImportError:
        pass

class SolrConn(object):
    def __init__(self, conn, id='main'):
        self._solr = pysolr.Solr(conn)

    def search(self, query, id='main'):
        return self._solr.search(**query.params)

    def add(self, doc, commit=True):
        self._solr.add(doc._to_dict(),commit=commit)

    def add_all(self, docs, commit=False):
        self._solr.add([doc._to_dict() for doc in docs], commit=commit)

    def commit(self):
        self._solr.commit()

    def optimize(self):
        self._solr.optimize()

    def rollback(self):
        self._solr.rollback()