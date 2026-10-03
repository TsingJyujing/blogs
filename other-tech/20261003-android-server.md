# 使用Termux把Android变成一台服务器


## 起因

我之前的Pixel4因为电池鼓包了，把手机的背板微微顶起来了。顶起来以后NFC接触不良，所以我发现了。换电池的时候，可能我手上的静电打坏了什么东西，反正信号差了，前置摄像头也不能用了。就这样，这个手机在我的柜子里吃灰了几年。

最近我冒出了一些俺寻思之力：既然Android的底层也是Linux，虽说这个Linux和我们日常使用的Debian之类的发行版又有少许不同，那么能否让Android成为一台服务器呢？

诶！还真行。站在Termux巨人的肩膀上，几乎没什么要做的事情。

但是也有一些限制，这里整理一下。

## 如何操作

### 安装Termux

首先是操作系统，我的操作系统是CalyxOS 5.14.2，一个开源的、真正自由的Android。里面没有Google原装Android那么多鬼东西。
我之所用它，是因为几年前我刷机刷了它，懒得刷回去了。再者，我也更喜欢这种简洁干净的系统。

不过如果只是运行Termux的话，相信别的Android系统应该也基本都可以安装。不一定要使用CalyxOS。

我用F-Droid安装了Termux和Termux:Boot两个App，一个是核心，一个负责开机启动。

#### 多余的话

这里我得为F-Doird（和任何期待自由的人）来『广告』一下，Google即将在Android实施限制，任何Google认证的Android设备安装的App，其开发者必须在Google缴费注册。

这也意味着，想要自己写一个apk分发到世界各地，不太可能了。
当然，Google假惺惺的提供了绕过限制的方法，但是操作路径之复杂，还要等24小时（等我们自己忘了操作吗？），让分发应用收到极大的限制。
而且Google也可以任意修改这些规则。

我们这些用户，只是想要在自己买的设备上安装任何自己想要的应用，却要费千辛万苦。

而且我不负责任的说，垄断收费只是最小的副作用。这个功能给了各国政府（中国是个例外，中国基本没有Google认证Android，是以另外的方式——比如反诈中心——来控制）以屏蔽某个应用的手段，以后就可以以“国家安全”的名义来封禁任何不想要的应用，对于许多国家来说，这会强化独裁。

更多详细信息，请看[Keep Android Open](https://keepandroidopen.org/)

### 连接到手机

```shell
pkg update
pkg upgrade
pkg install openssh tmux git vim zsh # 安装一些常用的应用
```

如果下载慢，可能需要你`termux-change-repo`来换个源。

然后我们运行`whoami`获取当前用户，比如我是`u0_a219`。这里是个有点神奇的地方，这里的u0应该是指用户的编号，我这个系统当然支持多租户，但是我只创建了一个用户。a219则是指app+编号。

随后我们可以新增一个authorized_key来进行ssh的登录，也可以先设置密码通过密码登录。这部分和标准的Linux一样我就不再赘述了。

唯一需要注意的是，请使用sshd启动服务器。

重启sshd的方式是

```bash
pkill sshd
sshd
```

### 和一般Linux的区别

路径不一样，因为我们只是有用户的权限，所以文件夹也是`/data/data/com.termux/files/usr`而不是挂在根目录下。手机存储的路径在`/storage/emulated/0/`，这个老Android用户肯定都熟。

其次也没有systemd这种东西，所以服务器是作为一个正常的App来运行的。比如我之后运行Prometheus，就是直接用二进制启动的。

开机启动请编辑 `~/.termux/boot/start-server` 里面写

```bash
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
/data/data/com.termux/files/usr/bin/sshd
# 别的有的没的。。。
```

申请端口开放的时候只能申请8000以上的端口，不过一般都够用了。

最大的区别其实是glibc没有了朋友！Android的C库是Bionic。至于为什么要费劲搞一个C库，只能说glibc的历史包袱太多了。而且Android本身也不是服务器，对userspace的要求也不一样。

可是大多数标准的Linux App（特别是C/C++开发的那些）都会用到glibc，所以它们大多得重新编译。

但是自带Runtime的语言就没事了，比如你可以安装Python，Golang，rust，前者是解释器，后面两个则可以跨平台编译，只要你不是调用了C库，事情就很简单了。

但是考虑到大多数软件都不会闲到构建一个Android的版本，很多时候还是得自己编译，比如我使用pipx安装uv的时候，就得重新用rust编译uv，rust的编译工作量大家都懂，我觉得我的Pixel4都要冒火星子了。


#### 多余的话

- 也没有Root权限，所以docker这种东西是想不要想（当然可以Root但是我只打算运行），如果有兴趣，请确认这个文档：[Docker on Android ](https://gist.github.com/FreddieOliveira/efe850df7ff3951cb62d74bd770dce27)
- 如果你想要真正的 Debian 用户空间，可以试试`pkg install proot-distro`然后`proot-distro install debian` + `proot-distro login debian`，我这次是探索直接在Android下面运行App能到什么程度，不管这个。

### 跑Prometheus

为什么我决定用Pixel跑Prometheus呢？主要是下面几个原因。

- Prometheus完全用Go写成，Go有自己的Runtime，不依赖glibc，所以我不用重新编译（有空还是重新编译的好）
    - 顺便一提， 编译的时候配合GOOS=android GOARCH=arm64即可。
- 我的手机的存储跑Prometheus正好，而且还是SSD，速度快。
- 手机自带电池，作为监控和系统，这很完美了。
- 最近我运行在别处的Prometheus有一点死了（主要是外接硬盘的寿命差不多了）

直接到官网下载给Linux ARM64准备的Prometheus的二进制文件，解压下来就能跑。要是没有Termux，我可能就得用gomobile先把Prometheus编译成AAR，然后再用Kotlin写一个简单的控制和配置界面了，那么会麻烦特别多。

之后我可能会把Loki之类的服务也放到这里。

### 安装uv

我也是没有特别期待它能运行多少Python的应用，因为很多Python的程序都有C扩展，安装要么慢，要么干脆不能安装。
但是uv用了rust的依赖，所以用来解释一下rust编译的问题是再合适不过了。

首先就是确保你的Termux里面安装了rust：`pkg i rust`

其次要设置正确的ANDROID_API_LEVEL，可以这么获取：`export ANDROID_API_LEVEL=$(getprop ro.build.version.sdk)`


### 还能干什么？


其实它可以作为一个很好的干杂活的服务器。由于缺失了systemd这些关键的系统组件，其应用还是受到了不小的限制。运行也不是很稳定，比如负载重的时候sshd都可能被挤崩。

话虽如此，我们都开始拿手机当服务器玩儿了，最重要的肯定是开心咯？谁会在乎可靠性和性能呢？
