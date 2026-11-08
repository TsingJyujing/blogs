# 记一个离谱的MySQL语句的性能问题

## 故障现象

我司有一个系统里存在某个SQL，定期会需要把一些数据标记为删除，这个SQL是这样写的：

```sql
-- 注：本文的SQL都进行了脱敏处理，但是绝对不影响理解
UPDATE production_embedding_map
SET deleted = true
WHERE production_id IN (SELECT production_id FROM t_delete_production_ids);
```

Beta环境里测试过了后，就扔到线上去跑了（当时开发的急，只有做功能测试，性能测试则没有做）。
结果有一天，突然告警，说任务超时了，然后就被自动干掉重新执行，但是重试了几十次仍然是失败的。

## 故障重现

看到这个SQL的第一反应就是`IN`写的不好（因为已经确认过，`production_id`字段是有索引的），这个没什么证据，就是SQL写多了的直觉（但是仍然写出了这样的SQL，丢人啊）。

于是我跑到线上去下载了一份生产数据，本地（其实是另一个服务器）用Docker起了一个MySQL8实例，然后把数据导入本地进行测试。

打开一个SQL会话，然后随机抽取一些数据来模拟标记删除的过程：

```sql
create temporary table t_delete_production_ids
(
    production_id INT UNSIGNED
);

insert into t_delete_production_ids (production_id)
select production_id
from (select distinct production_id
      from production) eids
order by RAND()
limit 3000;
```

然后执行该SQL，期待该SQL直接卡死，然而发现完！全！没！问！题！！

多执行了几次发现的确没问题以后，怀疑是MySQL小版本的问题，线上跑的是MySQL 8.0.19而我Docker里面拉的是最新的8.0.30。
使用二分法最小版本进行测试后发现，该问题在8.0.21被修复了。

## 分析与修复

其实问题出在执行计划上，如果用EXPLAIN解释原始的SQL，可以看到8.0.20及以前的执行计划是：

| id | select\_type | table | partitions | type | possible\_keys | key | key\_len | ref | rows | filtered | Extra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | UPDATE | production\_embedding\_map | null | index | null | PRIMARY | 4 | null | 6201234 | 100 | Using where |
| 2 | DEPENDENT SUBQUERY | t\_delete\_production\_ids | null | ALL | null | null | null | null | 2818 | 10 | Using where |

如果更新到8.0.21及以后，哦，它把SUBQUERY的结果物化了，然后就变成了和INNER JOIN（最后的解决方案）一样的执行计划（MATERIALIZED这一步骤的执行成本可忽略）。

| id | select\_type | table | partitions | type | possible\_keys | key | key\_len | ref | rows | filtered | Extra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SIMPLE | &lt;subquery2&gt; | null | ALL | null | null | null | null | null | 100 | Using where |
| 1 | UPDATE | production\_embedding\_map | null | ref | production\_id  | production\_id  | 5 | &lt;subquery2&gt;.production\_id | 44 | 100 | null |
| 2 | MATERIALIZED | t\_delete\_production\_ids | null | ALL | null | null | null | null | 3311 | 100 | null |

可是我们没法升级MySQL的版本，所以只能绕开它，让MySQL生成和新版一样的执行计划。不讨论Optimizer的骚操作，一般SQL如果在IN上遇到瓶颈，最好的办法是换成JOIN，如果换成INNER JOIN，执行计划就是：

```sql
UPDATE production_embedding_map pem
INNER JOIN t_delete_production_ids tdpi ON pem.production_id = tdpi.production_id
SET deleted = true
WHERE tdpi.production_id is not null;
```

| id | select\_type | table | partitions | type | possible\_keys | key | key\_len | ref | rows | filtered | Extra |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | SIMPLE | tdpi | null | ALL | null | null | null | null | 2818 | 90 | Using where |
| 1 | UPDATE | pem | null | ref | production\_id  | production\_id  | 5 | duplicated\_production\_detection.tdpi.production\_id | 46 | 100 | null |

## 所以MySQL到底更新了什么

其实MySQL的更新说来也简单，就是让优化器变得更加聪明一点，会物化子查询了：[Changes in MySQL 8.0.21 (2020-07-13, General Availability) Optimizer Notes](https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-21.html#mysqld-8-0-21-optimizer)

> A single-table UPDATE or DELETE statement that uses a subquery having a [NOT] IN or [NOT] EXISTS predicate can now in many cases make use of a semijoin transformation or subquery materialization.

## 这个故事告诉我们什么

- Beta/测试环境的所有版本最好都和生产做到小版本一致
- 对于赶工的项目不可能逐一确认，但是保险起见，所有的SQL最好都扫一眼执行计划
  - 我觉得更好的方式是封装执行SQL的部分，仅在Beta环境输出Explain的结果
- 不要完全相信Optimizer
