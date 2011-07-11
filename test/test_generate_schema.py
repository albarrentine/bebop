from unittest import TestCase
from solr_bebop import *

class TestGenerateSchema(TestCase):
    def test_schema(self):
        filename = './test/unit_test_schema.xml'
        schema = SolrSchema('test_schema',
                            field_types=SolrFieldTypes(Integer, Text),
                            fields = SolrSchemaFields(
                                model.TextField('foo'),
                                model.IntegerField('bar', document_id = True)
                                )
                            )

        schema.generate(path=filename)

        generated_file = open(filename).read()
        test_file = open('./test/test_schema.xml').read()

        self.assertEqual(generated_file, test_file)
