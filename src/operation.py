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

from account import path_convert, Amount, Memo

class JingtumOperException(Exception):
    pass

class Operation(object):
    def __init__(self, wallet):
        super(Operation, self).__init__()
        self.src_address = wallet.address
        self.src_secret = wallet.secret
        self.is_sync = False
        self.client_resource_id = self.getNextUUID()

        self.api_helper = APIServer()
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            
        self.validateAddress(self.src_address)

    def getNextUUID(self):
        return FinGate.getNextUUID()

    def validateAddress(self, address):
        if not JingtumBaseDecoder.verify_checksum(JingtumBaseDecoder.decode_base(address, 25)):
            raise JingtumOperException("Invalid address: %s" %  str(address))
        
    def submit(self, callback=None):
        #print self.oper()
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
        if callback is None:
            return self.api_helper.post(*self.oper(), callback=callback)
        else:
            self.api_helper.postasyn(*self.oper(), callback=callback)
            return None

    # def addSrcSecret(self, src_secret):
    #     self.src_secret = src_secret

    def setValidate(self, is_sync):
        self.is_sync = is_sync

    def setClientId(self, client_resource_id):
        self.client_resource_id = client_resource_id


class PaymentOperation(Operation):
    def __init__(self, wallet):
        super(PaymentOperation, self).__init__(wallet)
        self.amt = {}
        self.dest_address = ""
        self.path_convert = path_convert
        self.path = None
        self.memos = []

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

    def setAmount(self, amount):
        self.amt = amount

    def setDestAddress(self, dest_address):
        self.dest_address = dest_address

    def setChoice(self, key):
        if self.path_convert.has_key(key):
            self.path = self.path_convert[key]

    def setMemo(self, value):
        self.memos.append(value)


    @para_required
    def oper(self):
        _payment = {}
        _payment["destination_amount"] = self.amt
        _payment["source_account"] = self.src_address
        _payment["destination_account"] = self.dest_address

        if len(self.memos) > 0:
            _payment["memos"] = self.memos
        if self.path is not None:
            _payment["paths"] = self.path

        _para = {}
        _para["secret"] = self.src_secret
        _para["payment"] = _payment
        _para["client_resource_id"] = self.client_resource_id

        

        if self.is_sync:
          url = 'accounts/{address}/payments?validated=true'
        else:
          url = 'accounts/{address}/payments'
        url = url.format(address=self.src_address)

        return url, _para

class OrderOperation(Operation):
    SELL = "sell"
    BUY = "buy"
    def __init__(self, wallet):
        super(OrderOperation, self).__init__(wallet)
        self.order_type = "buy"
        self.base_currency, self.base_issuer = None, None
        self.counter_currency, self.counter_issuer = None, None
        self.amount = 0
        self.price = 0

    def para_required(func):
        def _func(*args, **args2): 
            if args[0].counter_currency is None or args[0].counter_issuer is None:
                #logger.error("setPair first:" + func.__name__)
                raise JingtumOperException("setPair first before oper.")
            elif args[0].base_currency is None or args[0].base_issuer is None:
                #logger.error("setPair first:" + func.__name__)
                raise JingtumOperException("setPair first before oper.")
            elif args[0].amount == 0:
                #logger.error("setAmount first:" + func.__name__)
                raise JingtumOperException("setAmount first before oper.")
            elif args[0].price == 0:
                #logger.error("setPrice first:" + func.__name__)
                raise JingtumOperException("setPrice first before oper.")
            elif args[0].src_secret == "":
                #logger.error("addDestAddress first:" + func.__name__)
                raise JingtumOperException("addSrcSecret first before oper.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    def setPair(self, pair):
        try:
            base, counter = pair.split("/")
            if base.find(":") > 0:
                self.base_currency, self.base_issuer = base.split(":")
            else:
                self.base_currency, self.base_issuer = base, ""

            if counter.find(":") > 0:
                self.counter_currency, self.counter_issuer = counter.split(":")
            else:
                self.counter_currency, self.counter_issuer = counter, ""
        except Exception, e:
            raise JingtumOperException("setPair para Invalid.")


    def setType(self, order_type):
        self.order_type = order_type

    def setAmount(self, amount):
        self.amount = amount

    def setPrice(self, price):
        self.price = price

    # def setTakePays(self, currency_type, currency_value, counterparty=""):
    #     self.takerpays["value"] = str(currency_value)
    #     self.takerpays["currency"] = str(currency_type)
    #     self.takerpays["counterparty"] = str(counterparty)

    # def setTakeGets(self, currency_type, currency_value, counterparty=""):
    #     self.takergets["value"] = str(currency_value)
    #     self.takergets["currency"] = str(currency_type)
    #     self.takergets["counterparty"] = str(counterparty)

    @para_required
    def oper(self):
        _order = {}
        takergets, takerpays = {}, {}

        if self.order_type == "sell":
            takergets["value"] = str(self.amount)
            takergets["currency"] = str(self.base_currency)
            takergets["counterparty"] = str(self.base_issuer)

            takerpays["value"] = str(self.amount * self.price)
            takerpays["currency"] = str(self.counter_currency)
            takerpays["counterparty"] = str(self.counter_issuer)
        else:
            takerpays["value"] = str(self.amount)
            takerpays["currency"] = str(self.base_currency)
            takerpays["counterparty"] = str(self.base_issuer)

            takergets["value"] = str(self.amount * self.price)
            takergets["currency"] = str(self.counter_currency)
            takergets["counterparty"] = str(self.counter_issuer)

        _order["type"] = self.order_type
        _order["taker_pays"] = takerpays
        _order["taker_gets"] = takergets

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
    def __init__(self, wallet):
        super(CancelOrderOperation, self).__init__(wallet)
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

    def setSequence(self, order_num):
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
    def __init__(self, wallet):
        super(AddRelation, self).__init__(wallet)
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
    def __init__(self, wallet):
        super(RemoveRelation, self).__init__(wallet)
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
    def __init__(self, wallet):
        super(WalletSettings, self).__init__(wallet)

    def oper(self):
        _para = {}
        _para["secret"] = self.src_secret 

        url = 'accounts/{address}/settings'
        url = url.format(address=self.src_address)

        return url, _para

class AddTrustLine(Operation):
    def __init__(self, wallet):
        super(AddTrustLine, self).__init__(wallet)
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
    def __init__(self, wallet):
        super(RemoveTrustLine, self).__init__(wallet)
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
    def __init__(self, wallet):
        super(SubmitMessage, self).__init__(wallet)
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

        








