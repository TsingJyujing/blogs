# IBKR(日本)相关资料

## 开户

之所以选择IBKR是因为市场支持多，支持程序化交易（在日本不是很多，好像Moomoo也还行），对Linux的支持也很好。账户持有也没有任何费用。

因为日本有日本特色的监管体系，IBKR在日本的开户也变得极为繁琐。https://www.interactivebrokers.co.jp/

总体没有什么需要注意的，顺着提交资料走下去就可以了。开户还等挺久的，

开户以后需要往里面转钱才能使用（包括获取数据等等），转账也需要Review我真的是服了，日本金融效率这一块……

税金这一块还得之后确认一下，是直接扣了还是要报税。

## API Gateway和TWS

- TWS下载：https://www.interactivebrokers.com/en/trading/download-tws.php
- IB Gateway下载：https://www.interactivebrokers.com/en/trading/ibgateway-latest.php?p=stable

TWS是桌面程序，IB Gateway是API的Gateway。

登录的时候有几个选项，一个是FIX CTCI，这个是专业版用的FIX API，我们普通人只能用IB规范的私有API。

Live Trading是真实交易场景，Paper Trading是模拟环境，可以从模拟环境测试起。

### 程序的显示问题

这两个程序都是Java Swing程序（爷青回），在高分辨率下的显示很奇怪。

在安装包下面有一个`.vmoptions`文件，比如TWS的是`{application-path}/tws.vmoptions`，找到以后添加这么一行：

```
-Dsun.java2d.uiScale=2
```

（其中的2可以根据你的实际情况改）就可以让界面大一些。