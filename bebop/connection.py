'''
Created on Feb 18, 2011

@author: al
'''

import pysolr

_solr_conns = {}

class Solr(object):
    def __init__(self, host, port, solr_dir='solr', id='main'):   
        self._solr = _solr_conns[id] = _solr_conns.get(id) or pysolr.Solr('http://%s:%s/%s/' % (host, port, solr_dir))
      
    @property
    def raw_conn(self):
        return _solr_conns[self.id]
              
    def search(self, query, id='main'):
        return self._solr.search(query)
    
    def add(self):
        pass

    def update(self):
        pass