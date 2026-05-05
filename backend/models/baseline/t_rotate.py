"""
TRotatE模型实现 - 时序知识图谱基线模型

TRotatE是RotatE的时序扩展，将关系建模为复数平面上的旋转操作，
并通过时序相位调制编码时间信息。

对于四元组(h, r, t, τ)，TRotatE假设 h * r_t = t
其中 r_t 是经过时序调制的旋转关系。

参考论文: Sun et al., "RotatE: Knowledge Graph Embedding by Relational Rotation in Complex Space", ICLR 2019
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, List, Optional
import numpy as np

from .base_tkg_model import BaseTKGModel


class TRotatE(BaseTKGModel):
    """
    TRotatE模型实现

    对于四元组(h, r, t, τ)，得分函数为：
    score(h, r, t, τ) = -||h * r_t - t||

    其中：
    - h, t 是复数嵌入，模长为1
    - r_t = r * exp(i * (θ_r + ω * τ)) 是时序调制后的旋转关系
    - θ_r 是关系的相位
    - ω * τ 是时序相位调制
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
        初始化TRotatE模型

        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            num_timestamps: 时间戳数量
            embedding_dim: 嵌入维度（复数的实部或虚部维度）
            margin: margin-based loss的边界值
            is_cuda: 是否使用GPU
        """
        super(TRotatE, self).__init__(
            num_entities, num_relations, num_timestamps,
            embedding_dim, is_cuda
        )

        self.model_name = "TRotatE"
        self.margin = margin

        # 实体嵌入（实部和虚部，模长为1）
        self.entity_real = nn.Embedding(num_entities, embedding_dim)
        self.entity_img = nn.Embedding(num_entities, embedding_dim)

        # 关系相位嵌入（用于旋转）
        self.relation_phase = nn.Embedding(num_relations, embedding_dim)

        # 时间频率参数（用于时序相位调制）
        self.time_freq = nn.Embedding(num_timestamps, embedding_dim)

        # 初始化参数
        self._init_embeddings()

    def _init_embeddings(self):
        """初始化嵌入"""
        # 实体嵌入初始化为单位圆上的点
        nn.init.xavier_uniform_(self.entity_real.weight.data)
        nn.init.xavier_uniform_(self.entity_img.weight.data)

        # 归一化为单位模长
        entity_norm = torch.sqrt(
            self.entity_real.weight.data ** 2 + self.entity_img.weight.data ** 2
        )
        self.entity_real.weight.data = self.entity_real.weight.data / entity_norm
        self.entity_img.weight.data = self.entity_img.weight.data / entity_norm

        # 关系相位初始化为[0, 2π]
        nn.init.uniform_(self.relation_phase.weight.data, 0, 2 * np.pi)

        # 时间频率初始化
        nn.init.xavier_uniform_(self.time_freq.weight.data)

    def _get_rotation(
        self,
        relation_phases: torch.Tensor,
        time_freqs: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        获取时序调制后的旋转因子

        Args:
            relation_phases: 关系相位
            time_freqs: 时间频率

        Returns:
            cos_term: cos(θ_r + ω * τ)
            sin_term: sin(θ_r + ω * τ)
        """
        # 时序调制相位：θ_r + ω * τ
        modulated_phase = relation_phases + time_freqs
        cos_term = torch.cos(modulated_phase)
        sin_term = torch.sin(modulated_phase)
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
        # 获取实体嵌入
        h_real = self.entity_real(batch[:, 0])
        h_img = self.entity_img(batch[:, 0])

        t_real = self.entity_real(batch[:, 2])
        t_img = self.entity_img(batch[:, 2])

        # 获取关系相位和时间频率
        r_phase = self.relation_phase(batch[:, 1])
        time_freq = self.time_freq(batch[:, 3])

        # 时序调制旋转
        cos_term, sin_term = self._get_rotation(r_phase, time_freq)

        # 计算 h * r_t
        hr_real, hr_img = self._complex_multiply(h_real, h_img, cos_term, sin_term)

        # 计算距离 ||h * r_t - t||
        diff_real = hr_real - t_real
        diff_img = hr_img - t_img

        # 使用L2范数
        scores = -torch.sqrt(diff_real ** 2 + diff_img ** 2 + 1e-10).sum(dim=1)

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

            # 获取头实体嵌入
            h_real = self.entity_real(batch[:, 0])  # (batch_size, dim)
            h_img = self.entity_img(batch[:, 0])

            # 获取关系相位和时间频率
            r_phase = self.relation_phase(batch[:, 1])
            time_freq = self.time_freq(batch[:, 3])

            # 时序调制旋转
            cos_term, sin_term = self._get_rotation(r_phase, time_freq)

            # 计算 h * r_t
            hr_real, hr_img = self._complex_multiply(h_real, h_img, cos_term, sin_term)

            # 获取所有实体嵌入
            all_t_real = self.entity_real.weight  # (num_entities, dim)
            all_t_img = self.entity_img.weight

            # 计算距离 ||h * r_t - t||
            hr_real = hr_real.unsqueeze(1)  # (batch_size, 1, dim)
            hr_img = hr_img.unsqueeze(1)
            all_t_real = all_t_real.unsqueeze(0)  # (1, num_entities, dim)
            all_t_img = all_t_img.unsqueeze(0)

            diff_real = hr_real - all_t_real
            diff_img = hr_img - all_t_img

            scores = -torch.sqrt(diff_real ** 2 + diff_img ** 2 + 1e-10).sum(dim=2)

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

    def normalize_embeddings(self):
        """归一化实体嵌入为单位模长"""
        entity_norm = torch.sqrt(
            self.entity_real.weight.data ** 2 + self.entity_img.weight.data ** 2
        )
        self.entity_real.weight.data = self.entity_real.weight.data / entity_norm
        self.entity_img.weight.data = self.entity_img.weight.data / entity_norm


class TRotatELoss(nn.Module):
    """
    TRotatE的margin-based损失函数

    L = Σ max(0, margin + score(h, r, t, τ) - score(h', r, t', τ))
    """

    def __init__(self, margin: float = 1.0):
        super(TRotatELoss, self).__init__()
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
        if neg_scores.dim() > pos_scores.dim():
            pos_scores = pos_scores.unsqueeze(1)

        loss = torch.max(
            torch.zeros_like(pos_scores),
            self.margin - pos_scores + neg_scores
        )
        return loss.mean()
