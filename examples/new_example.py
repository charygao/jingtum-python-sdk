# -*- coding:utf-8 -*-
import sys 
import time
sys.path.append("../")

from jingtumsdk.server import APIServer, WebSocketServer, TTongServer, Server
from jingtumsdk.account import Wallet, FinGate
from jingtumsdk.logger import logger
from jingtumsdk.operation import SubmitPayment, CreateOrder, AddRelation, AddTrustLine, \
    CancelOrder, RemoveRelation, RemoveTrustLine

# Please note the following addresses are only for Jingtum test network and they 
# do not work with Jingtum network.
# root account used for test
test_address = ""
test_secret = ""

//One example issuer in Jingtum test network.
test_issuer = "jBciDE8Q3uJjf111VeiUNM775AMKHEbBLS"

# Account with enough balances used for test
# user can get these accounts by contacting Jingtum developing center.
test_ulimit_address = "" 
test_ulimit_secret = "" 

# Fingate account used for issuing Tum test
# Need to get these information from Jingtum FinGate websites
# fingate.jingtum.com or tfingate.jingtum.com
ekey = ""
custom = ""
test_currency = ""

# init FinGate
fingate = FinGate()

tongtong testing
fingate.setConfig(custom, ekey)
order = fingate.getNextUUID()
ret = fingate.issueCustomTum(order, test_currency, "123.45", test_ulimit_address)
logger.info("issueCustomTum:" + str(ret))

logger.info("queryIssue:" + str(fingate.queryIssue(order)))

ret = fingate.queryCustomTum(test_currency, int(time.time()))
logger.info("queryCustomTum:" + str(fingate.queryIssue(order)))

# init test wallet
master_wallet = Wallet(test_address, test_secret)
master_unlimit_wallet = Wallet(test_ulimit_address, test_ulimit_secret)

# create my wallet
my_wallet = None
ret = fingate.createWallet()
my_address, my_secret = None, None
if ret.has_key("success") and ret["success"]:
    my_address, my_secret = ret["wallet"]["address"], ret["wallet"]["secret"]
    logger.info("My Account: %s-%s" % (my_address, my_secret))
    

# websocket init and subscribe
ws = WebSocketServer()
ws.subscribe(my_address, my_secret)

# active wallet
fingate.setActivateAmount(1000)
sp = SubmitPayment(test_address)
sp.addAmount("SWT", fingate.getActivateAmount())
sp.addDestAddress(my_address)
sp.addSrcSecret(test_secret)
logger.info(sp.submit())

class WalletTest(Wallet):
    def __init__(self, address, secret):
        super(WalletTest, self).__init__(address, secret)
        self.wallet_status = 0
        
        self.last_order_hash = None
        self.last_resource_id = None

        self.isActivated = False

    def set_wallet_status(self, status):
        self.wallet_status = status

    def get_wallet_status(self):
        return self.wallet_status

    def set_last_order_hash(self, hash_id):
        self.last_order_hash = hash_id

    def set_last_resource_id(self, resource_id):
        self.last_resource_id = resource_id

    def on_ws_receive(self, data, *arg):
        logger.info("do_socket_receive0")

        if data.has_key("success") and data["success"]:
            if my_wallet and data.has_key("type") and data["type"] == "Payment":
                ret = my_wallet.getBalance()
                print "2333333", ret
                self.isActivated = True
                if self.get_wallet_status() == 0:
                    self.set_wallet_status(1)
                elif self.get_wallet_status() == 2:
                    self.set_wallet_status(3) #3
            elif data.has_key("type") and data["type"] == "OfferCreate":
                logger.info("offer created:" + str(data) + str(arg))

                # set last order hash for next test
                if data.has_key("transaction"):
                    self.set_last_order_hash(data["transaction"]["hash"])

                self.set_wallet_status(6)
            elif data.has_key("type") and data["type"] == "OfferCancel":
                logger.info("offer canceled:" + str(data) + str(arg))
                self.set_wallet_status(8)
            elif data.has_key("type") and data["type"] == "TrustSet":
                logger.info("trust seted:" + str(data) + str(arg))
                self.set_wallet_status(14)
            else:
                logger.info("do_socket_receive:" + str(data) + str(arg))

# init my wallet
my_wallet = WalletTest(my_address, my_secret)

# register ws callback
ws.setTxHandler(my_wallet.on_ws_receive)

