+++
title = '把博客迁移到Hugo'
date = '2026-11-10'
draft = false
weight = 14
+++

# 把博客迁移到Hugo

我之前一直是用的Gitbook来管理我的博客，很早以前Gitbook也提供一个开源的方案来把我的博客编译为静态网站。
我一直使用CICD（Drone）将其自动发布到Github Pages上。
但是不知道是什么时候开始，Gitbook不再提供这样的功能。而且逐渐的越来越多的功能需要收费。

于是我决定迁移到另外一个开源的方案来代替Gitbook。

经过一番比较以后，最终我选了[Hugo](https://gohugo.io/)。

## 为什么选择Hugo

其实最开始我想到的是wordpress，但是它实在是太重了。
比起全套而专业的博客功能，我更希望能够快捷的记录并且分享。所以wordpress的高级功能对我来说并没有用。
我需要它能够生成静态网站，速度足够快，而且能够轻易的部署到Github Pages/Cloudflare Pages之类的静态网站托管平台。

## 如何使用

### Hugo编译

按照[教程](https://gohugo.io/documentation/)进行安装，之后`hugo new project xxx`就算开始了。

关于主题，我使用[hugo-book](https://github.com/alex-shpak/hugo-book)，以submodule的形式添加，这样以后升级方便，也不会占用当前repo的空间和commit记录。

一些具体的配置，可以去我博客的[github repo](https://github.com/TsingJyujing/blogs)下面看。

下面说说我觉得需要注意的几个点。

之前我的Gitbook的目录是自动生成的，所以只支持按照字母排序，但是Hugo支持记录更多的元数据，比如本文的元数据：

```md
+++
title = '把博客迁移到Hugo'
date = '2026-11-10'
draft = false
weight = 14
+++
```

里面有标题、日期还有权重之类的信息，这里面最有意思的是权重，他是会影响排序的。

所以我们不再需要使用一些诸如`z-`的技巧来修改博客的排序。

### Github设置

如各位所见，我的博客虽然在GitHub Pages上，但是是[自定义域名](https://docs.github.com/zh/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site#configuring-a-subdomain)。

这个在 <https://github.com/><user or org>/<repo>/settings/pages 里面可以修改。

以我的博客为例，设置好以后只需要在增加一条DNS记录：blog.tsingjyujing.com CNAME tsingjyujing.github.io 即可使用自定义的域名。

之后直接将[官方文档提供的WF](https://gohugo.io/host-and-deploy/deploy-to-github-pages/)复制到自己的Repo下即可方便的部署。

## 以后的打算

虽说只是分享，但是仍然想要有评论功能。

考虑到这是一个静态网站，所以我准备用[赛博菩萨Cloudflare的D1](https://www.cloudflare.com/products/d1/)来做。

我不会和中国政府一样要求实名制，相应的垃圾的评论也就更难控制。所以我准备设计Rate Limit+先审后发机制，审核使用规则+AI自动完成，反注入，反广告，检测煽动仇恨、辱骂的词汇，没有问题再显示，如果有问题就转存到日志系统以后删除。
