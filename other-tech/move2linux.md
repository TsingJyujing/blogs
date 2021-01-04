# 简易的Linux迁移指北

这篇文章写的比较简洁，如果有什么不能理解的，可以搜索一下（但是不要用百度，否则你的疑惑可能更深）。

## 不适宜使用Linux的人群

首先说说哪些人已经被绑死在了Mac/Win的船上下不去了，别的行业不了解，我说说工程师一类的：

如果你重度依赖一些无法迁移到Linux的软件系统，比如：

- 某些CAE/CAD绘图软件
- 开发Mac和iOS程序的Xcode
- Visual Studio
- Excel VBA
- 一些硬件烧写程序和开发工具（比如Keil）
- ...

那就老老实实用Mac和Win好了。
或者电脑的驱动比较封闭，无法正常运行Linux的，我建议使用WSL体验Linux也还凑合。

如果你懒得折腾，愿意呆在舒适区，那么不论你现在用的是Mac，Win，还是Linux，切换对你都意味着痛苦，对不？

## 为什么用Linux

原因其实可以有很多，就我自己的话，除了开发方便以外，我希望控制我自己买的电脑。

前段时间Apple的OCSP服务器宕机导致我什么软件都启动不了的经历对我的刺激太大，否则看在设计美观的份上我是愿意接受Mac的。
这次宕机事件让我觉得我的电脑只是苹果公司租给我的，很没有安全感，好在这台电脑是公司的，否则我真的要气死了。
Windows就更不要说了，我是Win95开始的骨灰用户，写注册表调Win32API开发都经历过，以前还挺喜欢，自从Win10开始了：“我是你爹，你必须更新”的模式以后，就再也不想用了。

## 安装Ubuntu 20遇到的坑

我个人现在用Ubuntu，但是我同样推荐Deepin，尤其是你不太愿意花时间配置一些细节，Deepin给你提供一个比较完美的开箱即用的体验。不过需要说的是，新版（20）Deepin的默认界面，我觉得是变丑了。

- 无线驱动有可能打不上
    - 其实这个和Ubuntu其实没有关系，如果Securety Boot开启的话，驱动就不一定能打的上
    - 话虽如此，Securety Boot该开还是最好要开的
- 磁盘的话，XPS上不兼容RAID模式，要选ACHI模式
- 不推荐安装系统的时候同时安装更新，完全可以安装好以后一边刷B站Youtube一边喝可乐一边更新啊！
    - 尤其是家里或者公司里搭建了Nexus的APT镜像的，安装好以后先修改源再更新，那叫一个快啊！
        - 当然前提是你家里或者公司里还有一个Linux服务器
- 老生常谈了，安装的时候最好选择英语，否则文档，下载之类的文件夹都是中文的，在命令行里不太方便。
- Ubuntu 20 的声音在有多个输出设备的时候切换的优先级很诡异

## 老生常谈的软件问题

初到Linux的时候，曾经有很多困难，比如烧写U盘的时候没了破解版的UltraISO，但是事实上Linux下根本不需要这么麻烦。比如制作Win10的启动盘，其实格式化成NTFS以后往里面拖文件就好。如果你实在想烧某个盘，可以用dd命令，如果觉得命令行有门槛，Ubuntu还有启动盘制作工具，磁盘管理工具还支持创建和还原磁盘镜像，树莓派一般是这么烧写的。

在比如，Putty和XShell没了，但是你有原生的SSH啊，你完全可以通过SSH Config文件配置跳板机，配合ZSH的自动补全，其实效率只有更高。
没有WinSFTP，但是scp速度更快，rsync灵活度更高，实在想用图形化，有FileZilla，事实上，用了Linux后，我都不用FileZilla了。

很多时候，我们沉溺在Wdinwos下拙劣的模仿者里，回过头来看一看Linux，其实最佳实践已经给我们准备好了。

- 视频播放：不要说了，VLC永远的神，不止在Linux上，Mac和Win上我也都用。
- Office系列软件：除了自带的 Libra Office，还可以选择 WPS Linux版的，M$ Office可以用在线的，还有Google Doc，腾讯文档等等。
- GIMP：我在Mac和Win上也用，一直当成开源的PS用，不过我其实不太会PS也不太会GIMP（捂脸）。

国产软件我们单独说，其余的我真的没有见到Mac/Win上能完成Linux上完不成的任务。

## 国产软件

国产软件（这里特指国内各大互不连网公司的大作）不少是毒瘤一般的存在，喜欢弹窗，扫硬盘等等，所以我的宗旨是能不用就不用。

更大的问题是，国产软件大多只支持Windows，有的支持Mac，支持Linux的很少，所以用起来更加复杂。
虚拟机固然是个不错的解决方案，但是相比之下过于消耗资源，所以我这里介绍的方法就不谈虚拟机了，用虚拟机的话，VirtualBOX或者KVM都不错，前者比较容易上手，后者更加强大。

