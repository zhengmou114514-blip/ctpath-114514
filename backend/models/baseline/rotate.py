"""
RotatE模型实现 - 静态知识图谱基线模型

RotatE将关系建模为复数空间中的旋转操作。
对于三元组(h, r, t)，RotatE假设 h ∘ r = t，其中∘表示复数乘法（旋转）

参考论文: Sun et al., "RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space", ICLR 2019
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, List
import numpy as np


class RotatE(nn.Module):
    """
    RotatE模型实现

    对于三元组(h, r, t)，得分函数为：
    score(h, r, t) = -||h ∘ r - t||

    其中h, r, t都是复数向量，∘表示逐元素的复数乘法（旋转）
    """

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        embedding_dim: int = 200,
        margin: float = 1.0,
        epsilon: float = 2.0,
        is_cuda: bool = False
    ):
        """
        初始化RotatE模型

        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            embedding_dim: 嵌入维度（实数维度，复数维度为embedding_dim/2）
            margin: margin-based loss的边界值
            epsilon: Adversarial negative sampling的参数
            is_cuda: 是否使用GPU
        """
        super(RotatE, self).__init__()

        if embedding_dim % 2 != 0:
            raise ValueError("RotatE requires an even embedding_dim")

        self.model_name = "RotatE"
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.embedding_dim = embedding_dim
        self.margin = margin
        self.epsilon = epsilon
        self.is_cuda = is_cuda

        # 实体嵌入（复数表示，实数维度为embedding_dim）
        self.entity_embeddings = nn.Embedding(num_entities, embedding_dim)
        # 关系嵌入（相位，用于旋转）
        self.relation_embeddings = nn.Embedding(num_relations, embedding_dim // 2)

        # 初始化参数
        self._init_embeddings()

    def _init_embeddings(self):
        """使用Xavier均匀分布初始化嵌入"""
        nn.init.xavier_uniform_(self.entity_embeddings.weight.data)
        nn.init.xavier_uniform_(self.relation_embeddings.weight.data)

    def complex_mul(self, a: torch.Tensor, b: torch.Tensor) -> torch.Tensor:
        """
        复数乘法（旋转操作）

        对于复数a = a_r + i*a_i，b = b_r + i*b_i
        a * b = (a_r*b_r - a_i*b_i) + i*(a_r*b_i + a_i*b_r)

        Args:
            a: 形状为(batch_size, dim)的实数张量，表示复数
            b: 形状为(batch_size, dim)的实数张量，表示复数

        Returns:
            result: 形状为(batch_size, dim)的实数张量
        """
        # 将实数张量分为实部和虚部
        a_r, a_i = torch.chunk(a, 2, dim=1)
        b_r, b_i = torch.chunk(b, 2, dim=1)

        # 复数乘法
        real = a_r * b_r - a_i * b_i
        imag = a_r * b_i + a_i * b_r

        return torch.cat([real, imag], dim=1)

    def forward(self, batch: torch.LongTensor) -> torch.Tensor:
        """
        前向传播，计算三元组的得分

        Args:
            batch: 形状为(batch_size, 3)的张量，每行为(h, r, t)

        Returns:
            scores: 形状为(batch_size,)的得分张量
        """
        h = self.entity_embeddings(batch[:, 0])  # (batch_size, dim)
        r_phase = self.relation_embeddings(batch[:, 1])  # (batch_size, dim)
        t = self.entity_embeddings(batch[:, 2])  # (batch_size, dim)

        # 将关系相位转换为复数（旋转）
        # r = cos(θ) + i*sin(θ)
        r_r = torch.cos(r_phase)
        r_i = torch.sin(r_phase)
        r = torch.cat([r_r, r_i], dim=1)

        # 计算h ∘ r - t
        h_rotate_r = self.complex_mul(h, r)
        diff = h_rotate_r - t

        # 计算L1范数
        scores = -torch.norm(diff, p=1, dim=1)

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
            r_phase = self.relation_embeddings(batch[:, 1])  # (batch_size, dim)
            t = self.entity_embeddings(batch[:, 2])  # (batch_size, dim)

            # 将关系相位转换为复数（旋转）
            r_r = torch.cos(r_phase)
            r_i = torch.sin(r_phase)
            r = torch.cat([r_r, r_i], dim=1)

            # 计算h ∘ r
            h_rotate_r = self.complex_mul(h, r)  # (batch_size, dim)

            # 计算所有候选实体的得分
            all_entities = self.entity_embeddings.weight  # (num_entities, dim)

            # 扩展维度以便广播
            h_rotate_r = h_rotate_r.unsqueeze(1)  # (batch_size, 1, dim)
            all_entities = all_entities.unsqueeze(0)  # (1, num_entities, dim)

            # 计算距离
            scores = -torch.norm(h_rotate_r - all_entities, p=1, dim=2)  # (batch_size, num_entities)

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


class RotatELoss(nn.Module):
    """
    RotatE的Adversarial Negative Sampling损失函数

    L = -log(σ(γ - d(h, r, t))) - Σ P(h'_j, r, t'_j) log(σ(d(h'_j, r, t'_j) - γ))

    其中σ是sigmoid函数，γ是margin，P是负样本的权重
    """

    def __init__(self, margin: float = 1.0, adversarial_temperature: float = 1.0):
        super(RotatELoss, self).__init__()
        self.margin = margin
        self.adversarial_temperature = adversarial_temperature

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
        # RotatE使用负距离作为得分，得分越高越好
        # 使用Adversarial Negative Sampling
        neg_score_weights = F.softmax(
            neg_scores * self.adversarial_temperature,
            dim=1
        ).detach()

        # 正样本损失
        pos_loss = -F.logsigmoid(pos_scores + self.margin).mean()

        # 负样本损失
        neg_loss = -(neg_score_weights * F.logsigmoid(-neg_scores - self.margin)).sum(dim=1).mean()

        return (pos_loss + neg_loss) / 2
