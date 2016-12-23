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
from sign import ecdsa_sign, ecc_point_to_bytes_compressed, root_key_from_seed, parse_seed
from serialize import fmt_hex, to_bytes, from_bytes

import binascii
import hashlib
import hmac
import time

from server import Server, APIServer, TTongServer

class Account(Server):
    def __init__(self):
        super(Account, self).__init__()
        self.api_helper = APIServer()
        self.tt_helper = TTongServer()
        
    def get(self, *para):
        return self.api_helper.get(*para)

    def tt_send(self, *para):
        return self.tt_helper.send(*para)


class FinGate(Account):
    def __init__(self):
        super(FinGate, self).__init__()

        self.tran_perfix = Config.TRAN_PERFIX
        self.trust_limit = Config.TRUST_LIMIT

        self.custom = ""
        self.ekey = ""
        self.activate_amount = 0

    def setPrefix(self, perfix):
        self.tran_perfix = perfix

    def getPrefix(self):
        return self.tran_perfix

    def createWallet(self):
        #return ("wallet/new", )
        return self.get("wallet/new", )

    def getNextUUID(self):
        return "%s%d"%(self.tran_perfix, int(time.time() * 1000))

    def getTrustLimit(self):
        return self.trust_limit

    def setTrustLimit(self, limit):
        self.trust_limit = limit

    def getActivateAmount(self):
        return self.activate_amount

    def setActivateAmount(self, amount):
        self.activate_amount = amount

    def getFinGate(self):
        pass

    def getPathRate(self):
        pass

    def setConfig(self, custom, ekey):
        self.custom = custom
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
    def issueCustomTum(self, p2_order, p3_currency, p4_amount, p5_account):
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
    def queryCustomTum(self, p2_currency, p3_date):
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

class Wallet(Account):
    def __init__(self, address, secret):
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
          parameters["currency"] = currency_type
        if counterparty is not None:
          parameters["counterparty"] = counterparty

        url = 'accounts/{address}/balances'
        url = url.format(address=self.address)        
        
        return self.get(url, parameters)
        #return url, parameters


    def getOrder(self, hash_id):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/orders/{hash_id}'
        url = url.format(address=self.address, hash_id=hash_id)
        
        #return url, parameters
        return self.get(url, parameters)

    def getOrderBook(self, base, counter):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/order_book/{base}/{counter}'
        url = url.format(address=self.address, base=base, counter=counter)
        
        #return url, parameters
        return self.get(url, parameters)

    def getOrderList(self):
        parameters = self.get_sign_info()

        url = 'accounts/{address}/orders'
        url = url.format(address=self.address)
        
        #return url, parameters
        return self.get(url, parameters)

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

    def getPaymentList(self, source_account=None, destination_account=None, exclude_failed=None, 
        direction=None, results_per_page=None, page=None):
        parameters = self.get_sign_info()

        if source_account is not None:
          parameters["source_account"] = source_account
        if destination_account is not None:
          parameters["destination_account"] = destination_account
        if exclude_failed is not None:
          parameters["exclude_failed"] = exclude_failed
        if direction is not None:
          parameters["direction"] = direction
        if results_per_page is not None:
          parameters["results_per_page"] = results_per_page
        if page is not None:
          parameters["page"] = page

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

    def getPathList(self, destination_account, value, currency, issuer=None):
        parameters = self.get_sign_info()

        elements = filter(bool, (value, currency, issuer))
        destination_amount = '+'.join(map(str, elements))
        url = 'accounts/{source}/payments/paths/{target}/{amount}'
        url = url.format(
          source=self.address,
          target=destination_account,
          amount=destination_amount,
        )

        #return url, parameters
        return self.get(url, parameters)

    def getTrustLineList(self, currency=None, counterparty=None, limit=None):
        parameters = self.get_sign_info()

        if currency is not None and counterparty is not None and limit is not None:
            parameters.upate({"limit": str(limit), "currency": currency_type, "counterparty": counterparty})

        url = 'accounts/{address}/trustlines'.format(address=self.address)

        #return url, parameters
        return self.get(url, parameters)

    def getTransactionList(self, source_account=None, destination_account=None, exclude_failed=None, \
        direction=None, results_per_page=None, page=None):
        parameters = self.get_sign_info()

        if source_account is not None:
          parameters["source_account"] = source_account
        if destination_account is not None:
          parameters["destination_account"] = destination_account
        if exclude_failed is not None:
          parameters["exclude_failed"] = exclude_failed
        if direction is not None:
          parameters["direction"] = direction
        if results_per_page is not None:
          parameters["results_per_page"] = results_per_page
        if page is not None:
          parameters["page"] = page

        url = 'accounts/{address}/payments'
        url = url.format(address=self.address)

        #return url, parameters        
        return self.get(url, parameters)





