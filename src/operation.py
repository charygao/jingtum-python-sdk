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

from config import Config
from account import FinGate    
from logger import logger
from server import APIServer
from serialize import JingtumBaseDecoder

class JingtumOperException(Exception):
    pass

class Operation(FinGate):
    def __init__(self, src_address):
        super(Operation, self).__init__()
        self.src_address = src_address
        self.src_secret = ""
        self.is_sync = False

        self.api_helper = APIServer()
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            
        self.validateAddress(src_address)

    def validateAddress(self, address):
        if not JingtumBaseDecoder.verify_checksum(JingtumBaseDecoder.decode_base(address, 25)):
            raise JingtumOperException("Invalid address: %s" %  str(address))
        
    def submit(self):
        #print self.oper()
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
        return self.api_helper.post(*self.oper())

    def addSrcSecret(self, src_secret):
        self.src_secret = src_secret

    def addSync(self, is_sync):
        self.is_sync = is_sync

class PaymentOperation(Operation):
    def __init__(self, src_address):
        super(PaymentOperation, self).__init__(src_address)
        self.amt = {}
        self.dest_address = ""
        self.path = ""

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].amt) == 0:
                #logger.error("addAmount first:" + func.__name__)
                raise JingtumOperException("addAmount first before oper.")
            elif args[0].dest_address == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addDestAddress first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def addAmount(self, currency_type, currency_value, issuer=""):
        self.amt["value"] = str(currency_value)
        self.amt["currency"] = str(currency_type)
        self.amt["issuer"] = str(issuer)

    def addDestAddress(self, dest_address):
        self.dest_address = dest_address

    def addPath(self, path):
        self.path = path

    @para_required
    def oper(self):
        _payment = {}
        _payment["destination_amount"] = self.amt
        _payment["source_account"] = self.src_address
        _payment["destination_account"] = self.dest_address
        _payment["payment_path"] = self.path

        _para = {}
        _para["secret"] = self.src_secret
        _para["payment"] = _payment
        _para["client_resource_id"] = self.getNextUUID()

        if self.is_sync:
          url = 'accounts/{address}/payments?validated=true'
        else:
          url = 'accounts/{address}/payments'
        url = url.format(address=self.src_address)

        return url, _para

