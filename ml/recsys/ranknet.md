# Learning To Rank 之 RankNet

先记录一下自己的梯度简化推导过程，我自己纸上推了3遍，每次纸丢了就要重新推。
特此记录，省的全尼玛忘了。

## 标准的 RankNet Loss 推导

对于Ranknet，其实是将一个排序问题（比如Top N推荐）演变成一个分类问题。
假设我们已经有一个训练好的评分器，输入User ID和Item ID能给出一个评分，那么，这个评分应该满足越相关（或者用户越喜欢）数值越大。
那么在训练这个评分器的时候，我们假定有i和j两个item，且i更加相关，那么对于分类来说满足：
$$
f(u,i)>f(u,j)  
$$

换个写法：
$$
P(f(u,i)>f(u,j))=1  
$$
对于一般的BCE Loss训练的分类模型，我们有：

对于一般的BCE Loss，我们有：

$$
L_{\omega} = - \sum_{i=1}^{N}{t_i \times log(f_{\omega}(x_i)) + (1-t_i) \times log(1-f_{\omega}(x_i))}
$$

其中：
- $$f_{\omega}(x_i)$$ 是网络的输出，范围应该在0～1之间，最后一般在Linear层后接入一个Sigmoid激活函数来达到这样的效果。
- $$t_i$$ 是优化目标，一般来说 $$t_i\in\{0,1\}$$，但是实际上允许0～1之间的任意实数。

在RankNet中


$$
L_{\omega} = - \sum_{i,j \in S}{t_{ij} \times log(sigmoid(s_i-s_j)) + (1-t_{ij}) \times log(1-sigmoid(s_i-s_j))}
$$

其中：
- $$t_ij$$的取值为：
    - 如果$$s_i>s_j$$，则为1
    - 如果$$s_i<s_j$$，则为0
    - 如果$$s_i=s_j$$，则为0.5
    - PyTorch中可以用 `(torch.sign(si-sj)+1.0)*0.5` 计算得到
- $$s_i$$ 与 $$s_j$$ 分别是项目i和j的输出分数
- 集合S中记录了所有需要计算的i，j对。

## 如果我们强行令$$s_i>s_j$$

如果我们强制$$s_i>s_j$$（如果$$s_i<s_j$$的话就交换，且不计算相等的pair）。
那么我们得到一个简单的Loss：

$$
L_{\omega} = - \sum_{i,j \in S}{log(sigmoid(s_i-s_j))}
$$

### PyTorch的实现

```python
import torch.nn
import torch.nn.functional as F

def ranknet_bce_loss(diff_output: torch.FloatTensor, weight: torch.FloatTensor = None):
    """
    Calculate the loss of rncf with weight, and reduce by mean()
    We assumed that all the output is positive (1)
    :param diff_output: The value of net(x1)-net(x2)
    :param weight: The weight for each sample
    :return: Loss of ranknet
    """
    y_loss = -F.logsigmoid(diff_output)
    if weight is not None:
        return torch.mul(y_loss, weight).mean()
    else:
        return y_loss.mean()
```

## 如果我们采用矩阵计算加速

考虑一下，假设某个用户（或者query）有N个item，如果我们计算除了某个用户的所有的item的分数，那么Loss的计算就如

$$
L_{\omega} = - \sum_{i=1}^{N}{
    \sum_{j=1}^{N}{
        t_{ij} \times log(sigmoid(s_i-s_j))  + 
        (1-t_{ij}) \times log(1-sigmoid(s_i-s_j))
    }
}
$$

注意：原则上来说，只要计算不含对角线的下三角矩阵就可以了，也就是j从i+1开始计算。损失函数应该是对称的。
但是这里为了在numpy或者pytorch等框架下矩阵比循环快，且可读性好出发，所以这里j从1开始计算。

