# 修复Linux磁盘中的坏道

## 前言

我之所以写这篇文章，是因为我最近在尝试修复一台十几年前的老笔记本（电脑的型号是联想的G470）。
我用了一块，大概几年前买的1TB的西部数据的SMR烂磁盘，和我另一台坏电脑上拆下来的2x8G的内存条来修复它。
老马拉破车，修复以后也不会让它跑太重的任务，可能也就跑一些爬虫或者定时任务的脚本，以Stateless的任务为主。再坏掉的话我可能会丢掉这台电脑，毕竟这玩意儿也就比树莓派强一些。

于是乎我在这台老电脑上装了最新的Debian操作系统，配XFCE轻量界面，即使是这样的界面，我也默认关闭了，平时启动只会启动命令行。
这里唯一的问题是这个磁盘，它有一些坏道，一旦操作系统读写到了这些坏道就有可能死机，本着没坏就往死里用的精神，我需要屏蔽这些坏道使用。

**注意**：正常的电脑请不要模仿这里的操作，如果磁盘到寿命了，应该尽快更换新的磁盘（哪怕它还能用）。

关于硬盘相关的内容，请看我以前的文章：[构建家用NAS过程中的碎碎念](https://blog.tsingjyujing.com/other-tech/nas#ying-pan-hdd)

## 方法

先`sudo fdisk -l`一下确认我有哪些硬盘：

```
Disk /dev/sda: 931.51 GiB, 1000204886016 bytes, 1953525168 sectors
Disk model: WDC WD10SPZX-22Z
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 4096 bytes
I/O size (minimum/optimal): 4096 bytes / 4096 bytes
Disklabel type: dos
Disk identifier: 0x826de920

Device     Boot      Start        End    Sectors   Size Id Type
/dev/sda1  *          2048 1920008191 1920006144 915.5G 83 Linux
/dev/sda2       1920010238 1953523711   33513474    16G  f W95 Ext'd (LBA)
/dev/sda5       1920010240 1953523711   33513472    16G 82 Linux swap / Solaris

Partition 2 does not start on physical sector boundary.
```

其中sda1是主分区，sda2是扩展分区，下面包含sda5这个swap逻辑分区。
这里可以看到`Partition 2 does not start on physical sector boundary.`是因为我装debian的时候偷懒，没有手动调整分区而是让安装器自己去分了。


### 进入Rescue模式

这个时候推荐用Debian的安装盘（U盘）启动另一个系统，因为修复坏扇区的时候要求系统盘**不被挂载**。

### 修复主分区

主分区是EXT文件系统，这个时候我们可以用Debian自带的badblocks来扫描坏道（没有的话可以试试安装`sudo apt install e2fsprogs`）:

```shell
sudo badblocks -v /dev/sda1 > badblocks-sda1.txt
```

这个扫描可能运行很久，最好放着跑一晚上。

我稍微数了一下，已经有56个坏道，可见硬盘已经到寿命了，这个电脑上运行的任何东西都需要随时备份，**做好随时崩溃的准备**。


修复SDA1（将坏道标记为不可用）

```shell
sudo e2fsck -l badblocks-sda1.txt /dev/sda1
```

别的系统可以用`fsck`，它本质上是个代理，会调用合适的程序去处理相应的文件系统。

### 查看磁盘健康情况

```shell
sudo apt install smartmontools
```

### 修复SWAP分区

修复SWAP的时候就不需要Rescue模式下了，因为SWAP可以关闭再打开而不会影响系统和运行。

SWAP分区也在同一块硬盘上，自然也会有相应的问题。

1. 首先关闭所有SWAP分区：`sudo swapoff -a`
2. 随后创建新的SWAP分区：`sudo mkswap -c /dev/sda5`
    - 其中参数c的意思是check这个磁盘，跳过有问题的扇区
3. 最后加载回来：`sudo swapon -a`

有的时候如果是外部修改，硬件的UUID可能变化而加载不上，可以试试看`lsblk -f`列出所有的硬件的UUID，然后手动修改`/etc/fstab`

