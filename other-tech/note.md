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

Comparing with the lazy, it more like cache the result, maybe can also simply replaced by `lru_cache`.
We have to ensure the return value won't change while using it.


## FFMPEG

### Convert MP4 File to MP3 File

```bash
ffmpeg -i ${MP4_FILE} -vn \
       -acodec libmp3lame -ac 2 -ab 320k -ar 48000 \
        ${MP3_FILE}
```

Replace `-ab {bitrate}` to `-ac 2 -qscale:a 4` to use VBR
