'''
Created on Jan 19, 2011

@author: al
'''

from util import *

"""
  <updateHandler class="solr.DirectUpdateHandler2" />

  <requestDispatcher handleSelect="true" >
    <requestParsers enableRemoteStreaming="false" multipartUploadLimitInKB="2048" />
  </requestDispatcher>

  <requestHandler name="standard" class="solr.StandardRequestHandler" default="true" />
  <requestHandler name="/update" class="solr.XmlUpdateRequestHandler" />
  <requestHandler name="/admin/" class="org.apache.solr.handler.admin.AdminHandlers" />

  <!-- config for the admin interface -->
  <admin>
    <defaultQuery>solr</defaultQuery>
  </admin>
"""

class BaseConfigElement(BaseSolrXMLElement):
    required = {'solr_class': 'class'}

class MainIndex(SingleValueTagsMixin):
    tag = 'mainIndex'
    def __init__(self,
                 use_compound_file=NotGiven,
                 ram_buffer_size_mb=NotGiven,
                 merge_factor=NotGiven,
                 unlock_on_startup=NotGiven,
                 reopen_readers=NotGiven,
                 max_buffered_docs=NotGiven,
                 max_merge_docs=NotGiven,
                 max_field_length=NotGiven):
        SingleValueTagsMixin.__init__(locals().pop('self'),**locals())

class AutoCommit(SingleValueTagsMixin):
    def __init__(self,
                 max_docs = NotGiven,
                 max_time = NotGiven
                 ):
        SingleValueTagsMixin.__init__(locals().pop('self'),**locals())

class MergePolicy(BaseConfigElement):
    tag='mergePolicy'

    solr_class = None

class LogByteSizeMergePolicy(MergePolicy):
    solr_class = "org.apache.lucene.index.LogByteSizeMergePolicy"

class LogDocMergePolicy(MergePolicy):
    solr_class = "org.apache.lucene.index.LogDocMergePolicy"

class MergeScheduler(BaseConfigElement):
    tag = "mergeScheduler"
    solr_class = None

class ConcurrentMergeScheduler(MergeScheduler):
    solr_class = "org.apache.lucene.index.ConcurrentMergeScheduler"

class SerialMergeScheduler(MergeScheduler):
    solr_class = "org.apache.lucene.index.SerialMergeScheduler"


class GenericTag(BaseSolrXMLElement):
    tag = None
    options = ['name']
    def __init__(self, val):
        self.value = val
        super(GenericTag, self).__init__()

class StrTag(GenericTag):
    tag = 'str'

class IntTag(GenericTag):
    tag = 'int'

class LongTag(GenericTag):
    tag = 'long'

class FloatTag(GenericTag):
    tag = 'float'

class DoubleTag(GenericTag):
    tag = 'double'

class BoolTag(GenericTag):
    tag = 'bool'

class DocTag(NamedSingleValueTagsMixin):
    tag = 'doc'

class ListTag(NamedSingleValueTagsMixin):
    tag = 'lst'
    options = ['name']

class ArrayTag(SingleValueTagsMixin, GenericTag):
    tag = 'arr'
    options = ['name']

class IndexDefaults(SingleValueTagsMixin):
    def __init__(self,
                 use_compound_file=NotGiven,
                 merge_factor=NotGiven,
                 max_buffered_docs=NotGiven,
                 ram_buffer_size=NotGiven,
                 max_field_length=NotGiven,
                 write_lock_timeout=NotGiven,
                 commit_lock_timout=NotGiven,
                 lock_type=NotGiven,
                 term_index_interval=NotGiven
              ):
        SingleValueTagsMixin.__init__(locals().pop('self'),**locals())

class RequestHandler(BaseSolrXMLElement):
    tag = "requestHandler"
    required={'solr_class': 'class', 'name': 'name'}

class DirectUpdateHandler(RequestHandler):
    name = '/update'
    solr_class = 'solr.DirectUpdateHandler2'

    auto_commit = None

