"""
时序基线模型训练器 - 用于训练TTransE、TComplEx、TRotatE模型

包含完整的训练、验证、测试流程，支持早停、模型保存和评估指标计算
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
import json
import time
from tqdm import tqdm
from typing import Dict, Tuple, List, Optional

from .t_transe import TTransE, TTransELoss
from .t_complex import TComplEx, TComplExLoss
from .t_rotate import TRotatE, TRotatELoss
from ..evaluator import KGEvaluator, save_metrics, print_metrics


class TKGTrainer:
    """
    时序基线模型训练器

    支持TTransE、TComplEx、TRotatE模型的训练、验证、测试
    """

    def __init__(
        self,
        model: nn.Module,
        model_name: str,
        dataset_name: str,
        num_entities: int,
        num_relations: int,
        num_timestamps: int,
        device: str = 'cuda:0',
        lr: float = 0.001,
        margin: float = 1.0,
        num_neg: int = 1
    ):
        """
        初始化训练器

        Args:
            model: 待训练的模型
            model_name: 模型名称
            dataset_name: 数据集名称
            num_entities: 实体数量
            num_relations: 关系数量
            num_timestamps: 时间戳数量
            device: 计算设备
            lr: 学习率
            margin: margin-based loss的边界值
            num_neg: 负样本数量
        """
        self.model = model.to(device)
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.num_entities = num_entities
        self.num_relations = num_relations
        self.num_timestamps = num_timestamps
        self.device = device
        self.lr = lr
        self.margin = margin
        self.num_neg = num_neg

        # 优化器
        self.optimizer = optim.Adam(model.parameters(), lr=lr)

        # 损失函数
        if model_name == 'TTransE':
            self.criterion = TTransELoss(margin=margin)
        elif model_name == 'TComplEx':
            self.criterion = TComplExLoss(margin=margin)
        elif model_name == 'TRotatE':
            self.criterion = TRotatELoss(margin=margin)
        else:
            raise ValueError(f"Unsupported model: {model_name}")

        # 评估器
        self.evaluator = TKGEvaluator(
            model=model,
            num_entities=num_entities,
            device=device
        )

        # 训练记录
        self.train_losses = []
        self.valid_metrics = []

    def train_epoch(
        self,
        train_data: torch.LongTensor,
        batch_size: int = 1000,
        epoch: int = 0
    ) -> float:
        """
        训练一个epoch

        Args:
            train_data: 训练数据，形状为(num_samples, 4)
            batch_size: 批次大小
            epoch: 当前epoch

        Returns:
            avg_loss: 平均损失
        """
        self.model.train()

        # 创建数据加载器
        dataset = TensorDataset(train_data)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        total_loss = 0.0
        num_batches = 0

        # 进度条
        pbar = tqdm(dataloader, desc=f'Epoch {epoch}')

        for batch in pbar:
            batch = batch[0].to(self.device)  # (batch_size, 4)

            # 正样本得分
            pos_scores = self.model(batch)

            # 负采样
            neg_batch = self._negative_sampling(batch)
            neg_scores = self.model(neg_batch)

            # 计算损失
            loss = self.criterion(pos_scores, neg_scores)

            # 反向传播
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

            # 归一化嵌入（对于某些模型）
            if hasattr(self.model, 'normalize_embeddings'):
                self.model.normalize_embeddings()

            total_loss += loss.item()
            num_batches += 1

            # 更新进度条
            pbar.set_postfix({'loss': loss.item()})

        avg_loss = total_loss / num_batches
        self.train_losses.append(avg_loss)

        return avg_loss

    def _negative_sampling(self, batch: torch.LongTensor) -> torch.LongTensor:
        """
        负采样

        Args:
            batch: 正样本批次，形状为(batch_size, 4)

        Returns:
            neg_batch: 负样本批次
        """
        batch_size = batch.shape[0]
        neg_batch = batch.clone()

        # 随机选择替换头实体或尾实体
        mode = np.random.choice(['head', 'tail'])

        if mode == 'tail':
            # 替换尾实体
            neg_entities = torch.randint(0, self.num_entities, (batch_size,))
            neg_batch[:, 2] = neg_entities
        else:
            # 替换头实体
            neg_entities = torch.randint(0, self.num_entities, (batch_size,))
            neg_batch[:, 0] = neg_entities

        return neg_batch

    def train(
        self,
        train_data: torch.LongTensor,
        valid_data: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]],
        num_epochs: int = 100,
        batch_size: int = 1000,
        save_path: Optional[str] = None,
        early_stop_patience: int = 10
    ) -> Dict[str, float]:
        """
        完整训练流程

        Args:
            train_data: 训练数据
            valid_data: 验证数据
            filters: 过滤字典
            num_epochs: 训练轮数
            batch_size: 批次大小
            save_path: 模型保存路径
            early_stop_patience: 早停耐心值

        Returns:
            best_metrics: 最佳验证指标
        """
        print(f"Training {self.model_name} on {self.dataset_name}")
        print(f"Train samples: {len(train_data)}, Valid samples: {len(valid_data)}")

        best_mrr = 0.0
        best_metrics = {}
        patience_counter = 0

        for epoch in range(1, num_epochs + 1):
            # 训练
            avg_loss = self.train_epoch(train_data, batch_size, epoch)

            # 验证
            valid_metrics = self.evaluate(valid_data, filters)

            # 记录
            self.valid_metrics.append(valid_metrics)

            # 打印
            print(f"Epoch {epoch}: Loss={avg_loss:.4f}, MRR={valid_metrics['mrr']:.4f}, "
                  f"Hits@1={valid_metrics['hits@1']:.4f}, Hits@10={valid_metrics['hits@10']:.4f}")

            # 保存最佳模型
            if valid_metrics['mrr'] > best_mrr:
                best_mrr = valid_metrics['mrr']
                best_metrics = valid_metrics
                patience_counter = 0

                if save_path:
                    self.save_model(save_path)
                    print(f"Saved best model to {save_path}")
            else:
                patience_counter += 1

            # 早停
            if patience_counter >= early_stop_patience:
                print(f"Early stopping at epoch {epoch}")
                break

        return best_metrics

    def evaluate(
        self,
        data: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]]
    ) -> Dict[str, float]:
        """
        评估模型

        Args:
            data: 测试数据
            filters: 过滤字典

        Returns:
            metrics: 评估指标
        """
        return self.evaluator.evaluate(data, filters)

    def save_model(self, path: str):
        """保存模型"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_name': self.model_name,
            'dataset_name': self.dataset_name,
            'num_entities': self.num_entities,
            'num_relations': self.num_relations,
            'num_timestamps': self.num_timestamps,
            'train_losses': self.train_losses,
            'valid_metrics': self.valid_metrics
        }, path)

    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.train_losses = checkpoint.get('train_losses', [])
        self.valid_metrics = checkpoint.get('valid_metrics', [])


