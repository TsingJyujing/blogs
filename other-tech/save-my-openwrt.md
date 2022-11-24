# 拯救变砖的OpenWRT路由器

我的路由器是[TP-Link Archer C7 V5](https://www.tp-link.com/us/home-networking/wifi-router/archer-c7/v5/)，之后刷了[OpenWRT](https://openwrt.org/toh/tp-link/archer_c7)系统。

其实之所以要用OpenWRT，还是因为官方的固件不稳定（没错，不如OpenWRT稳定），每周左右就要“死”上一次，无法联网。重启还不能解决问题，非得恢复并且重新配置不可。这一点让我多少后悔买TP-Link的路由器。

而且OpenWRT的本身是Linux，可玩性更好，这样就可以更好的配置我的网络环境了。

今早起床，网络猛然不能用了，于是我切换到了一个备用的路由器，一遍琢磨怎么修复。

其实这个时候我应该做的是：

- 逐个断开有线的连接；
- 同时重启PPPoE并检查网络。

但是我不知道怎么脑子抽抽了，居然删掉了`br-lan`，这下作大死直接无法连接到路由器了。

## 恢复出厂设置

[官方文档在这里](https://openwrt.org/docs/guide-user/troubleshooting/failsafe_and_factory_reset)。

首先找一台电脑，随便入接一个有线的LAN口。在电脑端设置有线连接的静态IP为 192.168.1.2 (2～254都行，你挑个吉利的数字吧)，子网掩码（subnet mask）设置为`255.255.255.0`，网关（gateway）设置为`255.255.255.1`。
设置完成后给路由器断电，随后找一根牙签，顶着Reset按钮不要放，同时给路由器上电。上电以后仍然不要放手，一直等到电源灯开始狂闪烁的时候再松手。

也可以电脑时刻`ping 192.168.1.1`，看到ping通了再撒手。

这个时候一些教程提示`telnet 192.168.1.1`，但是如果你的路由器版本够新的话是需要用ssh的，只有15.05及以前需要telnet：

> Note that modern OpenWrt always uses SSH, but early OpenWrt releases (15.05 and before) offered a telnet connection in this state but no SSH. 

直接`ssh root@192.168.1.1`，进入以后执行`firstboot && reboot now`即可重置所有的配置。

## 注意

路由器的整体状态会受所连接设备的影响（按照道理这不应该出现，但是急着上班没时间看了），所以在恢复的时候尽量保证只连接必要的设备，甚至可以设置好PPPOE以后再连接WAN口网线并Restart连接。

操作路由器的时候一定要冷静，记得Review自己的修改再Apply，避免造成生产事故。

这次影响我网络的设备是一个RaspberryPi 4，平时就是个小透明，但是不知道这次怎么了，居然能搞断我的网络。
