# 家用Airflow搭建指南

## 前言

本文会介绍一种使用Docker Compose + Git + S3启动一个完全可用的Airflow的方法和过程中踩的坑。

首先说说为什么需要在家里搭Airflow，正常好人家里是不需要Airflow的，但是我最近遇到了一些需要管理的定时任务。

所谓管理，也就是任务的定时启动、手动启动、历史日志（以及任务的状态）的管理和并发控制。

其中最痛的当属并发控制了。比如：

- 从IBKR下载数据的时候最多使用32个Client ID
- 使用yfinance下载数据的时候最多单线程，多线程就容易报429（Too Many Requests）的错误
- 迁移数据库表结构的时候最多只能有一个实例运行，否则容易乱套
- ……

我以前是怎么做的呢？
定时任务用crontab，手动启动那就直接执行，每次启动自动用日期创建日志文件，历史日志则写了个脚本定期删除过期日志。
并发控制都是采用文件锁的方式完成这些任务的，写脚本费心费力不说，而且也不好管理。

我很早就知道Airflow，工作中也一直在用，那么为什么我的HomeLab不用Airflow呢？

当然是因为Airflow的配置本身也很难顶，特别是工作中的时候我们用的是K8S，更增加了部署的难度，给我留下了深刻的心理阴影。
这也就是为什么我前面说：“正常好人家里是不需要Airflow的”。

但是随着手动+脚本管理任务的难度逐渐高于配置Airflow的痛苦程度，我最终还是选择了Airflow。

## 最终成品

首先给出最终成品，你拿着这个脚本就可以自己运行了。

