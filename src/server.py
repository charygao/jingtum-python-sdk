# -*- coding:utf-8 -*-

"""
 * Copyright@2016 Jingtum Inc. or its affiliates.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
"""

from websocket import create_connection
import threading
import json
import unirest

import urllib2
#import urllib.parse
import urlparse
#from urllib.error import HTTPError
from urllib2 import HTTPError
import json
import uuid
import urllib
import socket
from logger import logger

from config import Config

g_test_evn = False

class JingtumRESTException(Exception):
  pass

class TumApiException(Exception):
  pass

class Server(Config):
    def __init__(self):
        super(Server, self).__init__()  
        global g_test_evn
        self.setTest(g_test_evn)
        
    def setTest(self, isTest = False):
        global g_test_evn
        g_test_evn = isTest
        self.isTest = isTest

        if isTest:
            self.api_version = Config.test_api_version
            self.url = Config.test_api_address
            self.ws_address = Config.test_web_socket_address

            self.tt_address = Config.test_ttong_address
        else:
            self.api_version = Config.sdk_api_version
            self.url = Config.sdk_api_address
            self.ws_address = Config.sdk_web_socket_address

            self.tt_address = Config.ttong_address

    def setMode(self, is_Test):
        self.setTest(is_Test)    

class APIServer(Server):
    def __init__(self):
        super(APIServer, self).__init__()  
        pass

    def getasyn(self, path, parameters=None, method="GET", callback=None, cb_para=None):
        def get_cb(response):
            callback(response.body, cb_para)

        path = '/{version}/{path}'.format(version=self.api_version, path=path)
        url = "%s%s"%(self.url, path)
        if parameters:
          parameters = {k:v for k,v in parameters.items() if v is not None}
          for k, v in parameters.items():
            if type(v) is bool:
              parameters[k] = 'true' if v else 'false'
          parameters = urllib.urlencode(parameters)
          parameters = urllib.unquote(parameters)
        print ("in _request:" + str(url))
        print ("in _request:" + str(parameters))
        unirest.get(url, headers={"Content-Type": "application/json;charset=utf-8"}, 
                params=parameters, callback=get_cb)

    def get(self, path, parameters=None, method="GET"):
        path = '/{version}/{path}'.format(version=self.api_version, path=path)
        if parameters:
          parameters = {k:v for k,v in parameters.items() if v is not None}
          for k, v in parameters.items():
            if type(v) is bool:
              parameters[k] = 'true' if v else 'false'
          parameters = urllib.urlencode(parameters)
          parameters = urllib.unquote(parameters)
        pieces = (self.url, path, parameters, None)
        url = "%s%s?%s"%(self.url, path, parameters)
        #logger.debug("in _request:" + str(url))
        print ("in _request:" + str(url))

        req = urllib2.Request(url)
        if method is not None:
          req.get_method = lambda:method
        try:
          response = urllib2.urlopen(req, timeout=10)
          realsock = response.fp._sock.fp._sock
          res = json.loads(response.read().decode('utf-8'))
          realsock.close() 
          response.close()
        except HTTPError as e:
          error_object = e.read()
          if e.code == 400:
            return json.loads(error_object.decode('utf-8'))
          else:
            raise JingtumRESTException(error_object)
        if res['success']:
          #del response['success']
          return res
        else:
          raise JingtumRESTException(res['message'])

    def postasyn(self, path, data=None, method="POST", callback=None):
        def post_cb(response):
            callback(response.body)

        path = '/{version}/{path}'.format(version=self.api_version, path=path)
        url = "%s%s"%(self.url, path)
        data = json.dumps(data).encode('utf-8')
        print ("in _request:" + str(url))
        print ("in _request:" + str(data))
        if method == "DELETE":
            unirest.delete(url, headers={"Content-Type": "application/json;charset=utf-8"}, 
                params=data, callback=post_cb)
        else:
            unirest.post(url, headers={"Content-Type": "application/json;charset=utf-8"}, 
                params=data, callback=post_cb)


    def post(self, path, data=None, method="POST", callback=None):
        """Make an HTTP request to the server
      
        Encode the query parameters and the form data and make the GET or POST
        request
      
        :param path: The path of the HTTP resource
        :param parameters: The query parameters
        :param data: The data to be sent in JSON format
        :param secret: The secret key, which will be added to the data
        :param complete_path: Do not prepend the common path
      
        :returns: The response, stripped of the 'success' field
        
        :raises JingtumRESTException: An error returned by the rest server
        """
        path = '/{version}/{path}'.format(version=self.api_version, path=path)
        
        url = "%s%s"%(self.url, path)
        #logger.debug("in _request:" + str(url))
        print ("in _request:" + str(url))
        #req = urllib.request.Request(url)
        req = urllib2.Request(url)
        if method is not None:
          req.get_method = lambda:method
        if data is not None:
          req.add_header("Content-Type","application/json;charset=utf-8")
          data = json.dumps(data).encode('utf-8')
        try:
          #logger.debug("in _request:" + str(data))
          print ("in _request:" + str(data))
          response = urllib2.urlopen(req, data, timeout=10)
          realsock = response.fp._sock.fp._sock
          res = json.loads(response.read().decode('utf-8'))
          realsock.close() 
          response.close()
        except HTTPError as e:
          #error_object = json.loads(e.read().decode('utf-8'))['message']
          error_object = e.read()
          raise JingtumRESTException(error_object)
        #####print "in _request", path, response
        if res['success']:
          #del response['success']
          if callback is None:
            return res
          else:
            callback(res)
        else:
          raise JingtumRESTException(res['message'])

    def delete(self, path, data=None, method="DELETE"):
        return self.post(path, data, method)