while 1:
    if my_wallet and my_wallet.isActivated:
        if my_wallet.get_wallet_status() == 1: # USD payment, from ulimit wallet to my wallet
            usd = SubmitPayment(test_ulimit_address)
            usd.addAmount("CNY", 100, test_issuer)
            usd.addDestAddress(my_address)
            usd.addSrcSecret(test_ulimit_secret)
            ret = usd.submit()
            if ret.has_key("success") and ret["success"]:
                my_wallet.set_last_resource_id(ret["client_resource_id"])
            my_wallet.set_wallet_status(2)
        elif my_wallet.get_wallet_status() == 3:
            r = my_wallet.getPayment(my_wallet.last_resource_id)
            logger.info("get_payment test:" + str(r))
            r = my_wallet.getPaymentList(results_per_page=3, page=1)
            logger.info("get_payments test:" + str(r))    
            my_wallet.set_wallet_status(4)
        elif my_wallet.get_wallet_status() == 4:
            r = my_wallet.getPathList(my_wallet.address, 
                "1.00", "CNY", issuer=test_issuer)
            logger.info("get_paths test:" + str(r))
            
            # create order
            co = CreateOrder(my_wallet.getAddress())
            co.setTakePays("CNY", 20, test_issuer)
            co.setTakeGets("SWT", 10)
            co.addSrcSecret(my_wallet.getSecret())
            co.submit()

            my_wallet.set_wallet_status(5)
        elif my_wallet.get_wallet_status() == 6:
            r = my_wallet.getOrderList()
            logger.info("get_account_orders test:" + str(r))

            # cancel order
            co = CancelOrder(my_wallet.getAddress())
            co.setOrderNum(1)
            co.addSrcSecret(my_wallet.getSecret())
            r = co.submit()
            logger.info("cancel_order 1 test:" + str(r))
            my_wallet.set_wallet_status(7) #7
        elif my_wallet.get_wallet_status() == 8:
            if my_wallet.last_order_hash is not None:
                r = my_wallet.getOrder(my_wallet.last_order_hash)
                logger.info("get_order_by_hash test:" + str(r))
            my_wallet.set_wallet_status(9)
        elif my_wallet.get_wallet_status() == 9:
            if my_wallet.last_order_hash is not None:
                r = my_wallet.getTransaction(my_wallet.last_order_hash)
                logger.info("retrieve_order_transaction test:" + str(r))
            r = my_wallet.getTransactionList(destination_account=my_wallet.getAddress())
            logger.info("order_transaction_history test:" + str(r))
            my_wallet.set_wallet_status(10)
        elif my_wallet.get_wallet_status() == 10:
            # add relation
            ar = AddRelation(my_wallet.getAddress())
            ar.addAmount("CNY", 5, test_issuer)
            ar.setRelationType("authorize")
            ar.setCounterparty(test_address)
            ar.addSrcSecret(my_wallet.getSecret())
            r = ar.submit()

            logger.info("add_relations test:" + str(r))
            time.sleep(8)
            try:
                r = my_wallet.getRelationList(relations_type="authorize", counterparty=test_address, 
                    currency="USD+"+test_issuer)
                #r = my_wallet.getRelationList()
                logger.info("get_relations test:" + str(r))
            except Exception, e:
                logger.error("get_relations:" + str(e)) 
            my_wallet.set_wallet_status(11)
        elif my_wallet.get_wallet_status() == 11:
            try:
                r = my_wallet.getCoRelationList(test_address, test_secret, "authorize", "USD+"+test_issuer)
                #r = my_wallet.getCoRelationList(test_address, test_secret)
                logger.info("get_counter_relations test:" + str(r))
            except Exception, e:
                logger.error("get_counter_relations:" + str(e)) 
            try:
                # remove relation
                rr = RemoveRelation(my_wallet.getAddress())
                rr.addAmount("CNY", 5, test_issuer)
                rr.setRelationType("authorize")
                rr.setCounterparty(test_address)
                rr.addSrcSecret(my_wallet.getSecret())
                r = rr.submit()
                logger.info("delete_relations test:" + str(r))
            except Exception, e:
                logger.error("delete_relations:" + str(e)) 
            my_wallet.set_wallet_status(12)
        elif my_wallet.get_wallet_status() == 12:
            # add trustline
            ot = AddTrustLine(my_wallet.getAddress())
            ot.setCounterparty(test_ulimit_address)
            ot.setCurrency("CNY")
            ot.setLimit(200)
            ot.addSrcSecret(my_wallet.getSecret())
            r = ot.submit()

            logger.info("add_trustline test:" + str(r))
            my_wallet.set_wallet_status(13)
        elif my_wallet.get_wallet_status() == 14:
            r = my_wallet.getTrustLineList()
            logger.info("get_trustlines test:" + str(r)) 
            my_wallet.set_wallet_status(15)
        elif my_wallet.get_wallet_status() == 15:
            try:
                # remove trustline
                ot = RemoveTrustLine(my_wallet.getAddress())
                ot.setCounterparty(test_ulimit_address)
                ot.setCurrency("CNY")
                ot.addSrcSecret(my_wallet.getSecret())
                r = ot.submit() 
                logger.info("remove_trustline test:" + str(r))
            except Exception, e:
                logger.error("remove_trustline:" + str(e)) 
            my_wallet.set_wallet_status(16)


    time.sleep(2)
    pass
