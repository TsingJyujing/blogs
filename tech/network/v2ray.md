# V2RAY使用方法备忘

v2ray或者v2fly是有官方文档的，但是官方文档的时不时有所错漏之处，我经过阅读他人写的文档加上自己测试，总结为这篇文章，以备我后续查用。
其路由的功能非常好用，有了路由功能就不需要经常切换网络，甚至可以直接远程配置家里的路由器。

这个文档里，配置文件的设计原则是：

1. 尽可能保证联通性，保证该访问的到的页面都要访问的到
2. 在保证1的基础上，尽可能的直接连接
3. 做好保密和伪装

## 日志模块

在Docker里面运行的时候，我习惯把日志吐到`/logs`，然后再把某个文件夹挂载到`/logs`里面。

```json
"log": {
    "loglevel": "warning",
    "access": "/logs/access.log",
    "error": "/logs/error.log"
},
```

缺点是时间一长容易忘记清理，而且也不能用在其它客户端的配置里。

所以保险起见的话：

```json
"log": {
    "loglevel": "warning"
},
```

## DNS

```json
"dns": {
    "servers": [
        "114.114.114.114",
        {
            "address": "1.1.1.1",
            "port": 53,
            "domains": [
                "geosite:geolocation-!cn"
            ]
        }
    ]
},
```


## 入口配置

入口配置会在本地打开端口，一般常用的入口配置如下：

### Socket代理

只建议在本地或者局域网内使用，不加密。

```json
{
    "listen": "127.0.0.1",
    "port": 10808,
    "protocol": "socks",
    "settings": {
        "auth": "noauth",
        "udp": true,
        "userLevel": 8
    },
    "sniffing": {
        "destOverride": [
            "http",
            "tls"
        ],
        "enabled": true
    },
    "tag": "socksxxx"
},
```

### HTTP代理

只建议在本地或者局域网内使用，不加密。

```json
{
    "listen": "127.0.0.1",
    "port": 10809,
    "protocol": "http",
    "settings": {
        "userLevel": 8
    },
    "tag": "httpxxx"
}
```

### VMESS协议代理

这里的VMESS Inbound有两种用途，第一种是单独用作服务器和客户端的传输渠道（这个时候加上WebSocket更好），第二种是在本地局域网搭建客户端以后利用手机上的App访问局域网内机器，这个时候只是借用一下这个协议（配置方便）。


```json
{
    "port": 3238,
    "protocol": "vmess",
    "settings": {
        "clients": [
            {
                "id": "a83baffa-2c05-4bd9-8d86-10c7e278997a",
                "security": "auto",
                "level": 0
            }
        ]
    },
    "tag": "v2ray"
}
```

#### 客户端配置

```json
{
    "protocol": "vmess",
    "settings": {
        "vnext": [
            {
                "address": "域名或者IP",
                "port": 12345,
                "users": [
                    {
                        "id": "a83baffa-2c05-4bd9-8d86-10c7e278997a",
                        "security": "auto",
                        "level": 0
                    }
                ]
            }
        ]
    },
    "tag": "aaa"
}
```


#### WebSocket

```json
{
    "port": 12345,
    "protocol": "vmess",
    "settings": {
        "clients": [
            {
                "id": "a83baffa-2c05-4bd9-8d86-10c7e278997a",
                "security": "auto",
                "level": 0
            }
        ]
    },
    "streamSettings": {
        "network": "ws",
        "wsSettings": {
            "path": "/data" // Need to match the config in nginx
        }
    }
},
```
##### Nginx配置

```nginxconf
server {
    listen      80;
    server_name vr.xxxx.com; # 需要配置
    return      302 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2 default_server;
    listen [::]:443 ssl http2 default_server;
    ssl_certificate /xxxxx/fullchain.cer; # 需要配置
    ssl_certificate_key //xxxxx/xxxx.key; # 需要配置
    ssl_ciphers EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+ECDSA+AES128:EECDH+aRSA+AES128:RSA+AES128:EECDH+ECDSA+AES256:EECDH+aRSA+AES256:RSA+AES256:EECDH+ECDSA+3DES:EECDH+aRSA+3DES:RSA+3DES:!MD5;
    ssl_protocols TLSv1.1 TLSv1.2 TLSv1.3;
    root /path/to/a/static/website; # 需要配置
    server_name vr.xxxx.com; # 需要配置
    location /data { # 需要配置
        proxy_redirect off;
        proxy_pass http://v2ray-server-local:12345; # 需要配置
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $http_host;
    }
}
```

建好服务器以后，将需要配置的地方改一下，主要是：

1. 域名和相应的证书
2. 一个用于伪装的静态网站
3. websocket的地址（和上面保持一致）
4. 本地的v2ray服务器的地址和端口

有一个小思考，考虑到已经使用了标准的HTTPS进行加密，其实内层的协议未必需要是vmess，甚至可以是socket。但是不知会不会暴露流量特征。

##### 客户端配置

```json
{
    "protocol": "vmess",
    "settings": {
        "vnext": [
            {
                "address": "域名或者IP",
                "port": 12345,
                "users": [
                    {
                        "id": "a83baffa-2c05-4bd9-8d86-10c7e278997a",
                        "security": "auto",
                        "level": 0
                    }
                ]
            }
        ]
    },
    "streamSettings": {
        "network": "ws",
        "security": "tls",
        "wsSettings": {
            "path": "/data"
        }
    },
    "tag": "aaa"
}
```

### 路由设置

服务端比较简单，一般直连就可以，不需要任何路由配置：

```json
{
    "protocol": "freedom",
    "settings": {},
    "tag": "direct"
},
```

客户端出口的配置如下：

```json
"routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
        {//连接家里局域网的，走代理，可删除
            "type": "field",
            "ip": [
                "192.168.1.0/24"
            ],
            "outboundTag": "aaa"
        },
        {//直连中国域名
            "type": "field",
            "outboundTag": "direct",
            "domain": [
                "geosite:cn"
            ]
        },
        {//其它的中国IP和私有IP都直连
            "type": "field",
            "outboundTag": "direct",
            "ip": [
                "geoip:cn",
                "geoip:private"
            ]
        },
        // TODO 可以增加更多配置
        {//直接连接到世界的互联网
            "type": "field",
            // "balancerTag": "blancerxxx",
            "outboundTag": "aaa",
            "network": "tcp,udp"
        }
    ],
    "balancers": [//可配置负载均衡
        {
            "tag": "blancerxxx",
            "selector": [
                "aaa",
                "bbb"
            ],
            "strategy": {
                "type": "random"
            }
        }
    ]
}
```
