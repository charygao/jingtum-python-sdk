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
from sign import ecdsa_sign, ecc_point_to_bytes_compressed, root_key_from_seed, parse_seed, get_secret, get_jingtum_from_secret
from serialize import fmt_hex, to_bytes, from_bytes

import binascii
import hashlib
import hmac
import time

from server import Server, APIServer, TumServer

path_convert = {}

class JingtumOperException(Exception):
    pass

class Amount(dict):
    def __init__(self, value, currency, issuer=None):
        self['value'] = str(value)
        self['currency'] = str(currency)
        self['issuer'] = str(issuer) 

class Memo(dict):
    def __init__(self):
        pass

    def setType(self, value):
        self['memo_type'] = value

    def setData(self, value):
        self['memo_data'] = value

class Account(Server):
    def __init__(self):
        super(Account, self).__init__()
        self.api_helper = APIServer()
        self.tt_helper = TumServer()
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            self.tt_helper.setTest(True)

    def get(self, url, para, callback=None, cb_para=None):
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            self.tt_helper.setTest(True)
        
        if callback is None:
            return self.api_helper.get(url, para)
        else:
            self.api_helper.getasyn(url, para, callback=callback, cb_para=cb_para)
            return None

    def tt_send(self, *para):
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            self.tt_helper.setTest(True)
        return self.tt_helper.send(*para)

    def submit(self, url, para, callback=None):
        from server import g_test_evn
        if g_test_evn:
            self.api_helper.setTest(True)
            self.tt_helper.setTest(True)

        if callback is None:
            return self.api_helper.post(url, para, callback=callback)
        else:
            self.api_helper.postasyn(url, para, callback=callback)
            return None


