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

class UpdateHandler(BaseSolrXMLElement):
    pass

class DirectUpdateHandler(UpdateHandler):
    solr_class = 'solr.DirectUpdateHandler2'

class RequestHandler(BaseConfigElement):
    required = {'solr_class': 'class',
                'field_name': 'name'}

class StandardRequestHandler(RequestHandler):
    field_name = 'standard'

class DismaxRequestHandler(BaseSolrXMLElement):
    field_name = 'dismax'

class SolrConfig(BaseSolrXMLElement):
    tag = "config"
    
    request_handler = StandardRequestHandler
