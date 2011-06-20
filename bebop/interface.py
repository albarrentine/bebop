from connection import SolrConn
from query import SolrQuery
from config import generate_multicore_schema, generate_config
from schema import generate_schema
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
            generate_schema(index.solr_schema)
            generate_config(index.solr_config)

    def add_connection(self, conn, id='main'):
        self.connections[id] = conn

    def search(self, index=None):
        if hasattr(index, '__solr_index__'):
            index = index.__solr_index__
        if index not in self.indexes:
            raise BebopConfigurationException("Tried to search index '%r' which is not in the configuration")
        return SolrQuery(connections=self.connections,
                         index=self.indexes[index])