class TumServer(Server):
    def __init__(self):
        super(TumServer, self).__init__()  
        pass

    def send(self, path, data=None, method="POST"):
        # if parameters:
        #   parameters = {k:v for k,v in parameters.items() if v is not None}
        #   for k, v in parameters.items():
        #     if type(v) is bool:
        #       parameters[k] = 'true' if v else 'false'
        #   parameters = urllib.urlencode(parameters)
        #   parameters = urllib.unquote(parameters)
        # pieces = (self.url, path, parameters, None)
        # url = urlparse.urlunsplit(pieces)
        url = path
        #logger.debug("in _request:" + str(url))
        print "in _request:" + str(url)
        req = urllib2.Request(url)
        if method is not None:
          req.get_method = lambda:method
        if data is not None:
          req.add_data(urllib.urlencode(data))
          req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
          #logger.debug("in _request:" + str(data))
          print "in _request:" + str(data)
          response = urllib2.urlopen(req, timeout=10)
          realsock = response.fp._sock.fp._sock
          res = json.loads(response.read().decode('utf-8'))
          realsock.close() 
          response.close()
        except HTTPError as e:
          error_object = e.read()
          if e.code == 400:
            return json.loads(error_object.decode('utf-8'))
          else:
            #print "ddddddd", e.__dict__
            raise TumApiException(error_object)

        return res

class WebSocketServer(Server):
    def __init__(self):
        super(WebSocketServer, self).__init__()  
        self._shutdown = False
        self.ws = create_connection(self.ws_address)
        #print self.ws.recv()#, self.ws.__dict__
        
    # def __del__(self):
    #     print "WebSocketClient __del__", self.close()

    def send(self, data):
        ret = None
        data = json.dumps(data).encode('utf-8')
        try:
            self.ws.send(data)
            #ret = self.ws.recv()
            #ret = json.loads(ret.decode('utf-8'))
        except Exception, e:
            print "websocket send error", e
        return ret

    def subscribe(self, address, secret):
        _data = {
            "command": "subscribe",
            "account": address,
            "secret": secret 
        }
        ret = self.send(_data)
        return ret

    def unsubscribe(self, address):
        _data = {
            "command": "unsubscribe",
            "account": address,
        }
        ret = self.send(_data)
        return ret

    def close(self):
        _data = {
            "command": "close",
        }
        self._shutdown = True
        return self.send(_data) 

    def setTxHandler(self, callback, *arg):
        t = threading.Thread(target=self.receive, args=(callback, arg))
        t.setDaemon(True)
        t.start()

    def receive(self, callback, *arg):
        try: 
            while not self._shutdown: 
                msg = json.loads(self.ws.recv().decode('utf-8'))
                #print 'websocket<<<<<<<< receiving % s', json.dumps(msg, indent=2)
                callback(msg, arg)
        except Exception, e:
            print e
