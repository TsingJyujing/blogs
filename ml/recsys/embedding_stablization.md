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

$$\begin{aligned}
   \underset{\Omega}{\text{minimize}}\quad & \|\Omega A-B\|_F
\end{aligned}$$

这个是有解析解的，只要对A和B的Gramian Matrix做SVD分解，脱去中间的特征值对角矩阵$$\Sigma$$以后把U和V乘起来就可以了。

## Spark实战

为什么用Spark举例呢？虽说SVD或者Orthogonal Procrustes都是numpy和scipy自带的算法，但是在工业中肯定没法直接计算。Embedding一般会存储在某些分布式存储中，比如HDFS，或者某个HIVE表。把两个矩阵下载下来就很费工夫。最好的办法是直接在Spark里面分布式的把计算完成。

（写累了，未完待续å）