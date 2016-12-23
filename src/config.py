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
import json, sys, os

class ConfigException(Exception):
  pass

class Config(object):
    path = os.path.split(os.path.realpath(__file__))[0]
    f = open(path + '/config.json')
    ff = f.read()
    config = json.loads(ff)
    f.close()
    
    try:
        CURRENCY_TYPE = config["constant"]["currency_type"]
        TRAN_PERFIX = config["constant"]["tran_perfix"]
        TRUST_LIMIT = config["constant"]["trust_limit"]
        SIGN_PREFIX = config["constant"]["sign_perfix"]

        issue_custom_tum = config["constant"]["issue_custom_tum"]
        query_issue = config["constant"]["query_issue"]
        query_custom_tum = config["constant"]["query_custom_tum"]

        sdk_api_address = config["prod"]["api_address"]
        sdk_web_socket_address = config["prod"]["web_socket_address"]
        sdk_api_version = config["prod"]["api_version"]
        ttong_address = config["prod"]["ttong_address"]

        test_api_address = config["dev"]["api_address"]
        test_web_socket_address = config["dev"]["web_socket_address"]
        test_api_version = config["dev"]["api_version"]
        test_ttong_address = config["dev"]["ttong_address"]
    except:
        raise ConfigException("config.json error")
    