class TKGEvaluator:
    """
    时序知识图谱评估器

    计算MRR、Hits@1、Hits@3、Hits@10等指标
    """

    def __init__(
        self,
        model: nn.Module,
        num_entities: int,
        device: str = 'cuda:0'
    ):
        """
        初始化评估器

        Args:
            model: 待评估的模型
            num_entities: 实体数量
            device: 计算设备
        """
        self.model = model
        self.num_entities = num_entities
        self.device = device

    def evaluate(
        self,
        data: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]],
        batch_size: int = 100
    ) -> Dict[str, float]:
        """
        评估模型

        Args:
            data: 测试数据，形状为(num_samples, 4)
            filters: 过滤字典
            batch_size: 批次大小

        Returns:
            metrics: 评估指标字典
        """
        self.model.eval()

        ranks = []

        dataset = TensorDataset(data)
        dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=False)

        with torch.no_grad():
            for batch in tqdm(dataloader, desc='Evaluating'):
                batch = batch[0].to(self.device)

                # 预测
                scores, targets = self.model.predict(batch, filters)

                # 计算排名
                for i in range(len(batch)):
                    score = scores[i]
                    target_score = targets[i]

                    # 排名 = 得分大于目标得分的实体数量 + 1
                    rank = (score > target_score).sum().item() + 1
                    ranks.append(rank)

        ranks = np.array(ranks)

        # 计算指标
        mrr = np.mean(1.0 / ranks)
        hits1 = np.mean(ranks <= 1)
        hits3 = np.mean(ranks <= 3)
        hits10 = np.mean(ranks <= 10)

        metrics = {
            'mrr': mrr,
            'hits@1': hits1,
            'hits@3': hits3,
            'hits@10': hits10
        }

        return metrics


def load_tkg_data(dataset_path: str) -> Tuple[torch.LongTensor, ...]:
    """
    加载时序知识图谱数据

    Args:
        dataset_path: 数据集路径

    Returns:
        train_data: 训练数据
        valid_data: 验证数据
        test_data: 测试数据
        num_entities: 实体数量
        num_relations: 关系数量
        num_timestamps: 时间戳数量
    """
    # 加载训练集
    train_data = np.loadtxt(os.path.join(dataset_path, 'train.txt'), dtype=np.int64)
    valid_data = np.loadtxt(os.path.join(dataset_path, 'valid.txt'), dtype=np.int64)
    test_data = np.loadtxt(os.path.join(dataset_path, 'test.txt'), dtype=np.int64)

    # 加载统计信息
    with open(os.path.join(dataset_path, 'stat'), 'r') as f:
        stat = f.read().strip().split()
        num_entities = int(stat[0])
        num_relations = int(stat[1])
        num_timestamps = int(stat[2]) if len(stat) > 2 else 1

    return (
        torch.LongTensor(train_data),
        torch.LongTensor(valid_data),
        torch.LongTensor(test_data),
        num_entities,
        num_relations,
        num_timestamps
    )


def build_tkg_filters(
    train_data: torch.LongTensor,
    valid_data: torch.LongTensor,
    test_data: torch.LongTensor
) -> Dict[Tuple[int, int, int], List[int]]:
    """
    构建过滤字典

    Args:
        train_data: 训练数据
        valid_data: 验证数据
        test_data: 测试数据

    Returns:
        filters: 过滤字典
    """
    filters = {}

    # 合并所有数据
    all_data = torch.cat([train_data, valid_data, test_data], dim=0)

    for quad in all_data:
        h, r, t, ts = quad.tolist()
        key = (h, r, ts)
        if key not in filters:
            filters[key] = []
        filters[key].append(t)

    return filters
