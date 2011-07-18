from unittest import TestCase
from bebop import *
import os

class TestGenerateConfig(TestCase):
    
    def test_generate_config(self):

        config = DismaxSolrConfig

        generated_path = os.path.join(os.path.dirname(__file__), 'unit_test_config.xml')
        generate_config(config, path=generated_path)
    
        expected_path = os.path.join(os.path.dirname(__file__), 'test_config.xml')
        expected = open(expected_path).read()
        generated = open(generated_path).read()

        self.assertEqual(expected, generated)