### PyTorch的实现
```python
import torch.nn
import torch.nn.functional as F

def ranknet_loss(
        score_predict: torch.Tensor,
        score_real: torch.Tensor,
):
    """
    Calculate the loss of ranknet without weight
    :param score_predict: 1xN tensor with model output score
    :param score_real: 1xN tensor with real score
    :return: Loss of ranknet
    """
    score_diff = torch.sigmoid(score_predict - score_predict.t())
    tij = (1.0 + torch.sign(score_real - score_real.t())) / 2.0
    loss_mat = tij * torch.log(score_diff) + (1-tij)*torch.log(1-score_diff)
    return loss_mat.sum()
```
## 如果我们直接计算梯度

这一次我们优化到直接计算梯度，对，就连Loss我们也不计算了，直接计算梯度优化。
之所以要计算梯度不是因为少一步能快点，而是我们可以直接针对输出的$$s_i$$这样的评分输出进行优化。
这样优化可以大大减少网络前馈计算的次数，假设每个用户有N个item，那么我们就可以把前馈从$$N^2$$减少到N次。

$$
\frac{\partial{L_{\omega}}}{\partial{\omega}}=
\frac{\partial{L_{\omega}}}{\partial{s_i}}\frac{\partial{s_i}}{\partial{\omega}} + 
\frac{\partial{L_{\omega}}}{\partial{s_j}}\frac{\partial{s_j}}{\partial{\omega}}
$$

这里有两个结果列出，第一个是论文里的结果(sigma先取1好了)：

$$
\frac{\partial{L_{\omega}}}{\partial{\omega}} = 
(\frac{(1-S_{ij})}{2} - \frac{1}{1+e^{s_i-s_j}})(
    \frac{\partial{s_i}}{\partial{\omega}} - 
    \frac{\partial{s_j}}{\partial{\omega}}
)
$$

其中$$t_{ij}$$和$$S_{ij}$$的关系是：$$t_{ij} = \frac{(1+S_{ij})}{2}$$

我个人是使用$$t_{ij}$$推导了一遍，结果是一样的，形式不一样，不相信的可以自己展开看。

$$
\frac{\partial{L_{\omega}}}{\partial{\omega}} = 
(sigmoid(s_i-s_j)-t_{ij})(
    \frac{\partial{s_i}}{\partial{\omega}} - 
    \frac{\partial{s_j}}{\partial{\omega}}
)
$$

这样我们就看到，针对 $$\omega$$ 的Loss的导数其实有两部分，一部分针对项目i，一部分针对项目j的。


不妨把前面的部分叫做$$\lambda_{ij}$$，这也是论文的核心思想的前戏。
先整理一下：
$$
\lambda_{ij}=
\frac{(1-S_{ij})}{2} - \frac{1}{1+e^{s_i-s_j}}=
sigmoid(s_i-s_j)-t_{ij}
$$

我们可以看到，对网络整体的导数可以被分解为对每一个项目的导数。

$$
\lambda_{i}=
\sum_{j: \{i,j\}\in I}{\lambda_{ij}}
- \sum_{j: \{j,i\}\in I}{\lambda_{ij}}
$$

这里的意思是，把所有的$$pair_{ab}$$里面$$a=i$$或者$$b=i$$的挑选出来，如果i在前面，那就取正，否则就取负。
全部加起来以后，就是对这一个分数项的梯度了。



### 最终版本的PyTorch的实现

```python
import torch.nn
import torch.nn.functional as F

def ranknet_grad(
        score_predict: torch.Tensor,
        score_real: torch.Tensor,
) -> torch.Tensor:
    """
    Get loss from one user's score output
    :param score_predict: 1xN tensor with model output score
    :param score_real: 1xN tensor with real score
    :return: Gradient of ranknet
    """
    sigma = 1.0
    score_predict_diff_mat = score_predict - score_predict.t()
    score_real_diff_mat = score_real - score_real.t()
    tij = (1.0 + torch.sign(score_real_diff_mat)) / 2.0
    lambda_ij = torch.sigmoid(sigma * score_predict_diff_mat) - tij
    return lambda_ij.sum(dim=1, keepdim=True) - lambda_ij.t().sum(dim=1, keepdim=True)
```