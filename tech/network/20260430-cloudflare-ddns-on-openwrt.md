# 在OpenWRT路由器上配置Cloudflare DDNS

修订日志：
- 2026-04-30 初稿

## 前言

最近准备把一个数据库共享给小伙伴用。Cloudflared的性能不太够用，想来想去就看看能不能直接上公网，结果意外发现了家里是有公网IP的，甚至连80和443都是可用的。

上一次NTT光封禁了我的80和443端口以后我就一直没试（包括搬家后），但是现在用的是BBIQ的网络，形势可不一样了。

于是我准备把DDNS设置起来。

我上一次设置DDNS还是用Aliyun的API（[这是我的方案](https://github.com/TsingJyujing/aliyun-ddns-client)）

现在我把域名迁移到Google又迁移到Cloudflare，方法也准备换一下，直接在OpenWRT上配置。

## OpenWRT软件安装

需要在OpenWRT上安装以下软件：

```
ddns-scripts
ddns-scripts-cloudflare
ddns-scripts-services
luci-app-ddns
bind-host
```

不安装luci-app-ddns的话就没有图形界面配置，不安装bind-host的话其实也能用，但是会有一个警告，我忘记复制了，好像是无法通过TCP确认绑定的情况。

## Cloudflare Token准备

在Cloudflare上新建一个API Token，赋予DNS的编辑权限。

我知道还有一种是API Key，但是不安全，我也就没有尝试。

## 配置

安装好之后导航栏上应该出现Services，点击Services -> Dynamic DNS进入配置页面。

安装好的ddns-scripts默认带了两个配置，可以都删掉重新配置。

注意，创建配置（Service）的时候，Name是不能修改的，所以不要乱起名，回头还得删掉重来。


| Item                  | Example Value             | Comment                                                                                                      |
| --------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Lookup Hostname       | something.your-domain.com | 这个是用来确认你的IP是否正确更新了的，如果是泛解析，由于不支持直接解析*，那就随便填一个xxxxx.your-domain.com |
| IP address version    | IPv4                      | IPv6还没有普及，应该大多数人都是IPv4                                                                         |
| DDNS Service provider | cloudflare.com-v4         | 不解释                                                                                                       |
| Domain                | something@your-domain.com | 这里需要用@把域名的前后段隔离开，如果是泛解析那么就是*@your-domain.com                                       |
| Username              | Bearer                    | 如果你是用Token的话设置这个就好                                                                              |
| Password              | *********                 | 刚才你生成的Token填在这里                                                                                    |

配置好以后Save&Apply，然后Reload，应该就能看到DDNS设置成功了。

## 感想

路由器买小了。我用的是TP-Link Archer C7 v5路由器，内存都有120M，但是存储只有10M，随便安装点什么软件就满了。只能说TP-Link真的是太奸商了。
更要命的是，OpenWRT比原生的固件还要稳定。
以前我经常听书听到一半——网断了，半夜三更起来重启路由器。
对，我最初折腾OpenWRT不仅仅是为了功能，还是为了稳定性。
现在连续运行个把月一点问题都没有。我还配了一个方波UPS，现在断电都不带重启的。

如果路由器再大一点，那么我直接会把Nginx，更新SSL证书的东西全套放上去。