class OrderOperation(Operation):
    def __init__(self, src_address):
        super(OrderOperation, self).__init__(src_address)
        self.order_type = "buy"
        self.takerpays = {}
        self.takergets = {}

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].takerpays) == 0:
                #logger.error("setTakePays first:" + func.__name__)
                raise JingtumOperException("setTakePays first before oper.")
            elif len(args[0].takergets) == 0:
                #logger.error("setTakeGets first:" + func.__name__)
                raise JingtumOperException("setTakeGets first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setOrderType(self, is_sell):
        self.order_type = "sell" if is_sell else "buy"

    def setTakePays(self, currency_type, currency_value, counterparty=""):
        self.takerpays["value"] = str(currency_value)
        self.takerpays["currency"] = str(currency_type)
        self.takerpays["counterparty"] = str(counterparty)

    def setTakeGets(self, currency_type, currency_value, counterparty=""):
        self.takergets["value"] = str(currency_value)
        self.takergets["currency"] = str(currency_type)
        self.takergets["counterparty"] = str(counterparty)

    @para_required
    def oper(self):
        _order = {}
        _order["type"] = self.order_type
        _order["taker_pays"] = self.takerpays
        _order["taker_gets"] = self.takergets

        _para = {}
        _para["secret"] = self.src_secret
        _para["order"] = _order

        if self.is_sync:
          url = 'accounts/{address}/orders?validated=true'
        else:
          url = 'accounts/{address}/orders'
        url = url.format(address=self.src_address)

        return url, _para

class CancelOrderOperation(Operation):
    """docstring for CancelOrder"""
    def __init__(self, src_address):
        super(CancelOrderOperation, self).__init__(src_address)
        self.order_num = 0

    def para_required(func):
        def _func(*args, **args2): 
            if args[0].order_num == 0:
                #logger.error("setOrderNum first:" + func.__name__)
                raise JingtumOperException("setOrderNum first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setOrderNum(self, order_num):
        self.order_num = order_num

    @para_required
    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret

        if self.is_sync:
          url = 'accounts/{address}/orders/{order}?validated=true'
        else:
          url = 'accounts/{address}/orders/{order}'
        url = url.format(address=self.src_address, order=self.order_num)

        return url, _para, "DELETE"

class AddRelation(Operation):
    def __init__(self, src_address):
        super(AddRelation, self).__init__(src_address)
        self.amt = {}
        self.counterparty = ""
        self.relation_type = ""

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].amt) == 0:
                #logger.error("addAmount first:" + func.__name__)
                raise JingtumOperException("addAmount first before oper.")
            elif args[0].relation_type == "":
                #logger.error("setRelationType first:" + func.__name__)
                raise JingtumOperException("setRelationType first before oper.")
            elif args[0].counterparty == "":
                #logger.error("setCounterparty first:" + func.__name__)
                raise JingtumOperException("setCounterparty first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def addAmount(self, currency_type, currency_value, issuer=""):
        self.amt["limit"] = str(currency_value)
        self.amt["currency"] = str(currency_type)
        self.amt["issuer"] = str(issuer)

    def setCounterparty(self, counterparty):
        self.counterparty = counterparty

    def setRelationType(self, relation_type):
        self.relation_type = relation_type

    @para_required
    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret
        _para["type"] = self.relation_type
        _para["counterparty"] = self.counterparty
        _para["amount"] = self.amt

        if self.is_sync:
          url = 'accounts/{address}/relations?validated=true'
        else:
          url = 'accounts/{address}/relations'
        url = url.format(address=self.src_address)

        return url, _para

class RemoveRelation(Operation):
    def __init__(self, src_address):
        super(RemoveRelation, self).__init__(src_address)
        self.amt = {}
        self.counterparty = ""
        self.relation_type = ""

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].amt) == 0:
                #logger.error("addAmount first:" + func.__name__)
                raise JingtumOperException("addAmount first before oper.")
            elif args[0].relation_type == "":
                #logger.error("setRelationType first:" + func.__name__)
                raise JingtumOperException("setRelationType first before oper.")
            elif args[0].counterparty == "":
                #logger.error("setCounterparty first:" + func.__name__)
                raise JingtumOperException("setCounterparty first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def addAmount(self, currency_type, currency_value, issuer=""):
        self.amt["limit"] = str(currency_value)
        self.amt["currency"] = str(currency_type)
        self.amt["issuer"] = str(issuer)

    def setCounterparty(self, counterparty):
        self.counterparty = counterparty

    def setRelationType(self, relation_type):
        self.relation_type = relation_type

    @para_required
    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret
        _para["type"] = self.relation_type
        _para["counterparty"] = self.counterparty
        _para["amount"] = self.amt
        
        url = 'accounts/{address}/relations'
        url = url.format(address=self.src_address)

        return url, _para, "DELETE"

class WalletSettings(Operation):
    def __init__(self, src_address):
        super(WalletSettings, self).__init__(src_address)

    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret 

        url = 'accounts/{address}/settings'
        url = url.format(address=self.src_address)

        return url, _para

class AddTrustLine(Operation):
    def __init__(self, src_address):
        super(AddTrustLine, self).__init__(src_address)
        self.counterparty = ""
        self.currency = ""
        self.frozen = False

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].counterparty) == 0:
                #logger.error("setCounterparty first:" + func.__name__)
                raise JingtumOperException("setCounterparty first before oper.")
            elif args[0].currency == "":
                #logger.error("setCurrency first:" + func.__name__)
                raise JingtumOperException("setCurrency first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setCounterparty(self, counterparty):
        self.counterparty = counterparty

    def setLimit(self, limit):
        self.trust_limit = limit

    def setCurrency(self, currency):
        self.currency = currency

    def setTrustlineFrozen(self, frozen):
        self.frozen = frozen

    @para_required
    def oper(self):
        _trust = {}
        _trust["limit"] = self.trust_limit
        _trust["currency"] = self.currency
        _trust["counterparty"] = self.counterparty
        _trust["account_trustline_frozen"] = self.frozen

        _para = {}
        _para["secret"] = self.src_secret 
        _para["trustline"] = _trust

        if self.is_sync:
          url = 'accounts/{address}/trustlines?validated=true'
        else:
          url = 'accounts/{address}/trustlines'
        url = url.format(address=self.src_address)

        return url, _para

class RemoveTrustLine(Operation):
    def __init__(self, src_address):
        super(RemoveTrustLine, self).__init__(src_address)
        self.counterparty = ""
        self.currency = ""
        self.frozen = False

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].counterparty) == 0:
                #logger.error("setCounterparty first:" + func.__name__)
                raise JingtumOperException("setCounterparty first before oper.")
            elif args[0].currency == "":
                #logger.error("setCurrency first:" + func.__name__)
                raise JingtumOperException("setCurrency first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setCounterparty(self, counterparty):
        self.counterparty = counterparty

    def setLimit(self, limit):
        self.trust_limit = limit

    def setCurrency(self, currency):
        self.currency = currency

    def setTrustlineFrozen(self, frozen):
        self.frozen = frozen

    @para_required
    def oper(self):
        _trust = {}
        _trust["limit"] = 0
        _trust["currency"] = self.currency
        _trust["counterparty"] = self.counterparty
        _trust["account_trustline_frozen"] = self.frozen

        _para = {}
        _para["secret"] = self.src_secret 
        _para["trustline"] = _trust

        if self.is_sync:
          url = 'accounts/{address}/trustlines?validated=true'
        else:
          url = 'accounts/{address}/trustlines'
        url = url.format(address=self.src_address)

        return url, _para

class SubmitMessage(Operation):
    def __init__(self, src_address):
        super(SubmitMessage, self).__init__(src_address)
        self.destination_account = ""
        self.message = ""

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].destination_account) == 0:
                #logger.error("setDestAddress first:" + func.__name__)
                raise JingtumOperException("setDestAddress first before oper.")
            elif len(args[0].message) == 0:
                #logger.error("setMessage first:" + func.__name__)
                raise JingtumOperException("setMessage first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setDestAddress(self, destination_account):
        self.destination_account = destination_account

    def setMessage(self, message):
        self.message = message

    @para_required
    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret 
        _para["destination_account"] = self.destination_account
        _para["message_hash"] = self.message

        if self.is_sync:
          url = 'accounts/{address}/messages?validated=true'
        else:
          url = 'accounts/{address}/messages'
        url = url.format(address=self.src_address)

        return url, _para

        








