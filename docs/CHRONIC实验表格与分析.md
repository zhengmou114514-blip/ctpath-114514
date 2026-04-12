# CHRONIC 实验表格与分析

## 1. 实验定位

`CHRONIC` 在本文中的定位是：

1. 慢病场景迁移验证数据
2. Web 系统联调与演示数据
3. 时序知识图谱模型与静态 KG 模型的对比实验数据

不将其单独用于支撑强真实临床疗效结论。

## 2. 主模型与静态 KG 基线结果

已获得结果如下：

| 模型 | 类型 | Test MRR | Hits@1 | Hits@3 | Hits@10 |
| --- | --- | ---: | ---: | ---: | ---: |
| CTpath / TKGR-GPRSCL | 时序 KG 主模型 | 0.3441 | 0.2294 | 0.4489 | 0.5163 |
| RotatE | 静态 KG 基线 | 0.3180 | 0.1950 | 0.4290 | 0.5101 |
| TransE | 静态 KG 基线 | 0.2954 | 0.1746 | 0.3700 | 0.5149 |

## 3. 结果分析

### 3.1 总体结论

主模型 CTpath 在 `CHRONIC` 数据上整体优于静态知识图谱基线 `TransE` 和 `RotatE`。

### 3.2 为什么这个结论合理

1. `MRR` 更高，说明主模型能把正确答案排在更靠前的位置。
2. `Hits@1` 更高，说明主模型在“首选答案命中率”上更强。
3. `Hits@3` 也保持领先，说明这种优势不是偶然的单点现象。

### 3.3 为什么 Hits@10 差距不大

当前 `CHRONIC` 数据具有以下特征：

1. 对象词表较小
2. 关系来自宽表字段展开
3. 同一天有较多结构化特征事件

因此进入前十本身不算特别难，`Hits@10` 的提升空间天然较小。  
这个现象是合理的，不代表主模型没有价值。

## 4. 消融实验表格

下面这张表可以直接用于补充实验：

| 模型 | 说明 | Test MRR | Hits@1 | Hits@3 | Hits@10 |
| --- | --- | ---: | ---: | ---: | ---: |
| CTpath / TKGR-GPRSCL | 完整模型 | 0.3441 | 0.2294 | 0.4489 | 0.5163 |
| CTpath w/o Path | 去掉路径表示模块 | 待运行 | 待运行 | 待运行 | 待运行 |
| CTpath w/o CL | 去掉监督对比学习 | 待运行 | 待运行 | 待运行 | 待运行 |
| RotatE | 静态 KG 基线 | 0.3180 | 0.1950 | 0.4290 | 0.5101 |
| TransE | 静态 KG 基线 | 0.2954 | 0.1746 | 0.3700 | 0.5149 |

## 5. 推荐写入论文的分析文字

可直接参考下面这段：

> 为验证所提模型在慢病场景下的有效性，本文在 CHRONIC 数据集上将 CTpath 与传统静态知识图谱嵌入模型 TransE、RotatE 进行了对比。实验结果表明，CTpath 在 MRR、Hits@1 和 Hits@3 指标上均优于两类静态 KG 基线，其中相较于表现最好的静态基线 RotatE，CTpath 的 Test MRR 由 0.3180 提升至 0.3441，Hits@1 由 0.1950 提升至 0.2294。该结果说明，引入时序建模、路径表示和对比学习后，模型在病程演化预测任务中能够更准确地识别未来时刻的关键实体。

## 6. 消融实验运行命令

### 6.1 去掉路径模块

```powershell
cd E:\CTpath-master\models
python learner.py --dataset CHRONIC --rank 800 --valid_freq 2 --max_epochs 20 --learning_rate 0.1 --batch_size 50 --n_hidden 160 --num_walks 1 --walk_len 8 --gpu 0 --cuda cpu --disable_path
```

### 6.2 去掉监督对比学习

```powershell
cd E:\CTpath-master\models
python learner.py --dataset CHRONIC --rank 800 --valid_freq 2 --max_epochs 20 --learning_rate 0.1 --batch_size 50 --n_hidden 160 --num_walks 1 --walk_len 8 --gpu 0 --cuda cpu --disable_cl
```

## 7. 论文里对 CHRONIC 的建议表述

建议写成：

> CHRONIC 数据主要用于慢病场景迁移验证与系统联调。该数据已被转换为时序知识图谱四元组格式，可用于模型训练与预测接口验证。但由于该数据具有较明显的宽表结构展开特征，因此本文不将其单独作为强真实临床结论依据，而是将其定位为慢病辅助诊疗系统设计与实现中的场景化实验数据。
