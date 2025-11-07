# 向量稳定化

最近接触到的一篇论文：[Orthogonal Low Rank Embedding Stabilization](https://dl.acm.org/doi/10.1145/3705328.3748141)

## 为什么我们要向量稳定化？

在训练机器学习模型的时候，尤其是推荐系统的模型的时候，有很多的模型会输出User或者Item的Embedding。这些Embedding一般来说很难在下游的任务中使用，其原因是不够稳定。
在训练稍微复杂一点的模型——哪怕只是一个几层的神经网络——我们也不能保证每一次输出的向量都是一样的，因为在Loss函数中我们约束的往往是User和Item求得的Score（内积或者Cosine Similarity之类），然后基于这个内积我能对物品进行正确的排序以保证用户感兴趣的物品在前面。

这篇论文可以通过做简单的线性变换，使这一次训练输出的Embedding和上一次尽可能的接近，并且在这个过程中：

- 不需要修改现在的训练模型，只操作输出的Embedding
- 变换前后User和Item的内积不变

可以说是非常省事的方法了。

## 什么时候能用

你随便弄两个向量矩阵肯定是不行的，这里我个人的思考是：两次模型训练之后的向量空间要有相似性。

举个简单的例子，请各位读者现在想象一下现在脑海中有一个三维的点云，每一个点就代表一个User或者Item。
随后我们有另一个点云，是第一个点云经过旋转镜像之类的操作得到的。如果仅仅从Cosine Similarity或者内积的角度，这两个点云不能说是一模一样吧至少也可以说是风马牛不相及。
但是他们**内在的结构是一样的**小王喜欢键盘鼠标，那么小王的Embedding就是会和3C数码产品很接近，小李喜欢口红化妆水，那么小李就是会和化妆品的Item很近。

其实Loss和数据一样也不能保证每一次学习出来的空间也一样，但是这样的结构一致性给我们机会去变换其中一个空间。


## 具体怎么做？

我们需要做两件事：

1. （低秩的）SVD分解
2. 对齐

### 低秩SVD分解

由于我们用相同或者相似的数据训练出来的模型，所以User和Item的内积矩阵也应该是差不多的（如果你这个模型真的有效的话）。那么他们的SVD分解应该也是差不多的，所以我们做SVD分解。

但是你现在已经手握User和Item的矩阵了，我们注意到两点：

1. 传统的推荐系统模型里面，这个Score矩阵是稀疏的，但是你握着Embedding再去求Score矩阵那就稠密了。
2. 你的User和Item的Embedding的维度都是e，这个e一般不大（32，64，192之类？），SVD做出来秩不会超过你的维度e。

所以我们肯定能找到一个低秩的方法：

首先我们设定如下的变量：

- User Embedding: W 是一个 m x e 矩阵
- Item Embedding: T 是一个 n x e 矩阵

评分矩阵S就可以这样算出： $$S=TW^T$$

我们不要急，先对User和Item的Embedding做一个QR分解：

- $$T=Q_TR_T$$
- $$W=Q_WR_W$$

我们就得到了$$Q_T$$和$$Q_W$$两个正交的向量组，和$$R_T$$与$$R_W$$两个上三角矩阵，别急，等下会有用：

如果一个正常的分解$$\text{SVD}(S)=\text{SVD}(TW^T)=U \Sigma V$$

我们就可以用刚才QR分解的结果去凑SVD分解的结果：

$$\text{SVD}(S)=Q_T R_T (Q_WR_W)^T=Q_T (R_T R_W^T) Q_W^T$$

到这一步就很清晰了，我们只要对中间的小核$$R_TR_W^T$$做SVD就可以了

$$S=Q_T \times SVD(R_TR_W^T) \times Q_W^T=Q_T U_R \Sigma V_R Q_W^T$$


所以我们得出等价的U和V是这样的：

- $$U =Q_TU_R =T R_T^{-1} U_R$$
- $$V^T=Q_W V_R^T=W R_W^{-1} V_R^T$$

我们当然可以把T和W后面的东西拿出来作为变换矩阵$$M_T$$和$$M_W$$，求exe的逆矩阵也不是很麻烦，像这样：

- $$TM_T = U \Sigma^{-1/2}$$
- $$WM_W= V^T\Sigma^{-1/2}$$

我们求得变换矩阵：

- $$M_T=R_T^{-1} U_R \Sigma^{1/2}$$
- $$M_W=R_W^{-1} V_R^T \Sigma^{-1/2}$$


事情还没有完，但是还可以更简单一点：

- 因为 $$R_TR_W^T = U_R \Sigma V_R$$
- 所以 $$R_TR_W^T V_R^T = U_R \Sigma V_R V_R^T$$
- 因为 $$V_R V_R^T = I$$ (SVD的性质)
- 所以 $$R_TR_W^T V_R^T = U_R \Sigma$$
- 所以 $$R_TR_W^T V_R^T = U_R \Sigma$$
- 所以 $$R_W^T V_R^T \Sigma^{-1/2} = R_T^{-1}U_R \Sigma^{1/2}$$
- 得到 $$M_T=R_W^T V_R^T \Sigma^{-1/2}$$

我这里就写了$$M_T$$的计算，$$M_W$$的计算方法是一样的，就不赘述了。

连逆矩阵也不用求了，对角矩阵开个平方就搞定了。

反正最后得到

- $$M_T=R_W^T V_R \Sigma^{-1/2}$$
- $$M_W=R_T^T U_R \Sigma^{-1/2}$$

天才。

### 对齐（Orthogonal Procrustes）

这里比较简单，证明也写在Wiki上了：https://en.wikipedia.org/wiki/Orthogonal_Procrustes_problem

简单来说，就是求一个正交矩阵（变换）$$\Omega$$，使得B和变换过的A尽可能接近。

$$\underset{\Omega}{\text{minimize}}\quad \|\Omega A-B\|_F$$

这个是有解析解的，只要对A和B的Gramian Matrix做SVD分解，脱去中间的特征值对角矩阵$$\Sigma$$以后把U和V乘起来就可以了。

## Spark实战

为什么用Spark举例呢？

虽说SVD或者Orthogonal Procrustes都是numpy和scipy自带的算法，但是在工业中肯定没法直接计算。Embedding一般会存储在某些分布式存储中，比如HDFS，或者某个HIVE表。把两个矩阵下载下来就很费工夫。最好的办法是直接在Spark里面分布式的把计算完成。

认识我的人可能知道我勉强算是个Flink爱好者，但是Spark仍然是大多数公司的数据处理基础，而且这样的批处理任务放在Spark里比Flink中要合适。

实际的代码设计公司内部的系统，我只挑一些核心的算法相关且业务无关的函数来讲讲。

### Low Rank SVD

我们需要两张表（Spark中的DataFrame），一张是User，一张是Item，其中一个列是Embedding(float array)。
这里我们会用到`qr_decompose`函数来求取QR分解的R矩阵，我们稍后会说明。

```python
def low_rank_svd(item_df: DataFrame, item_col: str, user_df: DataFrame, user_col: str) -> Tuple[np.ndarray, np.ndarray]:
    R_T = qr_decompose(item_df, item_col)  # R_T
    R_W = qr_decompose(user_df, user_col)  # R_W
    U_R, s, V_R = np.linalg.svd(R_T @ R_W.T, full_matrices=False)
    # Check if s has any non-positive values
    if np.any(s <= 0):  # matrix is ill-conditioned
        raise ValueError(
            "Singular values contain non-positive values, indicating an ill-conditioned matrix."
        )
    inv_sqrt_diag = np.diag(1 / np.sqrt(s))
    M_T = R_W.T @ V_R.T @ inv_sqrt_diag
    M_W = R_T.T @ U_R @ inv_sqrt_diag
    return M_T, M_W
```

其返回值是Item和User的变换矩阵。

### QR Decompose

其实Spark提供了[QR分解的函数](https://spark.apache.org/docs/3.5.5/api/python/reference/api/pyspark.mllib.linalg.distributed.RowMatrix.html#pyspark.mllib.linalg.distributed.RowMatrix.tallSkinnyQR)，但是我的环境里面运用有BUG。而且原生的函数需要创建相应的Matrix对象，我们这里的算法和Spark的矩阵计算的兼容性并不好——因为我们会需要对齐两个Embedding Matrix，而且对应的ID信息也不能丢。最后结果也要保存到HIVE中。基于以上的理由，最后我们没有选择Spark原生的矩阵计算函数。

`cross_gram_matrix`的作用是求得两个nxe矩阵的Gramian矩阵： $$G = A^T A$$

由于我们只要求取QR分解中的R，所以我们这里采取了另一种简易做法：

考虑到：$$A=QR$$

- Q: 正交向量组
- R: 上三角矩阵

我们轻易能够证明（中间的Q因为是正交矩阵，$$Q^TQ$$变成单位矩阵消掉了）

$$A^TA=(QR)^TQR=R^TQ^TQR=R^TR$$

所以我们只要把$$G = A^T A$$矩阵做一个cholesky分解就可以得到矩阵R了。

```python
def qr_decompose(df: DataFrame, col: str) -> np.ndarray:
    gram_mat = cross_gram_matrix(df, col, col)
    return np.linalg.cholesky(np.array(gram_mat)).T
```

### Cross Gram Matrix

没什么可说的，就是把1xe的行向量v求得$$v^Tv$$并且叠起来就得到了。

```python
# This is a function to calculate matrix multiplication A^T @ B in Spark
def cross_gram_matrix(df: DataFrame, colA: str, colB: str) -> np.ndarray:
    """
    df: DataFrame with columns colA and colB, each containing np.ndarray of shape (e,)
    colA: name of the column for matrix A
    colB: name of the column for matrix B

    Returns:
    A^T @ B as a numpy ndarray of shape (e, e)
    """
    e = len(df.select(colA).first()[0])

    def add_outer_product(rows):
        part_result = np.zeros((e, e))
        for row in rows:
            part_result += np.outer(row[colA], row[colB])
        yield part_result

    def reduce_matrices(mat1, mat2):
        return mat1 + mat2

    return df.rdd.mapPartitions(add_outer_product).reduce(reduce_matrices)
```

### Orthogonal Procrustes

其中，col_to_conv就是上文的A矩阵，一般是这一次训练的结果。而col_base就是B矩阵，一般是上一次训练的结果。

需要注意的是：

- df里面每一行都必须是相同的User或者是Item。
    - 所以我们会做一次Inner Join取公共结果
- 一般我们只用Item做对齐，但是也可以User和Item都用。

```python
def orthogonal_procrustes(df: DataFrame, col_to_conv: str, col_base: str) -> np.ndarray:
    """
    A, B: shape [n, e]
    Returns R (shape [e, e]) s.t. A @ R ≈ B, with R orthogonal.
    """
    svd_core = cross_gram_matrix(df, col_to_conv, col_base)
    U, _, Vt = np.linalg.svd(svd_core, full_matrices=False)
    return U @ Vt
```

### 组合起来

假设我们已经得到了M_T, M_W，也求得了Orthogonal Procrustes的矩阵O，我们就可以得到最终的：

- User变换矩阵：`M_W @ O`
- Item变换矩阵：`M_T @ O`

然后把每一个原始向量乘上我们得到的矩阵就可以了。


### 附：我们用到的Import

```python
from typing import Optional, Tuple

import numpy as np
from pyspark.ml.linalg import DenseVector, Vectors, VectorUDT
from pyspark.sql.dataframe import DataFrame
from pyspark.sql.functions import udf
import pyspark.sql.functions as F
```


## 实战之后的一些经验

### 算法相关

这里有一些主观的东西。

根据我们的经验，SVD至少不会损失性能，但事实上，SVD变换之后的ndcg会更低一些，可能的原因是我们并不是直接使用内积或者Cosine Similarity，而是把它输入到神经网络中作为一个Feature使用。而且大约是因为我们的模型稳定性较好，每次都能习得差不多的空间。

但是处于谨慎考虑，我们没有去掉这一步。

其次，在Orthogonal Procrustes阶段，用全量的数据做对齐效果更好。其原因可能是我们对参与计算的用户做了过滤，确保他们不是不稳定的新用户或者低频用户。

### Coding相关

多写单元测试。

一旦上了Cluster，Spark的程序是出了名的难调试。所以在单元测试里面临时起一个Local的Spark Session，确保你的代码是正确的还是很重要的。
比如这里，我们就可以和Numpy或者Scipy的结果比较，确保我们得到了正确的结果。

当然，上了Spark还有其它的幺蛾子（比如依赖或者PySpark的Memory问题），但是至少单元测试能解决大部分的问题。
