# 记录一次`rsync`命令引起的异常

在开发中，我使用 `rsync -avPz --delete ./ 目标机器:目标文件夹`将我的源代码同步到目标机器上，达到本地IDE编辑，远程服务器运行的目的。
源码不多，为了省去手动操作的麻烦，我干脆使用watch命令每两秒同步一次。

中间连接内网的VPN断开一次，之后发现，机器无法SSH登陆，提示错误：`shell request failed on channel 0`，好在管理员账户还是可以登陆，登陆以后使用`sudo su - 我的用户名`，提示：`su: failed to execute /bin/zsh: Resource temporarily unavailable`。

这就很奇怪了，我确认了zsh是存在的，半信半疑之间，我还是yum重装了zsh，并且修改`/etc/password`，让我的用户使用bash，结果还是不行。网上搜索问题也都搜不到点子上。

我的直觉告诉我，可能是连接数过多了，于是我使用who命令检查，果然有好几个会话，但是仍然很奇怪，因为平时我工作的时候，偶尔会话开的比这个多的时候也有。
于是我使用 `ps aux|grep sshd|grep 我的用户名`，好家伙，洋洋洒洒出来一大堆进程，没仔细数，于是使用：

```bash
# 注意，此命令有误杀风险，最好先grep出来看一眼再加上 |awk '{print $2}'|xargs -r sudo kill -9 。
sudo ps -ef|grep sshd|grep 我的用户名|grep -v grep|awk '{print $2}'|xargs -r sudo kill -9
```

全部干掉，恢复正常。
详细起因仍然不清楚，但是这么多ssh会话除了rsync也没谁能建立了。
回头还是使用`inotify`配合`rsync`使用吧，偷懒还是不行的。