class SearchHandler(RequestHandler):
    solr_class = "solr.SearchHandler"
    default = False

class StandardRequestHandler(RequestHandler):
    name = 'standard'
    solr_class = "solr.SearchHandler"

class DismaxRequestHandler(RequestHandler):
    name = 'dismax'
    solr_class = 'solr.SearchHandler'

class UpdateRequestProcessorChain(BaseSolrXMLElement):
    tag = 'updateRequestProcessorChain'

    def __init__(self, processors):
        self.processors = processors

class UpdateRequestProcessor(BaseSolrXMLElement):
    tag = 'processor'
    required = {'solr_class': 'class'}

class RunUpdateProcessor(UpdateRequestProcessor):
    solr_class = 'solr.RunUpdateProcessorFactory'

class LogUpdateProcessor(UpdateRequestProcessor):
    solr_class = 'solr.LogUpdateProcessorFactory'

class SolrConfig(SingleValueTagsMixin):
    tag = 'config'
    def __init__(self, **kw):
        super(SolrConfig, self).__init__(self, **kw)

StandardSolrConfig = SolrConfig(lucene_match_version='LUCENE_40',
                                update_handler = DirectUpdateHandler,
                                standard = StandardRequestHandler)

DismaxSolrConfig = SolrConfig(lucene_match_version='LUCENE_40',
                              update_handler = DirectUpdateHandler,
                              dismax = DismaxRequestHandler
                              )

def generate_config(config, path = 'solr/conf/solrconfig.xml'):
    ensure_dir(os.path.dirname(path))

    tree = etree.ElementTree(config.to_xml())
    tree.write(path, encoding='utf-8', xml_declaration=True, pretty_print=True)


class SolrCore(BaseSolrXMLElement):
    tag='core'
    name = None
    instance_dir = None

    required = dict((attr, attr) for attr in ['name', 'instance_dir'])

    def __init__(self, name, instance_dir):
        self.name = name
        self.instance_dir = instance_dir

class SolrCores(BaseSolrXMLElement):
    tag='cores'

    options = ['admin_path']
    admin_path='/admin/cores'

    def __init__(self, admin_path=None, cores=None):
        if admin_path:
            self.admin_path = admin_path
        self.cores = cores

class SolrMulticoreXML(BaseSolrXMLElement):
    tag = 'solr'
    persistent=False

    def __init__(self, solr_cores=SolrCores(admin_path='/admin/cores',
                                            cores=[SolrCore('core0', 'core0')]), persistent=None):
        super(SolrMulticoreXML, self).__init__(solr_cores=solr_cores,
                                               persistent=persistent if persistent is not None else self.persistent)

def get_multicore_conf(**indexes):
    core_xml = SolrMulticoreXML(solr_cores=SolrCores(admin_path='/admin/cores',
                                                     cores=[SolrCore(name=index, instance_dir=index)
                                                            for index in indexes.keys()]
                                                     )
                                )
    return core_xml


def generate_multicore_schema(conf=None, path_root='solr/', **indexes):
    core_xml = conf or get_multicore_conf(**indexes)

    ensure_dir(os.path.dirname(path_root))


    tree = etree.ElementTree(core_xml.to_xml())
    tree.write(os.path.join(path_root, 'solr.xml'), encoding='utf-8', xml_declaration=True, pretty_print=True)

    for index_name, index in indexes.iteritems():
        ensure_dir(os.path.join(path_root, index_name, 'conf'))
        xml_schema = etree.ElementTree(index.solr_schema.to_xml())
        xml_schema.write(os.path.join(path_root, index.__solr_index__, 'conf', 'schema.xml'), encoding='utf-8', xml_declaration=True, pretty_print=True)
        xml_conf = etree.ElementTree(index.solr_config.to_xml())
        xml_conf.write(os.path.join(path_root, index.__solr_index__, 'conf', 'solrconfig.xml'), encoding='utf-8', xml_declaration=True, pretty_print=True)