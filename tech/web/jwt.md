# JWT简介

## JWT是什么

JWT的全称是JSON Web Tokens，简单来说是一种令牌的格式，其令牌的详细内容是编码后的JSON且常用在Web领域的身份校验故称之为JWT。

一般来说，用户先用自己的用户名和密码（OAuth之类的第三方认证我们先暂时略去）送至服务器，服务器给用户发行一个Token。这个Token中包含了必要的信息，如签发人，主题（一般是用户ID），有效时间等等。
以后服务器便不再需要用户名密码，单靠这个Token就可以放心的确认用户的身份。

## JWT解决了什么问题

很多人可能会问， 既然用户已经有了用户名和密码，何必还要多此一举？先生成这个Token再使用，而不是直接使用用户名和密码呢？
就好像[HTTP Basic Authentication](https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication)那样，简单粗暴，靠HTTPS也能保证基本的安全。

主要有两个原因，第一个是安全，第二个是压力。

安全比较好理解，与经常把明文的用户名和密码扔在流量里飞想必，可以带有失效机制的JWT显然更加安全一点。第二个原因我觉得更为主要，那就是压力。我们不妨先考虑一下用户名和密码的鉴权过程是什么样的？

1. 用户发出请求，并且在HTTP请求中带上Base64编码后的用户名和密码。
2. 服务器解码请求，将用户名、密码同数据库中的内容（一般密码部分仅仅是Hash）作比对，返回通过或者不通过。

如果每秒钟只有几个请求，这样的设计当然没有问题，可如果这是一个每秒请求量数万的服务，仅做鉴权校验就会让数据库的压力非常的大。
而且目前相对成熟的数据库往往是单点的（涉及到事务的东西，即使能扩容也要脱一层皮）。

那有没有可能，我们发行一个令牌给用户，以后不要说是本后端服务器的其他副本（Replica）就算是跨服务器，也能进行验证，而且验证的过程不需要数据库？
这样的话，我们的服务器就真正的变成了无状态了，熟悉分布式系统的小伙伴都知道，无状态可太省事儿了。

## JWT的安全性是如何保障的

既然就是Base64编码过的JSON，那么用户自己捏一个骗服务器这就是Token可以吗？

当然——不可以，JWT会进行数字签名，JWT的最后一部分会使用服务器才有的密钥和前两部分的内容一起生成一个数字签名，由于这个密钥只有服务器才有，而且通过内容也很难（此处指几乎不可能）反推出密钥，所以攻击者无法伪造JWT。

## JWT的结构详解

JWT的结构分为三块：

- 头部 Header
- 载荷 Payload
- 签名 Signature


三个部分都是Base64的字符串，用`.`链接起来，一个典型的JWT如下所示：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.cThIIoDvwdueQB468K5xDc5633seEFoqwxjF_xSJyQQ
```

其中头部解码后为：

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

载荷解码后为：
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022
}
```

最后一个部分是二进制，用于校验前两部分之和是否有效。

## 如何使用JWT？

### HTTP Header

理论上，只要你把JWT传输给了服务器，这个事儿就算完了。我看RFC7519也没有规定到底一定要在哪里用JWT。
但是考虑到这是个Token，所以一般的使用方式是将其放在Request Header里：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.cThIIoDvwdueQB468K5xDc5633seEFoqwxjF_xSJyQQ
```

### 以FastAPI为例

我这里用的是python-jose，直接`pip install "python-jose[cryptography]"`即可。也可以使用别的库，看这里就行：https://jwt.io/libraries

出于简洁考虑，我们这里略去FastAPI的框架，只展示核心代码。

首先我们要创建一个Endpoint，来发行用户的Token：

```python
...
from fastapi.security import HTTPBasic, HTTPBasicCredentials

http_basic = HTTPBasic()

def create_jwt_access_token(
    data: Dict[str, Any],
    expires_delta: timedelta,
) -> str:
    """
    Create JWT token from data
    :param data:
    :param expires_delta:
    :return:
    """
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(
        to_encode,
        'jwt_secret', # 需要自行设置，
        algorithm="HS256",# 可以换成别的支持的算法
    )