class FinGate(Account):
    Tran_Perfix = Config.TRAN_PERFIX
    DEVLOPMENT = True
    def __init__(self):
        super(FinGate, self).__init__()

        self.tran_perfix = Config.TRAN_PERFIX
        self.trust_limit = Config.TRUST_LIMIT

        self.custom = ""
        self.ekey = ""
        self.activate_amount = 25

        self.fingate_address = None
        self.fingate_secret = None

    def __new__(self, *args, **kw):  
        if not hasattr(self, '_instance'):  
            orig = super(FinGate, self)  
            self._instance = orig.__new__(self, *args, **kw)  
        return self._instance  

    def setAccount(self, fingate_secret, fingate_address):
        self.fingate_address = fingate_address
        self.fingate_secret = fingate_secret

    def setPrefix(self, perfix):
        self.tran_perfix = perfix

    def getPrefix(self):
        return self.tran_perfix

    def createWalletServer(self):
        #return ("wallet/new", )
        my_address, my_secret, wallet = None, None, None
        ret = self.get("wallet/new", )
        if ret.has_key("success") and ret["success"]:
            my_address, my_secret = ret["wallet"]["address"], ret["wallet"]["secret"]
            print "My Account: %s-%s" % (my_address, my_secret) 
            wallet = Wallet(my_secret, my_address)

        return wallet

    def createWallet(self):
        my_secret = get_secret()
        my_address = get_jingtum_from_secret(my_secret)
        
        print "My Account: %s-%s" % (my_address, my_secret) 
        wallet = Wallet(my_secret, my_address)

        return wallet


    def getNextUUID(self):
        return "%s%d"%(self.tran_perfix, int(time.time() * 1000))

    @classmethod
    def getNextUUID(cls):
        return "%s%d"%(cls.Tran_Perfix, int(time.time() * 1000))

    def getTrustLimit(self):
        return self.trust_limit

    def setTrustLimit(self, limit):
        self.trust_limit = limit

    def getActivateAmount(self):
        return self.activate_amount

    def setActivateAmount(self, amount):
        if amount < int(Config.MIN_ACTIVE_AMT):
            raise JingtumOperException("Active Amt must greater than %s." % Config.MIN_ACTIVE_AMT)
        self.activate_amount = amount

    def getFinGate(self):
        pass

    def getPathRate(self):
        pass

    def setToken(self, custom):
        self.custom = custom
        
    def setKey(self, ekey):
        self.ekey = ekey

    def get_hmac_sign(self, to_enc):
        enc_res = hmac.new(self.ekey, to_enc, hashlib.md5).hexdigest()
        return enc_res

    def para_required(func):
        def _func(*args, **args2): 
            if len(args[0].custom) == 0:
                #logger.error("setDestAddress first:" + func.__name__)
                raise JingtumOperException("setConfig first before issueCustomTum.")
            elif len(args[0].ekey) == 0:
                #logger.error("setMessage first:" + func.__name__)
                raise JingtumOperException("setConfig first before issueCustomTum.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func 

    @para_required
    def issueCustomTum(self, p3_currency, p4_amount, p2_order, p5_account):
        to_enc = "%s%s%s%s%s%s" % (Config.issue_custom_tum, self.custom, 
            p2_order, p3_currency, p4_amount, p5_account)
        hmac = self.get_hmac_sign(to_enc)
        datas = {
            "cmd": Config.issue_custom_tum, 
            "custom": self.custom, 
            "order": p2_order, 
            "currency": p3_currency,
            "amount": p4_amount,
            "account": p5_account,
            "hmac": hmac
        }

        #return self.tt_address, datas
        return self.tt_send(self.tt_address, datas)

    @para_required
    def queryIssue(self, p2_order):
        to_enc = "%s%s%s" % (Config.query_issue, self.custom, p2_order)
        hmac = self.get_hmac_sign(to_enc)
        datas = {
            "cmd": Config.query_issue, 
            "custom": self.custom, 
            "order": p2_order, 
            "hmac": hmac
        }

        #return self.tt_address, datas
        return self.tt_send(self.tt_address, datas)

    @para_required
    def queryCustomTum(self, p2_currency):
        p3_date = int(time.time())
        to_enc = "%s%s%s%s" % (Config.query_custom_tum, self.custom, p2_currency, p3_date)
        hmac = self.get_hmac_sign(to_enc)
        datas = {
            "cmd": Config.query_custom_tum, 
            "custom": self.custom, 
            "currency": p2_currency, 
            "date": p3_date,
            "hmac": hmac
        }

        #return self.tt_address, datas
        return self.tt_send(self.tt_address, datas)

    @para_required
    def getSignKey(self):
        return self.ekey

    @para_required
    def getToken(self):
        return self.custom

    def para_required2(func):
        def _func(*args, **args2): 
            if args[0].fingate_secret == None:
                raise JingtumOperException("setAccount first before activeWallet.")
            elif args[0].fingate_address == None:
                raise JingtumOperException("setAccount first before activeWallet.")
            else: 
                back = func(*args, **args2)  
                return back  
            
        return _func

    @para_required2
    def activeWallet(self, destination_account, 
        currency_type=Config.CURRENCY_TYPE, is_sync=False, callback=None):
        _payment = {}
        _payment["destination_amount"] = {"currency": str(currency_type), \
            "value": str(self.getActivateAmount()), "issuer": ""}
        _payment["source_account"] = self.fingate_address
        _payment["destination_account"] = destination_account
        

        _para = {}
        _para["secret"] = self.fingate_secret
        _para["payment"] = _payment
        _para["client_resource_id"] = self.getNextUUID()

        if is_sync:
          url = 'accounts/{address}/payments?validated=true'
        else:
          url = 'accounts/{address}/payments'
        url = url.format(address=self.fingate_address)

        return self.submit(url, _para, callback=callback)

    def _pri_order_book_data_process(self, ob):
        ret = {}

        if ob.has_key("order_book"):
            ret["pair"] = ob["order_book"]

        if ob.has_key("bids"):
            ret["bids"] = []
            for l in ob["bids"]:
                _r = {}
                if l.has_key("sell") and l["sell"] == False:
                    _r["total"] = l["taker_pays_total"]["value"]
                    _r["funded"] = l["taker_pays_funded"]["value"]
                else:
                    _r["total"] = l["taker_gets_total"]["value"]
                    _r["funded"] = l["taker_gets_funded"]["value"]
                _r["order_maker"] = l["order_maker"]
                _r["sequence"] = l["sequence"]
                _r["price"] = l["price"]["value"]
                ret["bids"].append(_r)

        if ob.has_key("asks"):
            ret["asks"] = []
            for l in ob["asks"]:
                _r = {}
                if l.has_key("sell") and l["sell"] == False:
                    _r["total"] = l["taker_pays_total"]["value"]
                    _r["funded"] = l["taker_pays_funded"]["value"]
                else:
                    _r["total"] = l["taker_gets_total"]["value"]
                    _r["funded"] = l["taker_gets_funded"]["value"]
                _r["order_maker"] = l["order_maker"]
                _r["sequence"] = l["sequence"]
                _r["price"] = l["price"]["value"]
                ret["asks"].append(_r)

        return ret

    def getOrderBookCB(self, data, callback):
        ret = self._pri_order_book_data_process(data)
        if callback is not None:
            callback(ret)
        else:
            return ret

    @para_required2
    def getOrderBook(self, pair, callback=None):
        #parameters = self.get_sign_info()
        ret = None
        parameters = {}

        try:
            pair = pair.replace(":", "+")
            base, counter = pair.split("/")
        except Exception, e:
            raise JingtumOperException("pair para Invalid.")

        url = 'accounts/{address}/order_book/{base}/{counter}'
        url = url.format(address=self.fingate_address, base=base, counter=counter)
        
        #return url, parameters
        if callback is None:
            data = self.get(url, parameters)
            ret = self._pri_order_book_data_process(data) 
            return ret
        else:
            data = self.get(url, parameters, callback=self.getOrderBookCB, cb_para=callback)
            return None
            


class Wallet(Account):
    def __init__(self, secret, address):
        super(Wallet, self).__init__()
        self.address = address
        self.secret = secret
        
    def getAddress(self):
        return self.address

    def getSecret(self):
        return self.secret

    def getWallet(self):
        return self.address, self.secret

    def get_sign_info(self):
        if self.api_version <> "v2":
            return {}

        timestamp = int(time.time() * 1000)

        stamp = "%s%s%s" % (Config.SIGN_PREFIX, self.address, timestamp)
        hash_stamp = hashlib.sha512(stamp).hexdigest()
        msg = hash_stamp[:64]

        key = root_key_from_seed(parse_seed(self.secret))

        para = {
          "h": msg,
          "t": timestamp,
          "s": binascii.hexlify(ecdsa_sign(key, msg)),
          "k": fmt_hex(ecc_point_to_bytes_compressed(
              key.privkey.public_key.point, pad=False))
        }

        return para

    def getBalance(self, currency=None, counterparty=None):
        parameters = self.get_sign_info()
        if currency is not None:
          parameters["currency"] = currency
        if counterparty is not None:
          parameters["counterparty"] = counterparty

        url = 'accounts/{address}/balances'
        url = url.format(address=self.address)        
        
        ret = self.get(url, parameters)
        if ret.has_key("balances"):
            _b_list = []
            for b in ret["balances"]:
                if b.has_key("counterparty"):
                    b.update(issuer=b.pop("counterparty"))
                    _b_list.append(b)

            ret["balances"] = _b_list

        return ret
        #return url, parameters

    def _pri_one_order_data_process(self, data):
        ret = {}
        a = data["taker_pays"]["currency"] + ":" + data["taker_pays"]["counterparty"] if data["taker_pays"]["counterparty"] <> "" else data["taker_pays"]["currency"] 
        b = data["taker_gets"]["currency"] + ":" + data["taker_gets"]["counterparty"] if data["taker_gets"]["counterparty"] <> "" else data["taker_gets"]["currency"]     
        if data["type"] == "buy":
            ret["pair"] = a + "/" + b
            ret["amount"] = float(data["taker_pays"]["value"])
            ret["price"] = float(data["taker_gets"]["value"]) / int(data["taker_pays"]["value"])
        else:
            ret["pair"] = b + "/" + a
            ret["amount"] = float(data["taker_gets"]["value"])
            ret["price"] = float(data["taker_pays"]["value"]) / int(data["taker_gets"]["value"])
        ret["account"] = data["account"]
        ret["type"] = data["type"]
        ret["sequence"] = data["sequence"]

        return ret


    def getOrder(self, hash_id):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/orders/{hash_id}'
        url = url.format(address=self.address, hash_id=hash_id)
        
        #return url, parameters
        ret =  self.get(url, parameters)
        if ret.has_key("order"):
            order =  self._pri_one_order_data_process(ret["order"])
            ret["order"] = order

        return ret 

    # def getOrderBook(self, base, counter):
    #     parameters = self.get_sign_info()

    #     url = 'accounts/{address}/order_book/{base}/{counter}'
    #     url = url.format(address=self.address, base=base, counter=counter)
        
    #     #return url, parameters
    #     return self.get(url, parameters)

    def getOrderList(self):
        r = {}
        parameters = self.get_sign_info()

        url = 'accounts/{address}/orders'
        url = url.format(address=self.address)
        
        #return url, parameters
        ret = self.get(url, parameters)
        if ret.has_key("orders"):
            r["orders"] = []
            for o in ret["orders"]:
                order = self._pri_one_order_data_process(o)
                r["orders"].append(order)

        ret["orders"] = r["orders"]
        return ret


    def getRelationList(self, relations_type=None, counterparty=None, currency=None, maker=0):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/relations'
        url = url.format(address=self.address)
        
        if relations_type is not None:
          parameters["type"] = relations_type
        if counterparty is not None:
          parameters["counterparty"] = counterparty
        if currency is not None:
          parameters["currency"] = currency
        if maker <> 0:
          parameters["maker"] = maker

        #return url, parameters
        return self.get(url, parameters)

    def getCoRelationList(self, counterparty, relations_type, currency, maker=0):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/co-relations'
        url = url.format(address=self.address)
        parameters.update({
          'type': relations_type, 
          'address': counterparty,
          'currency': currency,
          'maker': maker
        })

        #return url, parameters
        return self.get(url, parameters)

    def getPayment(self, hash_or_uuid):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/payments/{hash_or_uuid}'
        url = url.format(
          address=self.address,
          hash_or_uuid=hash_or_uuid
        )

        #return url, parameters
        return self.get(url, parameters)

    def getPaymentList(self, options=None):
        parameters = self.get_sign_info()

        _l = ("source_account", "destination_account", "exclude_failed", "direction", "results_per_page", "page")
        if options is not None:
            keys = list(set(_l).intersection(set(options.keys())))
            for k in keys:
                parameters[k] = options[k]

        url = 'accounts/{address}/payments'
        url = url.format(address=self.address)

        #return url, parameters
        return self.get(url, parameters)

    def getTransaction(self, hash_id):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/transactions/{id}'
        url = url.format(address=self.address, id=hash_id)

        #return url, parameters
        return self.get(url, parameters)

    def getWalletSettings(self):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/settings'
        url = url.format(address=self.address)

        #return url, parameters
        return self.get(url, parameters)

    def _processPath(self, res):
        global path_convert
        _ret = []
        if res and res.has_key("payments"):
            for l in res["payments"]:
                _r, _k = {}, ""
                if l.has_key("paths"):
                    _k = hashlib.sha1(str(l["paths"])).hexdigest()
                    if not path_convert.has_key(_k):
                        path_convert[_k] = l["paths"]
                    _r["key"] = _k

                if l.has_key("source_amount"):
                    _r["choice"] = l["source_amount"]
                    
                _ret.append(_r)
        else:
            print "error"
            raise JingtumOperException("error when processing path.")
            
        return _ret


    def getChoices(self, destination_account, amount): #getPathList
        parameters = self.get_sign_info()

        elements = filter(bool, (amount["value"], amount["currency"], amount["issuer"]))
        destination_amount = '+'.join(map(str, elements))
        url = 'accounts/{source}/payments/paths/{target}/{amount}'
        url = url.format(
          source=self.address,
          target=destination_account,
          amount=destination_amount,
        )

        #return url, parameters
        res = self.get(url, parameters)
        return self._processPath(res) 

    def getTrustLineList(self, currency=None, counterparty=None, limit=None):
        parameters = self.get_sign_info()

        if currency is not None and counterparty is not None and limit is not None:
            parameters.upate({"limit": str(limit), "currency": currency_type, "counterparty": counterparty})

        url = 'accounts/{address}/trustlines'.format(address=self.address)

        #return url, parameters
        return self.get(url, parameters)

    def getTransactionList(self, options=None):
        parameters = self.get_sign_info()

        _l = ("source_account", "destination_account", "exclude_failed", "direction", "results_per_page", "page")
        if options is not None:
            keys = list(set(_l).intersection(set(options.keys())))
            for k in keys:
                parameters[k] = options[k]

        url = 'accounts/{address}/payments'
        url = url.format(address=self.address)

        #return url, parameters        
        return self.get(url, parameters)


    def getSettings(self):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/settings'
        url = url.format(address=self.address)

        #return url, parameters        
        return self.get(url, parameters)

    def getRelations(self, relations_type=None, counterparty=None, currency=None, maker=0):
        parameters = self.get_sign_info()

        if relations_type is not None:
          parameters["type"] = relations_type
        if counterparty is not None:
          parameters["counterparty"] = counterparty
        if currency is not None:
          parameters["currency"] = currency
        if maker <> 0:
          parameters["maker"] = maker

        url = 'accounts/{address}/relations'
        url = url.format(address=self.address)

        #return url, parameters        
        return self.get(url, parameters)


