from connection import SolrConn
from query import SolrQuery
from data_import import DBAPIBatchIndexer
from config import generate_multicore_schema, generate_config
from util import NotGiven
import inspect
import os
import pkgutil
import sys

class BebopConfigurationException(Exception):
    pass

class Solr(object):
    def __init__(self, connections = NotGiven):
        self.connections = {} if connections is NotGiven else connections
        self.indexes = {}

    def add_connection(self, url, id='main'):
        self.connections[id] = SolrConn(url)

    def autodiscover_indexes(self, *packages):
        for package in packages:
            pkg_path = os.path.dirname(package.__file__)
            module_names = [name for _, name, _ in pkgutil.iter_modules([pkg_path])]
            for module_name in module_names:
                qualified_name = package.__name__ + '.' + module_name
                __import__(qualified_name)
                module=sys.modules[qualified_name]
                for attr, obj in inspect.getmembers(module):
                    if hasattr(obj, '__solr_index__'):
                        self.indexes[obj.__solr_index__] = obj

    def generate_solr_configs(self, core_admin_conf=None):
        if len(self.indexes) > 1:
            generate_multicore_schema(core_admin_conf, **self.indexes)
        else:
            index = self.indexes.values()[0]
            index.solr_schema.generate()
            generate_config(index.solr_config)

    def _validate_index(self, obj):
        index = getattr(obj, '__solr_index__', None) or obj
        if index not in self.indexes:
            raise BebopConfigurationException("Tried to search index '%r' which is not in the configuration")
        return index

    def search(self, index=None):
        index = self._validate_index(index)
        return SolrQuery(connections=self.connections,
                         index=self.indexes[index])

    def batch_index(self, index, conn_id='main', indexer=DBAPIBatchIndexer):
        index = self._validate_index(index)
        return indexer(self.connections[conn_id],
                        index=self.indexes[index])
