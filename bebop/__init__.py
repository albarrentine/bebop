from schema import *
from model import *
from config import *
from data_import import *
from interface import *

class _SolrFunctions(object):
    def __getattr__(self, attr):
        pass

func = _SolrFunctions()