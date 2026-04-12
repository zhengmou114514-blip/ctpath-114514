# CHRONIC 消融实验记录模板

## 1. 运行记录

### 完整模型

- 路径：`models/results/.../log.txt`
- Test MRR：`0.3441`
- Hits@1：`0.2294`
- Hits@3：`0.4489`
- Hits@10：`0.5163`

### 去路径模块

- 命令：

```powershell
cd E:\CTpath-master\models
python learner.py --dataset CHRONIC --rank 800 --valid_freq 2 --max_epochs 20 --learning_rate 0.1 --batch_size 50 --n_hidden 160 --num_walks 1 --walk_len 8 --gpu 0 --cuda cpu --disable_path
```

- 结果填写：
  - Test MRR：
  - Hits@1：
  - Hits@3：
  - Hits@10：

### 去监督对比学习

- 命令：

```powershell
cd E:\CTpath-master\models
python learner.py --dataset CHRONIC --rank 800 --valid_freq 2 --max_epochs 20 --learning_rate 0.1 --batch_size 50 --n_hidden 160 --num_walks 1 --walk_len 8 --gpu 0 --cuda cpu --disable_cl
```

- 结果填写：
  - Test MRR：
  - Hits@1：
  - Hits@3：
  - Hits@10：

## 2. 最终表格

| 模型 | Test MRR | Hits@1 | Hits@3 | Hits@10 |
| --- | ---: | ---: | ---: | ---: |
| CTpath / TKGR-GPRSCL | 0.3441 | 0.2294 | 0.4489 | 0.5163 |
| CTpath w/o Path |  |  |  |  |
| CTpath w/o CL |  |  |  |  |
| RotatE | 0.3180 | 0.1950 | 0.4290 | 0.5101 |
| TransE | 0.2954 | 0.1746 | 0.3700 | 0.5149 |

## 3. 结论模板

若 `w/o Path` 指标下降，可写：

> 去掉路径表示模块后，模型在 MRR 和 Hits@1 指标上出现下降，说明路径信息能够有效补充实体在历史时刻中的结构上下文，对病程演化预测具有正向作用。

若 `w/o CL` 指标下降，可写：

> 去掉监督对比学习后，模型整体排名性能下降，说明监督对比学习有助于约束表示空间，使历史模式相近的样本在嵌入空间中更加聚合，从而提高时序推理性能。
