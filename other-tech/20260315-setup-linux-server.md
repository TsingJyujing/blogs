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


## 安装软件

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
