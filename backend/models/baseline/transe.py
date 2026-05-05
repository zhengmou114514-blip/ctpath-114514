"""
TransE模型实现 - 静态知识图谱基线模型

TransE是知识图谱嵌入的经典方法，将关系建模为从头实体到尾实体的翻译操作。
对于三元组(h, r, t)，TransE假设 h + r ≈ t

参考论文: Bordes et al., "Translating Embeddings for Modeling Multi-relational Data", NIPS 2013
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, List
import numpy as np


class TransE(nn.Module):
    """
    TransE模型实现

    对于三元组(h, r, t)，得分函数为：
    score(h, r, t) = -||h + r - t||

    使用L1或L2范数
    """

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 200,
        norm: str = 'L1',
        margin: float = 1.0,
        is_cuda: bool = False
    ):
        """
        初始化TransE模型

        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            embedding_dim: 嵌入维度
            norm: 范数类型，'L1'或'L2'
            margin: margin-based loss的边界值
            is_cuda: 是否使用GPU
        """
        super(TransE, self).__init__()

        self.model_name = "TransE"
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        self.norm = norm
        self.margin = margin
        self.is_cuda = is_cuda

        # 实体嵌入
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        # 关系嵌入
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim)

        # 初始化参数
        self._init_embeddings()

    def _init_embeddings(self):
        """使用Xavier均匀分布初始化嵌入"""
        nn.init.xavier_uniform_(self.entity_embeddings.weight.data)
        nn.init.xavier_uniform_(self.relation_embeddings.weight.data)

        # 归一化实体嵌入
        self.entity_embeddings.weight.data = F.normalize(
            self.entity_embeddings.weight.data, p=2, dim=1
        )

    def forward(self, batch: torch.LongTensor) -> torch.Tensor:
        """
        前向传播，计算三元组的得分

        Args:
            batch: 形状为(batch_size, 3)的张量，每行为(h, r, t)

        Returns:
            scores: 形状为(batch_size,)的得分张量
        """
        h = self.entity_embeddings(batch[:, 0])  # (batch_size, dim)
        r = self.relation_embeddings(batch[:, 1])  # (batch_size, dim)
        t = self.entity_embeddings(batch[:, 2])  # (batch_size, dim)

        # 计算h + r - t
        if self.norm == 'L1':
            scores = -torch.norm(h + r - t, p=1, dim=1)
        else:  # L2
            scores = -torch.norm(h + r - t, p=2, dim=1)

        return scores

    def predict(
        self,
        batch: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测所有候选实体的得分（用于评估）

        Args:
            batch: 形状为(batch_size, 3)的张量，每行为(h, r, t)
            filters: 过滤字典，用于过滤已知正确答案

        Returns:
            scores: 形状为(batch_size, num_entities)的得分矩阵
            targets: 形状为(batch_size, 1)的目标得分
        """
        with torch.no_grad():
            h = self.entity_embeddings(batch[:, 0])  # (batch_size, dim)
            r = self.relation_embeddings(batch[:, 1])  # (batch_size, dim)
            t = self.entity_embeddings(batch[:, 2])  # (batch_size, dim)

            # 计算所有候选实体的得分
            # score(h, r, t') = -||h + r - t'||
            all_entities = self.entity_embeddings.weight  # (num_entities, dim)

            # 扩展维度以便广播
            h_r = h + r  # (batch_size, dim)
            h_r = h_r.unsqueeze(1)  # (batch_size, 1, dim)
            all_entities = all_entities.unsqueeze(0)  # (1, num_entities, dim)

            # 计算距离
            if self.norm == 'L1':
                scores = -torch.norm(h_r - all_entities, p=1, dim=2)  # (batch_size, num_entities)
            else:
                scores = -torch.norm(h_r - all_entities, p=2, dim=2)

            # 获取目标实体的得分
            targets = []
            for i, (score, target_idx) in enumerate(zip(scores, batch[:, 2])):
                targets.append(score[target_idx].item())
            targets = torch.tensor(targets).view(-1, 1)
            if self.is_cuda:
                targets = targets.cuda()

            # 过滤已知正确答案
            if filters is not None:
                for i, query in enumerate(batch):
                    # 对于尾实体预测，过滤(h, r, ?)的所有已知答案
                    filter_out = filters.get(
                        (query[0].item(), query[1].item(), query[3].item() if query.shape[0] > 3 else 0),
                        []
                    )
                    filter_out = list(set(filter_out))
                    if query[2].item() in filter_out:
                        filter_out.remove(query[2].item())
                    if filter_out:
                        scores[i, torch.tensor(filter_out, dtype=torch.long, device=scores.device)] = -1e6

            return scores, targets

    def get_embeddings(self) -> Tuple[torch.Tensor, torch.Tensor]:
        """获取实体和关系嵌入"""
        return self.entity_embeddings.weight.data, self.relation_embeddings.weight.data

    def normalize_embeddings(self):
        """归一化实体嵌入（训练过程中定期调用）"""
        self.entity_embeddings.weight.data = F.normalize(
            self.entity_embeddings.weight.data, p=2, dim=1
        )


class TransELoss(nn.Module):
    """
    TransE的margin-based损失函数

    L = Σ max(0, margin + score(h, r, t) - score(h', r, t'))
    其中(h', r, t')是负样本
    """

    def __init__(self, margin: float = 1.0):
        super(TransELoss, self).__init__()
        self.margin = margin

    def forward(
        self,
        pos_scores: torch.Tensor,
        neg_scores: torch.Tensor
    ) -> torch.Tensor:
        """
        计算损失

        Args:
            pos_scores: 正样本得分
            neg_scores: 负样本得分

        Returns:
            loss: 损失值
        """
        # TransE使用负距离作为得分，得分越高越好
        # 损失：max(0, margin - pos_score + neg_score)
        if neg_scores.dim() > pos_scores.dim():
            pos_scores = pos_scores.unsqueeze(1)

        loss = torch.max(
            torch.zeros_like(pos_scores),
            self.margin - pos_scores + neg_scores
        )
        return loss.mean()


def negative_sampling(
    batch: torch.LongTensor,
    num_entities: int,
    num_neg: int = 1,
    mode: str = 'tail'
) -> torch.LongTensor:
    """
    负采样

    Args:
        batch: 正样本批次，形状为(batch_size, 3)
        num_entities: 实体数量
        num_neg: 每个正样本的负样本数量
        mode: 'tail'替换尾实体，'head'替换头实体

    Returns:
        neg_batch: 负样本批次，形状为(batch_size * num_neg, 3)
    """
    batch_size = batch.shape[0]
    neg_batch = batch.repeat(num_neg, 1)

    if mode == 'tail':
        # 替换尾实体
        neg_entities = torch.randint(0, num_entities, (batch_size * num_neg,))
        neg_batch[:, 2] = neg_entities
    else:
        # 替换头实体
        neg_entities = torch.randint(0, num_entities, (batch_size * num_neg,))
        neg_batch[:, 0] = neg_entities

    return neg_batch
