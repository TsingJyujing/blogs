# Linux下使用任天堂手柄的体验

家里确实也是买了Nintendo的Switch，但是买来以后猛猛玩了几个月以后就吃灰至今。

手柄倒是买了不少。之前为了打双人游戏买了一个手柄，大概长这样：

![](/img/2026-08-30-00-48-38.png)

之后发现没有震动，加之也没法和家人玩马里奥游戏，趁着回国在淘宝又买了一对。

这些手柄如今并没有什么用，卖掉又有些可惜，好歹上面有摇杆、各色按钮、陀螺仪和加速度传感器，是个绝好的输入设备，于是乎考虑做点什么。

## 如何连接和配置手柄

### 连接

只要按住上面按钮就会进入配对模式：

![](/img/2026-08-30-00-59-08.png)

按着按钮然后再搜索蓝牙设备就可以把手柄连上去。

### 配置

用的是[AntiMicroX](https://github.com/AntiMicroX/antimicrox)，这是一个有图形界面的配置工具，可以方便的把各个按键映射为鼠标和键盘的操作。

我的系统是Debian13，GNOME(wayland)，安装方式选了flatpak。

按照官网的说明安装即可，安装好以后启动软件即可在GUI配置：

```bash
flatpak run io.github.antimicrox.antimicrox
```

由于我是Wayland不是X11，模拟鼠标和键盘也不如之前那么自由，比较通用的做法是新建一个uinput来模拟一个输入设备。这个时候可能会遇到错误，参照[这个页面](https://github.com/AntiMicroX/antimicrox/wiki/Open-uinput-error)修复即可。

```bash
sudo mkdir -p /etc/udev/rules.d
cd /etc/udev/rules.d
sudo wget https://raw.githubusercontent.com/AntiMicroX/antimicrox/master/other/60-antimicrox-uinput.rules
sudo udevadm control --reload-rules && sudo udevadm trigger
```

配置界面大致如图：

![](/img/2026-08-30-01-19-41.png)

flatpak安装多少还是有点问题，比如：

- 界面没有按照我的系统设定变成暗色主题
- 无法最小化，最大化也有些小问题

之后我可能试试看安装deb，但是我个人对这种方式稍微有些抵触。

## 最终我拿它干了什么

嗯……干了两件事情。

第一件还是打游戏，我在Debian上安装了虚拟机，安装了Windows系统玩小时候玩过的空中攻击（Airstrike）游戏。

我这个人马大哈，魂经常不在身上。硬盘也是摔了好几块，小时候写的代码啥的都没有了，但是这个游戏（连带记录？）都完好的保存下来了。

这里的就单纯是把手柄当成一个键盘用了。

当然也不是不能用重力加速传感器来操作，但是我觉得那反而让我不好操作。

第二件是就是当成遥控板，吃饭的时候我会把电脑接到餐桌边的屏幕上看看B站网飞Youtube什么的。但是操作还得靠电脑有点不便。以后可以合上电脑直接操作手柄了。

## Linux驱动任天堂手柄的基本原理

我也不是Linux驱动开发的专家，所以只是把我调查到信息稍微说个一二。如果有错请联系我。

### AntiMicroX的原理

简单来说，就是把SDL2进行一个封装，SDL是一个C语言写的，跨平台的库，有了它就可以直接用API获取设备或者轮询操作。AntiMicroX用的是C++，但是我搜索了一下，也是有[Python的SDL库](https://github.com/py-sdl/py-sdl2)的，之后考虑可以做些什么玩具玩玩。

所以有了SDL以后可以把跨平台的一些脏活全部丢给它，基于SDL的API去做一些上层的配置。话虽如此，我不是要轻视AntiMicroX的开发。
我清楚界面开发的工作还是极为繁重的，AntiMicroX的界面做的极其简单易懂，特别是摇杆和传感器的部分，直接能看到数据和状态，让我对手柄的理解更加深了（感谢开发者的无私奉献）。

通过SDL获取了手柄的各个数据以后，下一步就是根据配置去输出。我是Wayland，所以这里走的就是uinput的路子。通过 /dev/uinput 模拟出一个一个标准的键鼠输入设备，然后对其发送信号即可。

### SDL2是怎么做的呢？

其它平台我没有深究，我只看了Linux的部分。Linux直接会提供标准的事件设备然后生成/dev/input/eventX文件。SDL直接去读取这些事件即可。SDL还支持别家的手柄，会将所有手柄的数据转为统一的控制指令，刚才说的AntiMicroX的数据就是从这里来的。

### hid-nintendo驱动的原理

令我诧异的是，任天堂的手柄设备的驱动居然[写入了Linux内核](https://github.com/torvalds/linux/blob/master/drivers/hid/hid-nintendo.c)！

我以为像这样的设备多少得是私有的协议所以做成DKMS之类的（类似英伟达）。我觉得这不符合N社的尿性。

后来我查了一些资料，别说DKMS了，任天堂啥也没有提供。不愧是你啊，任天堂。我还是Too young too simple, sometimes naive. 我买的是HORI的手柄，是任家官方认可的设备，肯定是又内部的资料的。我看到资料说有些设备则是完全靠逆向来生产的，我只能说还是有狠人。

所以这个驱动完全是大家通过逆向工程搞出来的产物（感谢大佬们）。

`hid-nintendo`驱动的任务是，将蓝牙发送的HID报文转换为（SDL库需要的）事件。所以驱动的开发就需要完整的报文协议，这个协议毫不意外是私有的。

好在这个世界永远不缺有时间的大神，[dekuNukem/Nintendo_Switch_Reverse_Engineering](https://github.com/dekuNukem/Nintendo_Switch_Reverse_Engineering)上面就有完整的报文协议。里面有很多有意思的细节，比如比如摇杆的精度是12bit，这样XY轴的数据就可以塞到3个Byte里面。

除了解析协议以外，这个驱动还有一些其它任务，比如根据读出的出厂时候的纠偏数据来对传感器进行校正。（可是我觉得这些应该在手柄内完成，难道是为了功耗？）

## 所感

总结一下，从数据的流向看，工作的机制是手柄（蓝牙）-> hid-nintendo报文解析 -> SDL事件读取和标准化 -> AntiMicroX配置按键映射 -> （至少对于Wayland）uinput模拟输入设备。

我只是简单的在我的电脑上敲了几行Bash命令，然后用鼠标点击配置了一下按键映射，就打开我的游戏来玩了。
但是背后是一层又一层的信号传递，是一个个大神破解协议，开发驱动，开发标准库，开发界面。经过了这么多的接力棒，把简单易用的解决方案传到了我的手上。

与任天堂的顽固和封闭相比，我更喜欢开源、开放的这种勃勃生机万物竞发的境界。
