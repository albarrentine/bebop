'''
Created on Mar 7, 2011

@author: al
'''

from bebop import Solr
from unittest import TestCase
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), os.pardir))

class TestModel(TestCase):

    def test_autodiscover(self):

        import test_bebop
        solr = Solr()
        solr.autodiscover_indexes(test_bebop)
        solr.generate_solr_configs()
        self.assertTrue(True)
