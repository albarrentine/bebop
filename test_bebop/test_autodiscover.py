'''
Created on Mar 7, 2011

@author: al
'''

from bebop import Solr
from unittest import TestCase

class TestModel(TestCase):

    def test_autodiscover(self):
        import test
        solr = Solr()
        solr.autodiscover_indexes(test)
        solr.generate_solr_configs()
        self.assertTrue(True)
