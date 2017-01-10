# 井通PYTHON SDK

jingtum_sdk python 正式版， 版本号0.9.14

本SDK包括井通PYTHON语言的SDK文件库和例子
其中，例子的执行需要申请帐号，具体请参见例子中的说明.

# 安装方式：

  pip install -i https://testpypi.python.org/pypi —pre jingtum_sdk_python

# 使用

可参见example下的test.py示例。

## 产生一组新的井通帐号
```python
# init FinGate
fingate = FinGate()
fingate.setTest(True)

# create my wallet
my_wallet = None
ret = fingate.createWallet()
my_address, my_secret = None, None
if ret.has_key("success") and ret["success"]:
    my_address, my_secret = ret["wallet"]["address"], ret["wallet"]["secret"]
    logger.info("My Account: %s-%s" % (my_address, my_secret))

# Active the new wallet
fingate.setActivateAmount(25)
logger.info(fingate.activeWallet(test_address, test_secret, my_address, "SWT"))

```

## 帐号操作

### 查询帐号的余额信息
```python

ret = my_wallet.getBalance()
```

## 支付操作

### 帐号的支付
```python
    usd = PaymentOperation(test_ulimit_address)
    usd.addAmount("USD", 1, test_issuer)
    usd.addDestAddress(my_address)
    usd.addSrcSecret(test_ulimit_secret)
    ret = usd.submit()


```


## 挂单操作

### 生成挂单

```python
    co = OrderOperation(my_wallet.getAddress())
    co.setTakePays("USD", 1, test_issuer)
    co.setTakeGets("SWT", 10)
    co.addSrcSecret(my_wallet.getSecret())
    co.submit()
```

### 取消挂单

```python
    co = CancelOrderOperation(my_wallet.getAddress())
    co.setOrderNum(1)
    co.addSrcSecret(my_wallet.getSecret())
    r = co.submit()
```
