# 为PostgreSQL配置SSL加密

## 为什么要为PostgreSQL配置SSL加密

如果你的服务只是在内网使用，那么数据库大多是不需要加密的（或者自签名加密也可以），但是如果你的数据要跨区域传递，而且你也没有相应的措施来确保你的流量是加密的，那么对数据库本身加密就显得特别重要了。

说到我的情况，我是为了把我的数据库共享给我的朋友用，考虑到数据量确实不小，我采取了下面两个措施：

1. 家庭的端口直接开放（配合DDNS）暴露数据库端口；
2. 数据定期打包备份到RustFS，配合Google OAuth，朋友用Google账户登录就可以直接访问数据。

最危险的其实是1，考虑到数据安全，必须用SSL加密。

## 用什么证书进行加密？

> [!TIP] 
> 如果对HTTPS和Let's encrypt还不熟悉的，建议先阅读这篇文章：[Let's encrypt -- 让我们一起愉快的使用HTTPS](../network/https.md)

一般来说，我们有自签名和标准的CA证书两种。我这里是推荐CA证书的。
很多人可能会想，用一下自签名证书差不多就得了，用CA签发的证书多少有点小题大做了。但是这有可能遭到中间人攻击，数据还是会被解密。
既然是做安全，那就贯彻到底吧！

细说一下的话，PostgreSQL的SSL证书验证有以下几种方式：

1. require：有证书就行，无条件相信对方的证书
2. verify-ca：只要是CA签发的证书就可以，不看主机名是不是匹配
3. verify-full：在验证证书链之后，还会严格检查服务器证书中的主机名（CN 或 SAN）是否与客户端连接时指定的主机名完全匹配。

我这里用的是`verify-full`，这可以有效防止中间人攻击，因为攻击者必须拿到与你所连主机名完全匹配的证书才行，而受信任的 CA 不会轻易签发这种证书。

## 本文使用的环境

本文使用PostgreSQL 18进行配置：

```yaml
services:
  db:
    image: postgres:18
    restart: always
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: "your-password"
      POSTGRES_DB: your_db
    ports:
      - "5432:5432"
    volumes:
      - ./pgdata:/var/lib/postgresql #数据
      - ./init:/docker-entrypoint-initdb.d #初始化的时候执行的脚本
      - ./backup:/backup #用于输出备份文件
      - ./letsencrypt:/etc/letsencrypt #kavehbc/free-ssl-cloudflare输出的证书会定期同步到这里
      - ./ssl:/etc/ssl/ #实际Postgresql使用的证书
      - ./scripts:/scripts #一些脚本
```

## 如何配置SSL加密

### 配置密钥文件

首先编辑`/var/lib/postgresql/18/docker/postgresql.conf`

找到下面三行做如下配置：

```ini
ssl = on
ssl_key_file = '/etc/ssl/server.key'
ssl_cert_file = '/etc/ssl/server.crt'
```

其次，定期复制和Reload配置的脚本如下：

```bash
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /etc/ssl/server.crt
cp /etc/letsencrypt/live/your-domain.com/privkey.pem  /etc/ssl/server.key
chown postgres:postgres /etc/ssl/server.crt /etc/ssl/server.key
chmod 600 /etc/ssl/server.key
chmod 644 /etc/ssl/server.crt
psql -U postgres -c "SELECT pg_reload_conf();
```

保存到scripts里面，用cronjob定期执行。之所以不直接使用letsencrypt文件夹下的密钥是因为文件不对，我不希望乱动权限所以就干脆复制一份了。

其次，PosgreSQL对文件的权限也有要求，权限太宽也不给过，所以这里用复制是坠吼的。

### 要求数据库连接加密

其次编辑`/var/lib/postgresql/18/docker/pg_hba.conf`，我的大方针是：localhost来的连接不需要鉴权，方便我执行一些操作（默认就是如此，不要改动）。

内网来的连接需要验证密码但是数据不用SSL加密：

```
host all all 192.168.1.0/24 scram-sha-256
```

其它所有的连接都需要验证密码+SSL加密：

```
hostssl	all	all	all	scram-sha-256
```

这里设定为hostssl就是需要SSL的意思。

## 如何使用

服务器端其实才不管有的没的，反正来了非内网的连接就用SSL加密通讯，账户密码验证过了就给用。

安全的设置是在客户端的，我在pgAdmin4设置了如下参数：

- `sslmode`: `verify-full`
- `sslrootcert`: `system`

![](/img/2026-05-08-00-10-45.png)

这样就会完整的校验服务器的证书是不是有效再决定是否通信了。

### Python(psycopg3)

为了确保我们有所有CA的根证书，首先安装[certifi](https://pypi.org/project/certifi/)包。

随后连接的时候记得加上：

```py
conn: Connection = psycopg.connect(
    conninfo=db_uri,
    sslmode="verify-full",
    sslrootcert=certifi.where(),
)
```

这样就连上了。

