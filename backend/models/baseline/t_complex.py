"""
TComplEx模型实现 - 时序知识图谱基线模型

TComplEx是ComplEx的时序扩展，使用复数嵌入和时序旋转编码。
对于四元组(h, r, t, τ)，TComplEx使用复数三线性得分函数，
并通过时序旋转 exp(i * ω * τ) 编码时间信息。

参考论文: Lacroix et al., "Canonical Tensor Decomposition for Knowledge Base Completion", ICML 2018
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, List, Optional
import numpy as np

from .base_tkg_model import BaseTKGModel


class TComplEx(BaseTKGModel):
    """
    TComplEx模型实现

    对于四元组(h, r, t, τ)，得分函数为：
    score(h, r, t, τ) = Re(<h, r_t, t_bar>)

    其中：
    - h, r, t 是复数嵌入（实部+虚部）
    - r_t = r * exp(i * ω * τ) 是时序旋转后的关系
    - t_bar 是t的共轭
    - <.,.,.> 是三线性积
    """

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        num_timestamps: int,
        embedding_dim: int = 200,
        margin: float = 1.0,
        is_cuda: bool = False
    ):
        """
        初始化TComplEx模型

        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            num_timestamps: 时间戳数量
            embedding_dim: 嵌入维度（复数的实部或虚部维度）
            margin: margin-based loss的边界值
            is_cuda: 是否使用GPU
        """
        super(TComplEx, self).__init__(
            num_entities, num_relations, num_timestamps,
            embedding_dim, is_cuda
        )

        self.model_name = "TComplEx"
        self.margin = margin

        # 实体嵌入（实部和虚部）
        self.entity_real = nn.Embedding(num_entities, embedding_dim)
        self.entity_img = nn.Embedding(num_entities, embedding_dim)

        # 关系嵌入（实部和虚部）
        self.relation_real = nn.Embedding(num_relations, embedding_dim)
        self.relation_img = nn.Embedding(num_relations, embedding_dim)

        # 时间频率参数（用于时序旋转）
        self.time_freq = nn.Embedding(num_timestamps, embedding_dim)

        # 初始化参数
        self._init_embeddings()

    def _init_embeddings(self):
        """使用Xavier均匀分布初始化嵌入"""
        nn.init.xavier_uniform_(self.entity_real.weight.data)
        nn.init.xavier_uniform_(self.entity_img.weight.data)
        nn.init.xavier_uniform_(self.relation_real.weight.data)
        nn.init.xavier_uniform_(self.relation_img.weight.data)
        nn.init.xavier_uniform_(self.time_freq.weight.data)

    def _get_time_rotation(self, timestamps: torch.LongTensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        获取时序旋转因子 exp(i * ω * τ)

        Args:
            timestamps: 时间戳ID张量

        Returns:
            cos_term: cos(ω * τ)
            sin_term: sin(ω * τ)
        """
        omega = self.time_freq(timestamps)  # (batch_size, dim)
        cos_term = torch.cos(omega)
        sin_term = torch.sin(omega)
        return cos_term, sin_term

    def _complex_multiply(
        self,
        a_real: torch.Tensor,
        a_img: torch.Tensor,
        b_real: torch.Tensor,
        b_img: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        复数乘法：(a_real + i*a_img) * (b_real + i*b_img)

        Returns:
            real: 实部
            img: 虚部
        """
        real = a_real * b_real - a_img * b_img
        img = a_real * b_img + a_img * b_real
        return real, img

    def forward(self, batch: torch.LongTensor) -> torch.Tensor:
        """
        前向传播，计算四元组的得分

        Args:
            batch: 形状为(batch_size, 4)的张量，每行为(h, r, t, timestamp)

        Returns:
            scores: 形状为(batch_size,)的得分张量
        """
        # 获取嵌入
        h_real = self.entity_real(batch[:, 0])
        h_img = self.entity_img(batch[:, 0])

        r_real = self.relation_real(batch[:, 1])
        r_img = self.relation_img(batch[:, 1])

        t_real = self.entity_real(batch[:, 2])
        t_img = self.entity_img(batch[:, 2])

        # 时序旋转：r_t = r * exp(i * ω * τ)
        cos_term, sin_term = self._get_time_rotation(batch[:, 3])
        r_t_real, r_t_img = self._complex_multiply(r_real, r_img, cos_term, sin_term)

        # 计算三线性积的实部
        # Re(<h, r_t, t_bar>) = Re(h * r_t * t_bar)
        # t_bar = t_real - i*t_img
        # 先计算 h * r_t
        hr_real, hr_img = self._complex_multiply(h_real, h_img, r_t_real, r_t_img)

        # 再计算 (h * r_t) * t_bar
        # (hr_real + i*hr_img) * (t_real - i*t_img)
        score_real = hr_real * t_real + hr_img * t_img

        # 得分为实部的和
        scores = score_real.sum(dim=1)

        return scores

    def score(self, batch: torch.LongTensor) -> torch.Tensor:
        """计算四元组的得分（与forward相同）"""
        return self.forward(batch)

    def predict(
        self,
        batch: torch.LongTensor,
        filters: Optional[Dict[Tuple[int, int, int], List[int]]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测所有候选实体的得分（用于评估）

        Args:
            batch: 形状为(batch_size, 4)的张量
            filters: 过滤字典

        Returns:
            scores: 形状为(batch_size, num_entities)的得分矩阵
            targets: 形状为(batch_size, 1)的目标得分
        """
        with torch.no_grad():
            batch_size = batch.shape[0]

            # 获取头实体和关系嵌入
            h_real = self.entity_real(batch[:, 0])  # (batch_size, dim)
            h_img = self.entity_img(batch[:, 0])

            r_real = self.relation_real(batch[:, 1])
            r_img = self.relation_img(batch[:, 1])

            # 时序旋转
            cos_term, sin_term = self._get_time_rotation(batch[:, 3])
            r_t_real, r_t_img = self._complex_multiply(r_real, r_img, cos_term, sin_term)

            # 计算 h * r_t
            hr_real, hr_img = self._complex_multiply(h_real, h_img, r_t_real, r_t_img)

            # 获取所有实体嵌入
            all_t_real = self.entity_real.weight  # (num_entities, dim)
            all_t_img = self.entity_img.weight

            # 计算得分：Re(hr * t_bar) = hr_real * t_real + hr_img * t_img
            # 扩展维度以便广播
            hr_real = hr_real.unsqueeze(1)  # (batch_size, 1, dim)
            hr_img = hr_img.unsqueeze(1)
            all_t_real = all_t_real.unsqueeze(0)  # (1, num_entities, dim)
            all_t_img = all_t_img.unsqueeze(0)

            # 计算得分矩阵
            scores = (hr_real * all_t_real + hr_img * all_t_img).sum(dim=2)  # (batch_size, num_entities)

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
                        (query[0].item(), query[1].item(), query[3].item()),
                        []
                    )
                    filter_out = list(set(filter_out))
                    if query[2].item() in filter_out:
                        filter_out.remove(query[2].item())
                    if filter_out:
                        scores[i, torch.tensor(filter_out, dtype=torch.long, device=scores.device)] = -1e6

            return scores, targets


class TComplExLoss(nn.Module):
    """
    TComplEx的负采样损失函数

    L = -log(σ(score(h, r, t, τ))) - log(1 - σ(score(h', r, t', τ)))
    """

    def __init__(self, margin: float = 1.0):
        super(TComplExLoss, self).__init__()
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
        # 使用softplus损失
        if neg_scores.dim() > pos_scores.dim():
            pos_scores = pos_scores.unsqueeze(1)

        # 损失：log(1 + exp(-pos_score)) + log(1 + exp(neg_score))
        loss = F.softplus(-pos_scores) + F.softplus(neg_scores)
        return loss.mean()
