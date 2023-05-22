# 备忘录

## 批量杀线程

```
#!/bin/bash
ps -ef|grep $1|grep -v grep|awk '{print $2}'|xargs -r kill -9
```

## MySQL

### 创建用户并且授权读写Schema

```sql
create user ${USERNAME} IDENTIFIED by '${PASSWORD}';
show grants for ${USERNAME};
grant all on ${SCHEMA}.* to ${USERNAME};
flush privileges;
```

## MongoDB 权限配置

### 管理员权限配置

```javascript
db.createUser({user:"root",pwd:"123456",roles: [{ role:"root", db:"admin"}]})
```

### 用户配置样例

```javascript
db.createUser({ 
    user: "someuser",
    pwd: "somepassword",
    roles:[
        { role: "readWrite", db: "somedb" }
    ]
})
```

### 删除用户

```javascript
db.dropUser("username")
```

## MongoDB 慢查询相关

### 查找当前大于10.0秒的、且最慢的一个查询的详情

```bash
mongo --quiet --eval "let limit_time = 10.0;" slow_query.js
```

### 统计大于10秒的慢查数量

```bash
mongo --quiet --eval "db.currentOp().inprog.filter(x=>x['secs_running']>10).length"
```

一般统计大于5秒，15秒，30秒,60秒，300秒的慢查数量。

### 查询Running总时间

这个指标可以从侧面反应数据库的操作体验和压力。

```bash
mongo --quiet --eval "db.currentOp().inprog.map(x=>x.microsecs_running/1000000.0).reduce((a,b)=>a+b)"
```

```javascript
// 检查大于 limit_time 秒的慢查询数据
// let limit_time = 10.0;
// 上一句在eval里面执行来达到动态设置的效果
db.currentOp().inprog.filter(
    x=>x["microsecs_running"]>(limit_time*1000000)
).sort(
    // 取最慢的一条进行展示
    (a,b)=>{
        const va = a["microsecs_running"];
        const vb = b["microsecs_running"];
        if(a==b){
            return 0;
        }else{
            if(a>b){
                return -1;
            }else{
                return 1;
            }
        }
    }
)
```

### 杀死超时任务

```javascript
let over_time = 60.0;// Over 1 min
db.currentOp().inprog.forEach(
    opInfo=>{
        try{
            const opId = opInfo["opid"];
            const opDuration = opInfo["secs_running"];
            if(opDuration>over_time){
                db.killOp(opId);
                console.log(`Operation ${opId} killed, details: ${JSON.stringify(opInfo)}`)
            }
        }catch(err){
            console.error("Error while executing killing filter.")
            console.error(err)
        }
    }
)
```

## Python Tricks

### Lazy Evaluation

