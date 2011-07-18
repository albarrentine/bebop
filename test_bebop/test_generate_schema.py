from unittest import TestCase
from bebop import *
import os

class TestGenerateSchema(TestCase):
    def test_schema(self):
        generated_path = os.path.join(os.path.dirname(__file__), 'unit_test_schema.xml')
        schema = SolrSchema('test_schema',
                            field_types=SolrFieldTypes(Integer, Text),
                            fields = SolrSchemaFields(
                                model.TextField('foo'),
                                model.IntegerField('bar', document_id = True)
                                )
                            )

        schema.generate(path=generated_path)

        generated = open(generated_path).read()
        expected_path = os.path.join(os.path.dirname(__file__), 'test_schema.xml')
        expected = open(expected_path).read()

        self.assertEqual(generated, expected)
