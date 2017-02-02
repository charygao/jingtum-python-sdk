# 井通PYTHON SDK

jingtum_sdk python 正式版， 版本号0.9.15

本SDK包括井通PYTHON语言的SDK文件库和例子
其中，例子的执行需要申请帐号，具体请参见例子中的说明.

## 运行环境

井通PYTHON SDK需要PYTHON 2.7以上版本。

## 安装PYTHON SDK

首先确认系统安装了pip工具。如果没有，则需要安装pip工具，具体可以参考 
(https://packaging.python.org/installing/)的说明。

  pip install -i https://testpypi.python.org/pypi —pre jingtum_sdk_python

## 程序示例

可参见example下的test.py示例和developer.jingtum.com下的说明。

### 产生新的井通帐号
```python
    # init FinGate
    fingate = FinGate()
    fingate.setMode(FinGate.DEVLOPMENT)


    # create my wallet
    my_wallet = None
    my_wallet = fingate.createWallet()

    # Active the new wallet
    # Need to setup an account with enough SWT in it.

    fingate.setAccount("snqFcH......pQYzxEEbW")
    fingate.setActivateAmount(25)
    fingate.activateWallet(my_wallet.address, callback)

```

### 查询帐号的余额信息
```python
    # init FinGate
    fingate = FinGate()
    fingate.setMode(FinGate.DEVLOPMENT)

    my_wallet = Wallet("shVC2gdG......gijqk4EsuqDF")
    ret = my_wallet.getBalance()
```

### 使用帐号进行支付
```python

    # init FinGate
    fingate = FinGate()
    fingate.setMode(FinGate.DEVLOPMENT)

    my_wallet = Wallet("shVC2gdG......gijqk4EsuqDF")
    op = PaymentOperation(my_wallet)

    op.setDestAddress('jpyyHbEWiuCA......DRrYJQzcXb')

    amt = Amount(10, "CNY", test_issuer)
    op.setAmount(amt)

    op.setClientId("20611171957")
    op.setValidate(true)

    op.submit(callback)

```

### 生成挂单

```python
    # init FinGate
    fingate = FinGate()
    fingate.setMode(FinGate.DEVLOPMENT);

    my_wallet = Wallet("shVC2gdG......gijqk4EsuqDF")
    co = OrderOperation(my_wallet)
    co.setPair("SWT/CNY:janxMdr...GewMMeHa9f");
    co.setType(OrderOperation.SELL);
    co.setAmount(20.00);
    co.setPrice(0.5);
    co.submit(callback)
```

### 取消挂单

```python
    # init FinGate
    fingate = FinGate()
    fingate.setMode(FinGate.DEVLOPMENT)

    my_wallet = Wallet("shVC2gdG......gijqk4EsuqDF")
    co = CancelOrderOperation(my_wallet)
    co.setOrderNum(54)
    co.submit(callback)
```
