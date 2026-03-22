# 2026年3月15日 搭建Linux服务器时候的备忘录

修复一台老电脑，使之能勉强使用的时候的一些碎碎念。

## 图形界面和CLI


### 启动的时候不要启动图形界面，而是CLI

```shell
sudo systemctl set-default multi-user.target
```

### 恢复图形界面的使用

```shell
sudo systemctl set-default graphical.target
```

### 手动临时启动图形界面

```shell
sudo systemctl start display-manager
```

或者 `startx` （我没试过）

如果之后要退回CLI但是不想重启的话： `sudo systemctl stop display-manager`

## 合盖时候的行为

`sudo vim /etc/systemd/logind.conf`

其中Lid相关的部分是合盖的操作：

```
#HandleLidSwitch=suspend
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
```


## swap相关设置

### swap file

如果是固态硬盘，推荐不要单独设置SWAP分区，而是使用SWAP File，这样调整起来比较灵活一点。

假设当前电脑内没有任何SWAP分区：

```shell
# 按照你的内存大小去创建即可，一般和内存一样大
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile

# 立刻挂载
sudo swapon /swapfile
sudo swapon --show
```

如果需要启动的时候自动挂载，编辑文件：`sudo vim /etc/fstab`

添加: `/swapfile    none    swap    sw  0   0`

### swapiness设置

一般来说，SWAP的速度总是不如正经内存的，如果过于积极的使用SWAP会降低系统的性能，所以我们把这个数值调整的小一些：

- 查看数值：`cat /proc/sys/vm/swappiness`
- 临时更改：`sudo sysctl vm.swappiness=10`
- 永久设置：`sudo vim /etc/sysctl.conf` 添加：`vm.swappiness=10`


### zram

如果系统的CPU有富余，可以设置zram，就是将一部分内存进行压缩，用CPU换内存空间。

其实Mac也会干这个事情，只是已经默认集成到了系统中不需要设置罢了。


```shell
sudo apt install zram-tools
sudo systemctl enable zramswap
sudo systemctl start zramswap
```

启用以后可以看到：`swapon --show`

```
swapon --show
NAME       TYPE      SIZE   USED PRIO
/swapfile  file       16G 379.3M   -2
/dev/zram0 partition 7.7G 539.8M  100
```

## 安装软件

### 常用软件

```shell

sudo apt install -y \
    tree htop ncdu git vim zsh wget curl \
    keyd keyd-application-mapper \
    ffmpeg pipx ibus-mozc ibus-pinyin \
    build-essential cmake intel-gpu-tools


pipx install "glances[all]"
pipx install ruff
pipx install uv
```

需要把~/.local/bin添加到PATH里面去，我是zsh所以修改~/.zshrc。

### Docker

没什么说的，按照步骤操作就行了：https://docs.docker.com/engine/install/debian/#install-using-the-repository

### Node Exporter

家里别的地方搭了整套的监控系统（Grafana/Prometheus之类的），需要安装Node Exporter。

用Docker Compose是最方便的，但是我希望能不受Docker的影响，所以我选择下载二进制文件安装。

首先下载并且把程序解压到 /usr/local/bin 里面去（或者任意你想要的路径）：https://github.com/prometheus/node_exporter/releases

创建相应的Service文件：`/etc/systemd/system/node_exporter.service`

```ini

[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/node_exporter \
    --collector.logind --collector.processes --collector.systemd --collector.swap

Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```shell
# 加载文件变更
sudo systemctl daemon-reload
# 启动服务
sudo systemctl start node_exporter
# 设置自动启动
sudo systemctl enable node_exporter
```

如果修改了Service文件
```shell
# 加载文件变更
sudo systemctl daemon-reload
# 重新启动服务
sudo systemctl restart node_exporter
```
