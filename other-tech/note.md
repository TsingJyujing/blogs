## 批量杀线程

```
#!/bin/bash
ps -ef|grep $1|grep -v grep|awk '{print $2}'|xargs -r kill -9
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