@app.post("/auth/issue-new-token")
def issue_new_token(
    request: Request,
    db: Session = Depends(get_db), # 根据你的数据库使用情况变化，此处仅供参考
    credentials: HTTPBasicCredentials = Depends(http_basic),
):
    username = basic_authentication(db, credentials) # TODO 这个函数用于同数据库交互，确认用户名是否有效，无效则抛出403异常
    access_token = create_jwt_access_token(
        data={"sub": username}, # 这里放你想要的payload
        expires_delta=timedelta(seconds=1234),# 这里放你要的过期时间
    )
    return {"access_token": access_token, "token_type": "bearer"} # 返回Token
...
```

这样就是一个极简版的JWT生成接口了，需要注意的是，这里既没有RateLimit，也没有针对错误进行处理，更是省略了与数据库交互验证用户名密码的逻辑，还是一个比较粗糙的鉴权校验函数。

那么有了鉴权校验，我们怎么在别的API里面验证JWT呢？

首先提供一个函数：


```python
...

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

http_bearer = HTTPBearer()

def jwt_authentication(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
):
    """
    Verify JWT and return username if it's a valid token
    :param credentials: Authentication token in headers parsed by HTTPBearer
    :return:
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        if credentials.scheme.lower() != "bearer":
            raise credentials_exception
        # 这里也可以做更多的处理和校验
        return jwt.decode(
            credentials.credentials,
            'jwt_secret', # 需要自行设置，
            algorithms=["HS256"],# 可以换成别的支持的算法
        )
    except JWTError:
        raise credentials_exception
...
```

随后在新建接口的时候，将它加入Dependencies中去：

```python
@app.get("/some/api/requires/auth",dependencies=[Depends(jwt_authentication)])
def some_api_requires_auth():
    ...
```

也可以获取其payload作进一步的处理：

```python
@app.get("/some/api/requires/auth")
def some_api_requires_auth(jwt_payload:dict=Depends(jwt_authentication)):
    # 处理 jwt_payload
    ...
```

### 以React为例

（警告：本人是二把刀的前端，蒙古大夫级别的水平，请谨慎服用本段落）

（很抱歉，由于源代码与公司业务纠缠太深，难以拿出来展示，这里仅提供一些思路，我以后争取补上源代码）

由于很多组件都会依赖后端的API，且这些API往往需要JWT，所以一般来说，我们会用Context来管理JWT，以便于跨层传输到其他组件。

在制作`AuthStateContext.Provider`的时候，我这里的思路是：

- 由于用了OAuth，JWT会从后段通过query string传入，这个时候首先检查query string有没有新的JWT Token
  - 如果有，那就提取出来，存到localStorage里面再做计较
  - 如果没有进入下一步
- 检查localStorage里面有没有存入的Token
  - 如果有，检查是否有效
  - 如果没有，或者上一步的结果为无效，则进入下一步
- 新增一个who am I这样的接口，并且用后端接口校验JWT（这一步可选，但是可以增加可靠性）
- 如果所有的校验都通过将JWT当前的状态用Provider传输给其他组件
- 否则跳转到相应的页面提示用户

对于其他组件，用`useContext(AuthStateContext)`即可获取确认有效的Token，一般来说会再包一层函数以便于使用。

## JWT的几个缺陷

JWT还是有几个小缺陷的，在设计系统的时候需要考虑，对于某些系统来说，这些缺陷可能导致JWT不能适用或者需要注意使用方式。

1. JWT一旦签发就难以撤回，这是无状态带来的代价。
2. 考虑到1，往往需要设置有效期，则客户端（或者说前端）需要维护JWT的状态。
3. JWT中的信息是默认不加密的，任何人都可以读取。
4. JWT这样的鉴权方式推荐HTTPS。


## 参考资料

- https://jwt.io/
  - https://datatracker.ietf.org/doc/html/rfc7519
- https://en.wikipedia.org/wiki/JSON_Web_Token
- https://developer.mozilla.org/en-US/docs/Web/HTTP/Authentication