## 微信

微信是支持网页版的，但是腾讯官方有意的削弱网页版，实际情况是很多账号不能登录网页版。

所以我推荐两个工具：
- [electronic-wechat](https://github.com/geeeeeeeeek/electronic-wechat)：这是把网页版微信封装了一下，优点是和系统结合比较好，缺点是不是所有人都能用。
- [DoChat](https://github.com/huan/docker-wechat) 这个是用Docker版的WINE虚拟Windows环境来运行Win版的微信。优点是功能全，缺点是显示，文件和托盘图标有点小问题。

另，最近得到的消息，不是很准确，有时间的朋友帮我测试下：
为了配合国家的科技自主化战略，微信最近号称开发了原生支持Linux（目前仅仅支持UOS）的版本。但是网友说实际上是网页版微信套壳，是个和[electronic-wechat](https://github.com/geeeeeeeeek/electronic-wechat)差不多的东西，所以腾讯的策略是，只要尝试登录UOS上的微信，就为你的账号解锁网页微信的功能。

## QQ

QQ 其实是有Linux版本的，虽然界面丑爆（简直梦回2008），功能不全，但是胜在干净。缺点还有一个，每次登陆都要你手机扫码，腾讯要确保你安装了手机客户端（这样才能更好的监控你（逃））。

[Linux QQ](https://im.qq.com/linuxqq/index.html)

## QQ，百度云之类的其它软件

和WINE微信思路一致，也可以用[RokasUrbelis/docker-wine-linux](https://github.com/RokasUrbelis/docker-wine-linux)这个项目来使用WINE来跑国内的各大毒瘤软件。


## 可操作性解决方案

主要涉及鼠标特殊按键，快捷键，人脸识别，输入法等等。

### Logitech 鼠标

Logitech 鼠标（其它牌子每试过，应该差不多）有多余的特殊按键，我一般设置为切换应用等等，Linux下我参考了：[How to configure extra buttons in Logitech Mouse](https://askubuntu.com/questions/152297/how-to-configure-extra-buttons-in-logitech-mouse)

根据自己的使用习惯修改即可。

### 人脸识别

用的是[boltgolt/howdy](https://github.com/boltgolt/howdy)，实际使用体验稍显鸡肋。如果不是快速模式，则基本要正脸面对摄像头才能PASS，但是在双屏的时候有点做不到。
其次，至少快速模式可以被照片破解。最后，识别的速度并不快，（可能比我手速还慢一点）所以我虽然安装了，但是最后还是disable掉了。


### 指纹识别

DELL工程师回复的方法在这里：[XPS 13 9300 - Does fingerprint reader work on linux?](https://www.dell.com/community/XPS/XPS-13-9300-Does-fingerprint-reader-work-on-linux/td-p/7514958)，但是我的笔记本的传感器驱动还没有，所以这是我用Linux唯一的痛。

### 触摸板手势

如果问我使用Mac，体验最好的地方是什么，那应该是触摸板强大的功能。Linux下也有相应的解决方案，亲测，如果好好配置，和Mac的不相上下。

我参考了这个帖子：[Touchpad Gestures in Ubuntu 18.04 LTS](https://askubuntu.com/questions/1034624/touchpad-gestures-in-ubuntu-18-04-lts)，我在用的是 [iberianpig/fusuma](https://github.com/iberianpig/fusuma)。

安装方式：

```bash
sudo gpasswd -a $USER input
sudo apt install libinput-tools xdotool ruby
sudo gem install fusuma
```

配置文件位置是：`~/.config/fusuma/config.yml`，需要自己创建，内容参考：

```yaml
swipe:
  3: 
    left: 
      command: 'xdotool key alt+Right'
    right: 
      command: 'xdotool key alt+Left'
    up: 
      command: 'xdotool key super'
    down: 
      command: 'xdotool key super'
  4:
    left: 
      command: 'xdotool key ctrl+alt+Down'
    right: 
      command: 'xdotool key ctrl+alt+Up'
    up: 
      command: 'xdotool key ctrl+alt+Down'
    down: 
      command: 'xdotool key ctrl+alt+Up'
pinch:
  in:
    command: 'xdotool key ctrl+plus'
  out:
     command: 'xdotool key ctrl+minus'

threshold:
  swipe: 0.4
  pinch: 0.4

interval:
  swipe: 0.8
  pinch: 0.1
```

配置好后直接`sudo fusuma`就可以运行了，建议加入启动程序中，比较方便。


### 输入法

只要在语言中安装了汉语以后，就可以添加ibus智能拼音输入法。
对了，记得开启记忆词汇功能和内置的词典，否则输入还是比较痛苦的，有用户数据的可以尝试导入历史数据。

日语输入推荐用Mozc。