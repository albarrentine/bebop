'''
Created on Feb 18, 2011

@author: al
'''

#@todo: rewrite pysolr
import pysolr

class SolrConn(object):
    def __init__(self, conn, id='main'):
        self._solr = pysolr.Solr(conn)

    def search(self, query, id='main'):
        response = self._solr._select(query.params)
        result = self._solr.decoder.decode(response)
        result_kwargs = {}

        if result.get('highlighting'):
            result_kwargs['highlighting'] = result['highlighting']

        if result.get('facet_counts'):
            result_kwargs['facets'] = result['facet_counts']

        if result.get('spellcheck'):
            result_kwargs['spellcheck'] = result['spellcheck']

        if result.get('stats'):
            result_kwargs['stats'] = result['stats']

        self._solr.log.debug("Found '%s' search results." % result['response']['numFound'])
        return pysolr.Results(result['response']['docs'], result['response']['numFound'], **result_kwargs)

    def add(self, doc, commit=True):
        self._solr.add(doc._to_dict(),commit=commit)

    def add_all(self, docs, commit=False):
        self._solr.add([doc._to_dict() for doc in docs], commit=commit)

    def commit(self):
        self._solr.commit()

    def delete(self, query='*:*', commit=True):
        self._solr.delete(q=query, commit=commit)

    def optimize(self):
        self._solr.optimize()

    def rollback(self):
        self._solr.rollback()