```yaml
x-airflow-common-env: &airflow-common-env
  AIRFLOW__CORE__EXECUTOR: LocalExecutor
  AIRFLOW__CORE__AUTH_MANAGER: "airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"
  AIRFLOW__API__AUTH_BACKENDS: airflow.api.auth.backend.basic_auth
  AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://${AIRFLOW_DB_USERNAME:-airflow}:${AIRFLOW_DB_PASSWORD:-airflow}@postgres/airflow
  AIRFLOW__CORE__LOAD_EXAMPLES: "false"
  AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "true"
  AIRFLOW__DAG_PROCESSOR__REFRESH_INTERVAL: "10"
  AIRFLOW__DAG_PROCESSOR__MIN_FILE_PROCESS_INTERVAL: "10"
  AIRFLOW__CORE__MIN_SERIALIZED_DAG_UPDATE_INTERVAL: "10"
  _AIRFLOW_DB_MIGRATE: "true"
  _AIRFLOW_WWW_USER_CREATE: "true"
  _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
  _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
  AIRFLOW__WEBSERVER__EXPOSE_CONFIG: "true"
  AIRFLOW__API_AUTH__JWT_SECRET: ${AIRFLOW__API_AUTH__JWT_SECRET:-airflow_jwt_secret}
  AIRFLOW__API_AUTH__JWT_ISSUER: ${AIRFLOW__API_AUTH__JWT_ISSUER:-airflow}
  AIRFLOW__API__BASE_URL: https://airflow.your-domain.com
  AIRFLOW__LOGGING__REMOTE_LOGGING: "true"
  AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER: s3://airflow/logs
  AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID: "airflow_log"
  AIRFLOW_CONN_AIRFLOW_LOG: ${AIRFLOW_LOG_CONN}
  AIRFLOW__CORE__FERNET_KEY: ${AIRFLOW__CORE__FERNET_KEY}

services:
  postgres:
    image: postgres:17
    container_name: airflow-postgres
    environment:
      POSTGRES_USER: ${AIRFLOW_DB_USERNAME:-airflow}
      POSTGRES_PASSWORD: ${AIRFLOW_DB_PASSWORD:-airflow}
      POSTGRES_DB: airflow
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 10s
      retries: 5
      start_period: 5s
    restart: unless-stopped
    # ports:
    #   - 15432:5432 # For debugging only

  airflow-init:
    image: apache/airflow:${AIRFLOW_IMAGE_TAG:-3.2.2-python3.13}
    container_name: airflow-init
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      <<: *airflow-common-env
      AIRFLOW__CORE__EXECUTOR: LocalExecutor
      AIRFLOW__CORE__AUTH_MANAGER: "airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager"
      AIRFLOW__API__AUTH_BACKENDS: airflow.api.auth.backend.basic_auth
      AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://${AIRFLOW_DB_USERNAME:-airflow}:${AIRFLOW_DB_PASSWORD:-airflow}@postgres/airflow
      AIRFLOW__CORE__LOAD_EXAMPLES: "false"
      AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION: "true"
      AIRFLOW__SCHEDULER__DAG_DIR_LIST_INTERVAL: "10"
      _AIRFLOW_DB_MIGRATE: "true"
      _AIRFLOW_WWW_USER_CREATE: "true"
      _AIRFLOW_WWW_USER_USERNAME: ${_AIRFLOW_WWW_USER_USERNAME:-airflow}
      _AIRFLOW_WWW_USER_PASSWORD: ${_AIRFLOW_WWW_USER_PASSWORD:-airflow}
    volumes:
      - ./data/dags:/opt/airflow/dags
      - ./data/logs:/opt/airflow/logs
      - ./data/plugins:/opt/airflow/plugins
    user: "${AIRFLOW_UID:-50000}:0"
    command: version

  airflow-apiserver:
    image: apache/airflow:${AIRFLOW_IMAGE_TAG:-3.2.2-python3.13}
    container_name: airflow-apiserver
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    environment:
      <<: *airflow-common-env
    volumes:
      - ./data/dags:/opt/airflow/dags
      - ./data/logs:/opt/airflow/logs
      - ./data/plugins:/opt/airflow/plugins
    ports:
      - "8080:8080"
    user: "${AIRFLOW_UID:-50000}:0"
    command: api-server
    restart: unless-stopped
    healthcheck:
      test:
        ["CMD", "curl", "--fail", "http://localhost:8080/api/v2/monitor/health"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 30s

  airflow-scheduler:
    image: apache/airflow:${AIRFLOW_IMAGE_TAG:-3.2.2-python3.13}
    container_name: airflow-scheduler
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    environment:
      <<: *airflow-common-env
      AIRFLOW__CORE__PARALLELISM: "16"
      AIRFLOW__CORE__MAX_ACTIVE_TASKS_PER_DAG: "8"
      AIRFLOW__CORE__MAX_ACTIVE_RUNS_PER_DAG: "4"
      AIRFLOW__SCHEDULER__MAX_TIS_PER_QUERY: "16"
    volumes:
      - ./data/dags:/opt/airflow/dags
      - ./data/logs:/opt/airflow/logs
      - ./data/plugins:/opt/airflow/plugins
      - /var/run/docker.sock:/var/run/docker.sock
    group_add:
      - "${DOCKER_GID}"
    user: "${AIRFLOW_UID:-50000}:0"
    command: scheduler
    restart: unless-stopped

  git-sync:
    image: registry.k8s.io/git-sync/git-sync:v4.7.0
    environment:
      GITSYNC_ADD_USER: "true"
      GITSYNC_GROUP_WRITE: "true"
      GITSYNC_REPO: "ssh://git@git.tsingjyujing.com:10022/homelab/airflow-dags.git"
      GITSYNC_BRANCH: "master"
      GITSYNC_ROOT: "/git"
      GITSYNC_LINK: "repo"
      GITSYNC_PERIOD: "30s"
      GITSYNC_DEPTH: "1"
      GITSYNC_SSH: "true"
      GITSYNC_SSH_KEY_FILE: "/etc/git-secret/ssh"
      GITSYNC_KNOWN_HOSTS: "true"
      GITSYNC_SSH_KNOWN_HOSTS_FILE: "/etc/git-secret/known_hosts"
    user: "${AIRFLOW_UID:-50000}:0"
    volumes:
      - ./data/dags:/git:rw
      - ./git-secret/id_airflow_ed25519:/etc/git-secret/ssh:ro
      - ./git-secret/known_hosts:/etc/git-secret/known_hosts:ro
    restart: unless-stopped

  airflow-dag-processor:
    image: apache/airflow:${AIRFLOW_IMAGE_TAG:-3.2.2-python3.13}
    container_name: airflow-dag-processor
    depends_on:
      airflow-init:
        condition: service_completed_successfully
    environment:
      <<: *airflow-common-env
    volumes:
      - ./data/dags:/opt/airflow/dags
      - ./data/logs:/opt/airflow/logs
      - ./data/plugins:/opt/airflow/plugins
    user: "${AIRFLOW_UID:-50000}:0"
    command: dag-processor
    restart: unless-stopped
```

配合.env文件：

```bash
AIRFLOW_UID=1000
AIRFLOW_IMAGE_TAG=3.2.2-python3.13
AIRFLOW_DB_USERNAME=airflow
AIRFLOW_DB_PASSWORD=your-db-password
AIRFLOW__CORE__FERNET_KEY=your-fernet-key
AIRFLOW_LOG_CONN='{"conn_type":"aws","login":"your-access-key","password":"your-secret-key","extra":{"endpoint_url":"http://your-endpoint:your-port"}}'
_AIRFLOW_WWW_USER_USERNAME=your-airflow-username
_AIRFLOW_WWW_USER_PASSWORD=your-airflow-password
AIRFLOW__API_AUTH__JWT_SECRET=your-jwt-secret
AIRFLOW__API_AUTH__JWT_ISSUER=airflow
DOCKER_GID=989
```

