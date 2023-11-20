# 使用FRP进行内网穿透

我本是个有公网IP的人，奈何最近NTT把我的443端口给封禁了，我便不能再（优雅的）配合DDNS使用自带的这个动态公网IP了。

没办法，只得开了一台距离比较近的VPS，在上面设置了一个FRP服务器。在此记录一下设置的过程，以备不时之需。

## 获取FRP

FRP是一个开源的反向代理项目：https://github.com/fatedier/frp
可以从Release页面下载需要的二进制文件：https://github.com/fatedier/frp/releases

### OpenWRT

如果你的路由器够强劲，可以试试OpenWRT版本的：
- https://openwrt.org/packages/pkgdata/frpc
- https://openwrt.org/packages/pkgdata/luci-app-frpc

其中，luci-app-frpc是在路由器的配置页面上直接配置frpc，但是我试过，其实未必有直接写配置文件来的便捷。

直接：

```shell
opkg update
opkg install frpc
opkg install luci-app-frpc
```

即可。

虽然说一般不会有人要在路由器上设置FRPS，但是还是写一下：

- https://openwrt.org/packages/pkgdata/frps
- https://openwrt.org/packages/pkgdata/luci-app-frps

## 服务器配置

首先下载frp，然后解压：`tar -xzvf frp_0.52.3_linux_arm64.tar.gz`

随后将文件复制`frps`到`/usr/bin`(或者任何在PATH里的目录): `cp frp_0.52.3_linux_arm64/frps /usr/bin/`

准备以下文件：

`/etc/frp/frps.toml`

```toml
bindPort = 7000
auth.method = "token"
auth.token = "自己设置想要的密码"
# 以下配置为可选项
webServer.addr = "0.0.0.0"
webServer.port = 7500
webServer.user = "admin"
webServer.password = "自己设置想要的管理员密码"
```

`/etc/systemd/system/frps.service`：

```
[Unit]
Description = frp server
After = network.target syslog.target
Wants = network.target

[Service]
Type = simple
ExecStart = /usr/bin/frps -c /etc/frp/frps.toml

[Install]
WantedBy = multi-user.target
```

之后

```shell
systemctl daemon-reload
systemctl enable frps
systemctl start frps
```

即可启动服务，服务一经启动，即不需要进一步的配置，其余的配置都在客户端。

还有一点需要确认的是防火墙，每个系统的防火墙不一定一样，这里是Ubuntu的服务器，所以用ufw配置。

需要开放7000端口和你之后想要对外放出的端口（这里是443）：

```
ufw allow 7000/tcp
ufw allow 443
```

## 客户端配置

同样是下载软件后复制`frpc`到`/usr/bin`(或者任何在PATH里的目录): `cp frp_0.52.3_linux_arm64/frpc /usr/bin/`

准备配置文件和服务文件：

`/etc/frp/frpc.toml`

```toml
serverAddr = "VPS的地址"
serverPort = 7000
auth.method = "token"
auth.token = "自己设置想要的密码"

# 本段落可以配置多个
[[proxies]]
name = "自己给个名字"
type = "tcp"
localIP = "目标机器的地址"
localPort = 目标机器的端口
remotePort = 想要在VPS上暴露的端口
```

`/etc/systemd/system/frpc.service`

```
[Unit]
Description=Frp Client Service
After=network.target
[Service]
Type=simple
DynamicUser=yes
Restart=on-failure
RestartSec=5s
ExecStart=/usr/bin/frpc -c /etc/frp/frpc.toml
ExecReload=/usr/bin/frpc reload -c /etc/frp/frpc.toml
LimitNOFILE=1048576
[Install]
WantedBy=multi-user.target
```

之后启动服务即可

```shell
systemctl daemon-reload
systemctl enable frpc
systemctl start frpc
```

### 关于OpenWRT

如果显示`frp Client - NOT RUNNING`，需要到 http://192.168.1.1/cgi-bin/luci/admin/system/startup 里面启动（Enable&Start）frpc服务。

以及，如果目标机器和跑FRPC的机器不是同一台(如路由器跑frpc，树莓派跑服务)情况下，建议设置固定的IP地址。