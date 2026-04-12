"""
时序知识图谱模型基类

所有时序知识图谱模型（TTransE、TComplEx、TRotatE等）都应继承此基类，
实现统一的接口以支持训练和评估。
"""

import torch
import torch.nn as nn
from abc import ABC, abstractmethod
from typing import Dict, Tuple, List, Optional


class BaseTKGModel(nn.Module, ABC):
    """
    时序知识图谱模型基类

    时序知识图谱数据格式为四元组(subject, relation, object, timestamp)
    模型需要处理时间信息，将时间编码融入实体和关系嵌入中
    """

    def __init__(
        self,
        num_entities: int,
        num_relations: int,
        num_timestamps: int,
        embedding_dim: int = 200,
        is_cuda: bool = False
    ):
        """
        初始化基类

        Args:
            num_entities: 实体数量
            num_relations: 关系数量
            num_timestamps: 时间戳数量
            embedding_dim: 嵌入维度
            is_cuda: 是否使用GPU
        """
        super(BaseTKGModel, self).__init__()

        self.num_entities = num_entities
        self.num_relations = num_relations
        self.num_timestamps = num_timestamps
        self.embedding_dim = embedding_dim
        self.is_cuda = is_cuda

    @abstractmethod
    def forward(self, batch: torch.LongTensor) -> torch.Tensor:
        """
        前向传播，计算四元组的得分

        Args:
            batch: 形状为(batch_size, 4)的张量，每行为(h, r, t, timestamp)

        Returns:
            scores: 形状为(batch_size,)的得分张量
        """
        pass

    @abstractmethod
    def score(self, batch: torch.LongTensor) -> torch.Tensor:
        """
        计算四元组的得分（与forward相同，提供语义化接口）

        Args:
            batch: 形状为(batch_size, 4)的张量

        Returns:
            scores: 形状为(batch_size,)的得分张量
        """
        pass

    @abstractmethod
    def predict(
        self,
        batch: torch.LongTensor,
        filters: Optional[Dict[Tuple[int, int, int], List[int]]] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测所有候选实体的得分（用于评估）

        Args:
            batch: 形状为(batch_size, 4)的张量，每行为(h, r, t, timestamp)
            filters: 过滤字典，用于过滤已知正确答案
                key: (head_id, relation_id, timestamp_id)
                value: 已知正确答案的实体ID列表

        Returns:
            scores: 形状为(batch_size, num_entities)的得分矩阵
            targets: 形状为(batch_size, 1)的目标得分
        """
        pass

    def normalize_embeddings(self):
        """
        归一化嵌入向量（训练过程中定期调用）
        子类可根据需要重写此方法
        """
        pass

    def get_regularization_term(self) -> torch.Tensor:
        """
        获取正则化项
        子类可根据需要重写此方法

        Returns:
            reg_term: 正则化项的值
        """
        return torch.tensor(0.0)

    def save_embeddings(self, path: str):
        """
        保存嵌入向量到文件

        Args:
            path: 保存路径
        """
        torch.save(self.state_dict(), path)

    def load_embeddings(self, path: str):
        """
        从文件加载嵌入向量

        Args:
            path: 文件路径
        """
        self.load_state_dict(torch.load(path))