## 踩过的坑

### API Base URL

这个不设置好，跳转的时候会有问题：

```yaml
AIRFLOW__API__BASE_URL: https://airflow.your-domain.com
```

按照道理我应该放到.env中去设置，但是我太懒了，所以请将就一下。

### 文件系统权限问题

相信你已经注意到配置中的 `user: "${AIRFLOW_UID:-50000}:0"` 了，这里的AIRFLOW_UID不是乱设置的，和你现在宿主机系统的当前用户（最好非Root）保持一致。
这样做的话，本机用非Root用户身份直接可以编辑Airflow里面的文件，其次，和git-sync的文件权限也保持一致还可以防止某个Container读写不了另一个Container的文件。

推荐运行`echo -e "AIRFLOW_UID=$(id -u)"`并且将输出复制到.env文件。

还需要获取DOCKER_GID：`getent group docker | cut -d: -f3`，你会得到一个数字，把它设置为你的DOCKER_GID去。不这么设置git-sync就会遇到权限不足的问题。

### git-sync的SSH Key问题

我们这里的方案是使用Git Repo管理所有的Airflow DAG，git sync的方式是给一个deploy key。无论GitHub还是我用的Gogs都支持这个功能。

生成密钥的方式如下：

```shell
mkdir -p git-secret
ssh-keygen -t ed25519 \
  -C "e.x. your email address" \
  -f git-secret/id_airflow_ed25519
```

随后把Public Key添加到Git中去。

生成known_hosts文件防止连接的时候需要手动确认：

```shell
ssh-keyscan github.com | grep -v '^#' > git-secret/known_hosts
```

权限设置

```shell
sudo chown 50000:0 git-secret/id_airflow_ed25519
sudo chmod 600 git-secret/id_airflow_ed25519
chmod 644 git-secret/known_hosts
```

然后你就可以用下列命令验证是不是好用：

```shell
GIT_SSH_COMMAND="ssh -i git-secret/id_airflow_ed25519 -p 22 -o UserKnownHostsFile=git-secret/known_hosts" git ls-remote ssh://git@github.com/your-org/your-repo.git
```

我在实测的时候遇到一个问题，Deploy Key添加了但是命令不生效，这个时候用SSH Config的方式Clone Repo一次，再测就通了。

```
Host github.com
    HostName github.com
    User git
    PreferredAuthentications publickey
    Compression yes
    IdentityFile /your/private-key/path
```

而且一定要启用新的shell（有空我确认一下这里到底是怎么回事）。

### 在Airflow内使用Docker

由于我们使用LocalExecutor执行代码，所以负责连接Docker的是Scheduler Node。

我们只需要在Scheduler Node上挂载如下的Volume即可: `/var/run/docker.sock:/var/run/docker.sock`

之后我也考虑在内网使用TCP管理多个Docker节点，这样可以部署负载到多个机器上。

### 使用S3存储日志

你首先要准备一个JSON配置，必须是一行，可以用这个命令压缩：`cat your-file.json | jq -c .`

```json
{"conn_type":"aws","login":"your-access-key","password":"your-secret-key","extra":{"endpoint_url":"http://your-endpoint:your-port"}}
```

随后配置 `.env`：

```bash
AIRFLOW_LOG_CONN='{"conn_type":"aws","login":"your-access-key","password":"your-secret-key","extra":{"endpoint_url":"http://your-endpoint:your-port"}}'
```

最后，通过以下设置启用远程日志。

```yaml
AIRFLOW_CONN_AIRFLOW_LOG: ${AIRFLOW_LOG_CONN}
AIRFLOW__LOGGING__REMOTE_LOGGING: "true"
AIRFLOW__LOGGING__REMOTE_BASE_LOG_FOLDER: s3://airflow/logs
AIRFLOW__LOGGING__REMOTE_LOG_CONN_ID: "airflow_log"
```

### 踩过坑又忘了的FERNET

一定要设置AIRFLOW__CORE__FERNET_KEY，这个Key会用来加密所有的敏感信息，比如Variable或者Connection之类的。

如果不设置，重启之后就无法读取之前设置的Variable或者Connection，而且API也会返回500。

实在忘记了就得把数据库的端口透出来，连上去以后删除connection和variable表里所有的数据才行。

