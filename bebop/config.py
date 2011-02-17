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
                 use_compound_file=None,
                 merge_factor=None,
                 max_buffered_docs=None,
                 max_merge_docs=None,
                 max_field_length=None):
        SingleValueTagsMixin.__init__(kw.pop('self'),**locals())

class AutoCommit(SingleValueTagsMixin):
    def __init__(self,
                 max_docs = None,
                 max_time = None
                 ):
        SingleValueTagsMixin.__init__(locals().pop('self'),**locals())

class MergePolicy(BaseSolrXMLElement):
    tag='mergePolicy'
    required = {'class': 'solr_class'}
    
    solr_class = None
    
class LogByteSizeMergePolicy(MergePolicy):
    solr_class = "org.apache.lucene.index.LogByteSizeMergePolicy"

class LogDocMergePolicy(MergePolicy):
    solr_class = "org.apache.lucene.index.LogDocMergePolicy"

class MergeScheduler(BaseSolrXMLElement):
    tag = "mergeScheduler"
    required = {'class': 'solr_class'}
    
    solr_class = None
    
class ConcurrentMergeScheduler(MergeScheduler):
    solr_class = "org.apache.lucene.index.ConcurrentMergeScheduler"
    
class SerialMergeScheduler(MergeScheduler):
    solr_class = "org.apache.lucene.index.SerialMergeScheduler"

class IndexDefaults(SingleValueTagsMixin):
    def __init__(self,
                 use_compound_file=None,
                 merge_factor=None,
                 max_buffered_docs=None,
                 ram_buffer_size=None,
                 max_field_length=None,
                 write_lock_timeout=None,
                 commit_lock_timout=None,
                 lock_type=None,
                 term_index_interval=None
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
    
class SolrConfig(SingleValueTagsMixin):
    tag = 'config'
    def __init__(self, **kw):
        SingleValueTagsMixin.__init__(self, **kw)
        
StandardSolrConfig = SolrConfig(lucene_match_version='LUCENE_40',
                                update_handler = DirectUpdateHandler,
                                standard = StandardRequestHandler)

DismaxSolrConfig = SolrConfig(lucene_match_version='LUCENE_40',
                              update_handler = DirectUpdateHandler,
                              dismax = DismaxRequestHandler
                              )
    
def generate_config(config, path = 'solr/conf/solr-config.xml'):
    ensure_dir(os.path.dirname(path))
    
    tree = etree.ElementTree(config.to_xml())
    tree.write(path, encoding='utf-8', xml_declaration=True, pretty_print=True)