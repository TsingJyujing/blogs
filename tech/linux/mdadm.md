# Linux 下利用 `mdadm` 命令设置软件 RAID

## 前言

RAID(Redundant Array of Independent Disk 独立冗余磁盘阵列)，可以用多个小硬盘组成大硬盘，也可以用来容错。
由于机械硬盘的损坏存在相当大的不确定性，而两块硬盘一起损坏的概率不高，所以我们可以用MDADM做一个软件RAID。
手上正好有两块1T的硬盘和一块3T的硬盘（不过都是移动硬盘），全部连接到主机上！

决定给两块1T设置一个软件RAID1，存放一些重要资料，3T的硬盘放一些不是很重要的资料。
其实也可以将2块1T的硬盘设置为RAID0，记作分区A，随后在3T硬盘上分出一个2T的分区，记作分区B，将A和B再组装成RAID1。这样就是2T存放重要资料的空间和1T不重要资料的空间。
不过我手上不重要的视频，电影等等比较多，动漫又全部做了蓝光备份，所以重要资料就是一些数据集和书籍，1T足矣。

这里多说一句，不是很推荐RAID5，重建成功率太低了。

## 设置方式

### 现实支持的分区特性和当前的MD设备

（注：我这里是做好分区以后运行的，所以会有一个MD0的设备）

```
$ cat /proc/mdstat
Personalities : [linear] [multipath] [raid0] [raid1] [raid6] [raid5] [raid4] [raid10]
md0 : active raid1 sdd1[0] sdc1[1]
      976628736 blocks super 1.2 [2/2] [UU]
      bitmap: 0/8 pages [0KB], 65536KB chunk

unused devices: <none>
```

### 对挂好的硬盘分区并且格式化

以对设备sdc操作为例：

```
parted /dev/sdc --script 'print'
parted /dev/sdc --script 'mklabel gpt'
parted /dev/sdc --script 'mkpart primary 0% 100%'
/usr/sbin/mkfs.ext4 /dev/sdc1
```

做好以后使用`lsblk`查看一下分区情况，这里可以看到已经完美的分好了：

```
NAME    MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINT
...
sdc       8:32   0 931.5G  0 disk
└─sdc1    8:33   0 931.5G  0 part
sdd       8:48   0 931.5G  0 disk
└─sdd1    8:49   0 931.5G  0 part
...
```

### 设置RAID
设置很简单，我们就在`sdc1`和`sdd1`上设置了，直接一行命令搞定：

```bash
sudo mdadm --create --verbose /dev/md0 --level=1 --raid-devices=2 /dev/sdc1 /dev/sdd1
```

### 后续处理

首先挂载md0设备到你喜欢的文件夹。

```
mount /dev/md0 /media/md0
```

也要记得将设置写入配置并且更新信息。

```
sudo mdadm --detail --scan | sudo tee -a /etc/mdadm/mdadm.conf
sudo update-initramfs -u
```

### 查看现在的状态

再运行`lsblk`，可以看到，设备已经

```
NAME    MAJ:MIN RM   SIZE RO TYPE  MOUNTPOINT
...
sdc       8:32   0 931.5G  0 disk
└─sdc1    8:33   0 931.5G  0 part
  └─md0   9:0    0 931.4G  0 raid1 /media/md0
sdd       8:48   0 931.5G  0 disk
└─sdd1    8:49   0 931.5G  0 part
  └─md0   9:0    0 931.4G  0 raid1 /media/md0
...
```

### 灾后重建

假设分区损坏了，我们需要恢复，方法记在下面，但是没有试过：

```bash
#（假设sdc1坏了）
# 设置损坏分区
mdadm /dev/md0 --set-faulty /dev/sdc1
# 移除故障分区
mdadm /dev/md0 --remove /dev/sdc1
# 重新准备一个好的SDC
# 添加分区以后应该自动回开始重建
mdadm /dev/md0 --add /dev/sdc1
# 可以通过如下命令查看重建进度
mdadm -D /dev/md0
```

## 后记

软件RAID的性能其实挺感人的，我的移动硬盘支持支持USB3.0，但是因为电脑旧了所以连接了USB2.0，就是这样以前单盘性能应该是40～50Mb/s左右，结果挂上RAID以后写入速度掉到了14Mb/s，稍稍有些过于感人，不过读取速度还行，但是也不能达到理论上单盘的两倍速度。

所以如果对性能有追求的去购买硬件RAID的设备比较好，或者有机箱的人可以考虑一下PCI接口的RAID卡。

从小到大我已经搞坏过好多硬盘了，所以千万记得数据备份，或者做RAID啊！