生成一个随机FERNET Key的方式为：

```bash
docker compose exec airflow-scheduler python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

当然你也可以直接执行里面的Python代码。

### JWT 设置

JWT虽说不设置也行，但是如果每次都使用Airflow自己随机创建的JWT密钥的话，每次重启后之前的登录就会失效。

设置这两个环境变量即可：

- `AIRFLOW__API_AUTH__JWT_SECRET`
- `AIRFLOW__API_AUTH__JWT_ISSUER`

### 一定要添加DAG Processor

Airflow 3如果不设置DAG Processor的话就不会自动加载DAG的变化。

手动重新加载DAG的代码如下： `docker compose exec airflow-scheduler airflow dags reserialize`

## 技术选型和思考

### 为什么使用Local Executor

所谓[LocalExecutor](https://airflow.apache.org/docs/apache-airflow/3.2.2/core-concepts/executor/local.html)就是在Scheduler Node上直接执行。

其实多个Worker才是Airflow并发的杀器，但是考虑到我的任务并发不大，而且大多数时候是连接Docker去执行代码，本身的负载并不大，所以Local的完全够用，还能节约资源。

### 为什么选择S3存储日志

可以看到，我这里用的是另一个S3而没有在本地启动RustFS或者Minio。

其原因是我有一个NAS，NAS用来存储文件比我的电脑要牢靠一些（我设置了RAID以避免突发的硬盘损坏）。

NAS当然也可以运行Docker，但是硬件有局限，不适合运行一些太重的任务。所以最终的选择是NAS运行数据库（当然我因为别的原因，数据库没有放在NAS上），Git（我用的是Gogs）和S3服务器这种需要可靠存储数据的服务，而服务器（是一台旧电脑）的任务则尽可能的保持无状态。

### 为什么是PostgreSQL

简单来说，Airflow需要的数据库并不大（至少我的数据库如此）。理论上MySQL也不是不能胜任，但是两者的启动内存其实差不多，CPU也用不了多少。
在性能更优的情况下，PostgreSQL并没有占用更多的资源，那么我肯定选择PostgreSQL了。

虽然我没有真正地去横向比较过MySQL和PostgreSQL的性能，但是以我的使用经验来看，任何MySQL的服务如果遇到了数据、计算的问题，切换到PostgreSQL可以解决掉90%（暴论）。

其次，PostgreSQL提供真正的数据库，数据库里是带schema的，权限控制也更细致。这么一比MySQL就好像个残废了。当然，Airflow并没有用到PostgreSQL和MySQL有差异的这部分功能（毕竟还是要考虑兼容性）。

至于为什么不是SQLite，其实SQLite本身是非常牢靠的，但是仅限于单进程的场景。而Airflow至少要部署API Server，Scheduler等等服务，通过挂载文件夹共享的方式来共同使用总让人觉得不是很牢靠。如果Airflow能通过配置在一个容器中同时启动API Server，Scheduler等等，我可能会选择SQLite。

### 为什么不用K8S

这个问题有些可笑，问为什么不在家用K8S部署Airflow仿佛是在问自己为什么吃的苦不够多。

但是正好借着这个机会说一下家庭部署服务的事情，很多人的Home Lab上了K8S（或者K3S吧），然后配合ArgoCD自动部署（完全就是企业级的那一套）。其实大多数人用不到企业级需要的那些功能，反而因为K8S增加了负担。

K8S在设计上就比较适合跑无状态的服务——你有N个无状态的POD，需要规模化部署和管理，自动管理网络，那么K8S非常合适。但是很少有人的Home Lab要扛高负荷的。大部分的需求是相册、音乐、博客、笔记等等，抛开其中有状态的那个数据库不谈，基本没有几个QPS，所以K8S就是杀鸡用牛刀了。

相反，如果真的有高流量访问的需求，比起家庭网络，部署到云上是更好的选择。

当然了，是否上云可以参考这篇文章：[为什么我劝你不要使用云计算？](./cloud-or-not.md)

## 本文的局限性

我虽然以前在K8S部署过Airflow 2，但是时隔多年已经忘了一部分，加上这是我第一次用Docker部署Airflow 3，所以很多配置都不一定是最优的，可能会有历史的痕迹。

其次，我放在airflow-common-env中的那些未必是全局都需要的变量，只是我太懒了，懒得去逐一分辨哪些是公共的，哪些是某些Container特有的。

而且，这个Airflow只有我一个人使用，所以很多配置从简了，比如没有配置OIDC Login，比如从GitHub或者Google登录。

如果你发现文章有任何让你不爽之处，欢迎给我提PR修改这篇文章。
