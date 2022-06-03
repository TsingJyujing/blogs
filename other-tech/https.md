# Let's encrypt -- 让我们一起愉快的使用HTTPS

## 前言

最近几年，我们跑步进入了HTTPS的时代，得益于SSL，我们的隐私得到了非常好的保护。 HTTPS的根基是[非对称加密技术](https://www.liaoxuefeng.com/wiki/1252599548343744/1304227873816610)，这个技术可以在即使有第三方完整监听的情况下进行安全的数据传输，可谓是对抗极权，保护个人利益的神器。

当然了，最近美国有人准备[以禁止儿童色情的名义禁止点对点加密](https://www.theguardian.com/technology/2020/mar/06/us-internet-bill-seen-as-opening-shot-against-end-to-end-encryption)，这就是后话了。

除了安全以外，HTTPS还可以杜绝很多运营商的流氓行为，比如HTTP劫持和DNS劫持。

* [遇到运营商的 DNS 劫持广告应该怎么办？](https://www.zhihu.com/question/20418863)
* [为什么运营商劫持的行为会普遍存在且无人监管？](https://www.zhihu.com/question/29340133)

我以前还住在上海的时候就遇到过联通的劫持，给你的HTTP页面注入广告，都TM注入到我们公司的GIT服务器上了。

## 为什么HTTPS这么难

作为一台个人PC，不可能存下所有网站的证书，更何况证书还会更新，这就变成了一个先有鸡还是现有蛋的问题，为了解决这个问题，我们引入了一个叫“根证书”的概念。 只有根证书签发的证书才是可信的，制作一张证书本身不需要任何费用，但是：

> 审核 ，验证 CSR 成本，支持成本，法律成本(保险费用，担保费用) 要进入各个浏览器的根证书列表，WebTrust 年度审计费用，是很大的开销 一些浏览器厂商还会对植入根证书列表的 CA 收费 基础设施开销，CRL 和 OCSP 服务器成本 验证 CSR：就是提交证书申请后，CA要做多项验证，越是高级的证书（比如EV）验证越麻烦。不固定开销，有些要花费很多人力和时间来完成。 CA链费用：新开的CA公司要等5-10年，才会被普遍信任，才能广泛进入根证书链。要想加快点，就得给别的大牌CA公司掏钱，买次级证书。

所以现在市面上的HTTPS证书大约是几百到几千元不等。

## 为什么不用某些免费签发HTTPS证书

比如阿里云就提供一次管一年的免费HTTPS证书，但是这个证书不能做到泛解析，而且相比以前，现在的阿里云把免费HTTPS的申请藏的越来越深了，绞尽脑汁让你买5800一年的证书。兄弟，我一个不盈利的个人站哪来这么多钱给你坑，所以果断选择了Let's Encrypt。

## Let's Encrypt

但是HTTPS其实不需要这么麻烦，不是吗？我们只需要证明你是你就可以了，于是就有了 [https://letsencrypt.org/](https://letsencrypt.org/) ，通过某种约定（比如在网站的某个目录下放一个特定的文件，或者增加一条解析什么的）证明网站是你的，我们就可以用根证书为你签名一张HTTPS证书。

具体的原理在官网上可以看到：[Let's Encrypt 的运作方式](https://letsencrypt.org/zh-cn/how-it-works/)。

一次生成的证书管3个月，但是只要你能控制服务器，其实可以用定时任务自动续命。

首先是安装软件：

```bash
apt-get install letsencrypt -y
```

随后生成证书就可以了：

```bash
letsencrypt certonly --standalone
```

输入命令以后一步步操作，证书就有了。 在执行之前记得停止你的Nginx（或者其它）服务器，你需要空出443端口等待证书发行方的检验，整个过程非常快，可以在1分钟内完结。

## ACME协议

ACME的全称是 "Automatic Certificate Management Environment" 自动证书管理环境。详细的内容可以看这里：[RFC 8555](https://datatracker.ietf.org/doc/rfc8555/?include\_text=1)

ACME协议的好处是不需要停止你的服务器，只需要加上一个“无意义”的域名解析，证明域名是你的就可以。缺点就是需要加一条解析会麻烦一点。

还有一个好处就是可以实现泛域名。

ACME的一个比较好的实现在这里：[acmesh-official/acme.sh](https://github.com/acmesh-official/acme.sh) 结合你的域名提供商，可以做到快速生成，自动续命。

首先安装ACME.SH

```bash
curl  https://get.acme.sh | sh
```

由于我是在阿里云上买的域名，所以首先在阿里云上生成Key和Secret并且赋予DNS和域名的管理权限。其它参见[官方文档](https://github.com/acmesh-official/acme.sh/wiki/%E8%AF%B4%E6%98%8E)

随后填写你的环境变量后就可以开始执行证书制作了。

```bash
export Ali_Key="sdfsdfsdfljlbjkljlkjsdfoiwje"
export Ali_Secret="jlsdflanljkljlfdsaklkjflsa"

acme.sh --issue --dns dns_ali -d example.com -d www.example.com
```

这个执行大约需要3～5分钟，可以去泡杯咖啡，回来以后一切就都设置好了。

随后会给你的crontab里面加上一条记录：

```
45 0 * * * "/home/[你的用户名]/.acme.sh"/acme.sh --cron --home "/home/[你的用户名]/.acme.sh" > /dev/null
```

这样就可以随时保持更新了，如果你觉得心里不舒服，可以修改或者删除。 所有的东西都放在：`/home/[你的用户名]/.acme.sh` 里面，移除也很方便。

## Nginx 配置

有了证书以后，我们可以给HTTP升级了！

```
server { # 自动跳转到HTTPS
    listen      80;
    server_name [你的域名];
    return      302 https://$server_name$request_uri;
}

server {

    # Setup HTTPS certificates
    listen       443 ssl;
    server_name  [你的域名];
    ssl_certificate /home/[你的用户名]/.acme.sh/[你的域名]/fullchain.cer;
    ssl_certificate_key /home/[你的用户名]/.acme.sh/[你的域名]/[你的域名].key;
    ssl_session_timeout  5m;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_protocols SSLv3 TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers   on;

    location / {
        proxy_set_header X-Real-IP         $remote_addr;
        proxy_set_header X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Forwarded-Host  $http_host;
        proxy_set_header Host              $http_host;
        proxy_max_temp_file_size           0;
        proxy_pass                         http://[你的upstream];
        proxy_redirect                     http:// https://;
    }
}
}
```

注意`ssl_certificate`要用`fullchain.cer`，我之前踩坑了，网站在浏览器里是正常的，但是如果用Python访问就会显示SSL错误，原因就没有提供完整的证书。

## 总结

总之，用 Let's Encrypt 生成证书，首先你要能控制自己的服务器，其次开头的配置会有一点复杂，但是配置完以后，就可以有永久免费的证书了。

网上还有一些方案使用certbot或者其它工具，本质上大同小异。但是如果你是成立了一家公司，就不要省这些小钱了。