From the blog [Python 延迟初始化（lazy property）](https://segmentfault.com/a/1190000005818249)

```python
class lazy(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, cls):
        val = self.func(instance)
        setattr(instance, self.func.__name__, val)
        return val

def lazy_property(func):
    attr_name = "_lazy_" + func.__name__

    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return _lazy_property
```

Comparing with the lazy, it more like cache the result, maybe can also simply replaced by `lru_cache`. We have to ensure the return value won't change while using it.

### Example of Async wait

```python
import asyncio
from asyncio import Future
from typing import Dict

futures: Dict[str, Future] = {}


@app.get("/test/lock/{task_id}")
async def test_lock(task_id: str):
    result = asyncio.get_event_loop().create_future()
    # Put the task in Queue
    futures[task_id] = result
    return {
        "result": await result
    }


@app.get("/test/release/{task_id}")
async def test_release(task_id: str):
    if task_id not in futures:
        raise Exception("Task not found")
    # Set result while the task finished
    futures[task_id].set_result(f"{task_id} is done")
    return {
        "task": task_id
    }
```

## FFMPEG

### Convert MP4 File to MP3 File

```bash
ffmpeg -i ${MP4_FILE} -vn \
       -acodec libmp3lame -ac 2 -ab 320k -ar 48000 \
        ${MP3_FILE}
```

Replace `-ab {bitrate}` to `-ac 2 -qscale:a 4` to use VBR

### Convert to H264 mp4 file

```bash
ffmpeg -vcodec h264 -acodec copy -movflags +faststart -pix_fmt yuv420p -crf 23 -i input.mp4 output.mp4
```

### Merge subtitle (srt) file and video

```bash
ffmpeg -i ${INPUT_VIDEO} -f srt -i ${SUBTITLE_FILE} -c:v copy -c:a copy -c:s srt ${OUTPUT_VIDEO}
# -c:s can also be copy
```

## 树莓派

### RPI3 Ubuntu 摄像头

1. 只能使用32位的系统
2. 在`/boot/firmware/config.txt`里增加`start_x=1`
3. 执行 `sudo snap install picamera-streaming-demo`以后重启系统
4. 打开 http://:8000/ 即可查看

参考资料：

* [Enable Raspberry Pi Camera in Ubuntu 20.04 MATE on Raspberry Pi 4 8GB RAM](https://www.youtube.com/watch?v=CakU8hIaP7c)
* [https://github.com/ogra1/picamera-streaming-demo](https://github.com/ogra1/picamera-streaming-demo)

### RPI3 Wifi

1. Edit `/etc/netplan/xxxxxx.yaml`:

```yaml
# This file is generated from information provided by
# the datasource.  Changes to it will not persist across an instance.
# To disable cloud-init's network configuration capabilities, write a file
# /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg with the following:
# network: {config: disabled}
network:
    version: 2
    ethernets:
        eth0:
            optional: true
            dhcp4: true
    # add wifi setup information here ...
    wifis:
        wlan0:
            optional: true
            access-points:
                "YOUR-SSID-NAME":
                    password: "YOUR-NETWORK-PASSWORD"
            dhcp4: true
```

```bash
sudo netplan --debug try 
# (continue even if there are errors)
sudo netplan --debug generate 
# (provides more details in case of issues with the previous command)
sudo netplan --debug apply 
# (if no issues during the previous commands)
```

Reference: [How to setup the Raspberry Pi 3 onboard WiFi for Ubuntu Server 18.04 with netplan?](https://raspberrypi.stackexchange.com/questions/98598/how-to-setup-the-raspberry-pi-3-onboard-wifi-for-ubuntu-server-18-04-with-netpla)

## Encryption

### SAML2 key/pem generator

```bash
openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:2048 -keyout encryption.key -out encryption.pem
openssl req -x509 -sha256 -nodes -days 3650 -newkey rsa:2048 -keyout signing.key -out signing.pem
```

## K8S

### 创建一个管理员账户的配置文件

首先创建一个Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: <Account Name>
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-user
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: <Account Name>
  namespace: default
```

获取账户详情 `kubectl describe serviceaccount <Account Name>`

随后获取secret的名字，格式一般是 `<Account Name>-token-<随机字符串>`

最后获取Token：

```bash
kubectl describe secret <Token Secret Name>
```

```yaml
apiVersion: v1
kind: Config
users:
- name: <Account Name>
  user:
    token: "<TOKEN>"
clusters:
- name: <Cluster Name>
  cluster:
    api-version: v1
    server: <API ENDPOINT>
contexts:
- name: <Cluster Name>
  context:
    cluster: <Cluster Name>
    user: <Account Name>
current-context: <Cluster Name>
```

## Java/Scala/Kotlin

### Maven Settings

Mainly `~/.m2/settings.xml`.

```markup
<?xml version="1.0" encoding="UTF-8"?>
<settings xmlns="http://maven.apache.org/SETTINGS/1.1.0"
  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
  xsi:schemaLocation="http://maven.apache.org/SETTINGS/1.1.0 http://maven.apache.org/xsd/settings-1.1.0.xsd">

  <servers>
    <server>
      <id>nexus-snapshots</id>
      <username>{username}</username>
      <password>{password}</password>
    </server>
    <server>
      <id>nexus-releases</id>
      <username>{username}</username>
      <password>{password}</password>
    </server>
  </servers>

  <mirrors>
    <mirror>
      <id>central</id>
      <name>central</name>
      <url>https://nexus.xxxx.com/repository/maven/</url>
      <mirrorOf>*</mirrorOf>
    </mirror>
  </mirrors>

</settings>
```

## Glances

### 屏蔽多余的设备

在使用snap的时候经常会有一些奇怪的设备，包括`loop{x}`或者是`/snap/`之类的，这个时候只要在配置文件里加上

```
[fs]
hide=/boot.*,/snap.*
[diskio]
hide=loop.*
[network]
hide=docker.*,lo,veth.*
```

就可以屏蔽这些设备。

官方文档：

1. https://glances.readthedocs.io/en/latest/aoa/diskio.html
2. https://glances.readthedocs.io/en/latest/aoa/fs.html
3. 配置文件的位置 https://glances.readthedocs.io/en/latest/config.html