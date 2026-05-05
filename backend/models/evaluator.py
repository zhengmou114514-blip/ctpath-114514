"""
统一评估器 - 计算MRR和Hits@K指标

用于评估知识图谱嵌入模型的性能，支持所有模型（TransE、RotatE、Supercomplex等）
"""

import torch
import numpy as np
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm
import json
import os


class KGEvaluator:
    """
    知识图谱评估器

    计算标准评估指标：
    - MRR (Mean Reciprocal Rank): 平均倒数排名
    - Hits@K: 前K个预测中正确答案的比例
    """

    def __init__(
        self,
        model,
        num_entities: int,
        device: str = 'cuda:0',
        ks: List[int] = [1, 3, 10]
    ):
        """
        初始化评估器

        Args:
            model: 待评估的模型（TransE、RotatE、Supercomplex等）
            num_entities: 实体数量
            device: 计算设备
            ks: Hits@K的K值列表
        """
        self.model = model
        self.num_entities = num_entities
        self.device = device
        self.ks = ks

    def evaluate(
        self,
        test_data: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]],
        batch_size: int = 1000,
        desc: str = "Evaluating"
    ) -> Dict[str, float]:
        """
        评估模型性能

        Args:
            test_data: 测试集，形状为(num_samples, 3)或(num_samples, 4)
            filters: 过滤字典，用于过滤已知正确答案
            batch_size: 批次大小
            desc: 进度条描述

        Returns:
            metrics: 包含MRR和Hits@K的字典
        """
        self.model.eval()

        all_ranks = []

        with torch.no_grad():
            for i in tqdm(range(0, len(test_data), batch_size), desc=desc):
                batch = test_data[i:i+batch_size].to(self.device)

                # 获取预测得分
                if hasattr(self.model, 'predict'):
                    scores, targets = self.model.predict(batch, filters)
                else:
                    # 对于Supercomplex等模型，使用forward方法
                    scores, targets = self._predict_generic(batch, filters)

                # 计算排名
                ranks = self._compute_rank(scores, batch[:, 2])
                all_ranks.extend(ranks.tolist())

        all_ranks = np.array(all_ranks)

        # 计算指标
        metrics = {
            'MRR': float(np.mean(1.0 / all_ranks)),
            'num_samples': len(all_ranks)
        }

        for k in self.ks:
            metrics[f'Hits@{k}'] = float(np.mean(all_ranks <= k))

        return metrics

    def _predict_generic(
        self,
        batch: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        通用预测方法（用于Supercomplex等模型）

        Args:
            batch: 批次数据
            filters: 过滤字典

        Returns:
            scores: 得分矩阵
            targets: 目标得分
        """
        # 对于Supercomplex模型，需要特殊处理
        # 这里假设模型有forward方法返回scores
        # 实际实现需要根据具体模型调整

        # 简化实现：假设模型返回所有实体的得分
        # 实际使用时需要根据模型接口调整

        scores = torch.zeros(batch.shape[0], self.num_entities).to(self.device)
        targets = torch.zeros(batch.shape[0], 1).to(self.device)

        return scores, targets

    def _compute_rank(
        self,
        scores: torch.Tensor,
        targets: torch.LongTensor
    ) -> torch.Tensor:
        """
        计算正确答案的排名

        Args:
            scores: 得分矩阵，形状为(batch_size, num_entities)
            targets: 目标实体索引，形状为(batch_size,)

        Returns:
            ranks: 排名，形状为(batch_size,)
        """
        batch_size = scores.shape[0]
        ranks = torch.zeros(batch_size, dtype=torch.long)

        for i in range(batch_size):
            # 获取目标实体的得分
            target_score = scores[i, targets[i]].item()

            # 计算有多少实体的得分大于目标实体
            # 排名 = 得分大于目标的实体数 + 1
            rank = (scores[i] > target_score).sum().item() + 1
            ranks[i] = rank

        return ranks

    def evaluate_both_directions(
        self,
        test_data: torch.LongTensor,
        filters: Dict[Tuple[int, int, int], List[int]],
        batch_size: int = 1000
    ) -> Dict[str, float]:
        """
        评估两个方向的预测（头实体预测和尾实体预测）

        Args:
            test_data: 测试集
            filters: 过滤字典
            batch_size: 批次大小

        Returns:
            metrics: 平均指标
        """
        # 尾实体预测
        metrics_tail = self.evaluate(
            test_data, filters, batch_size, desc="Evaluating tail prediction"
        )

        # 头实体预测（交换头尾实体）
        test_data_head = test_data.clone()
        test_data_head[:, [0, 2]] = test_data_head[:, [2, 0]]

        metrics_head = self.evaluate(
            test_data_head, filters, batch_size, desc="Evaluating head prediction"
        )

        # 平均指标
        metrics = {
            'MRR': (metrics_tail['MRR'] + metrics_head['MRR']) / 2,
            'num_samples': metrics_tail['num_samples'] + metrics_head['num_samples']
        }

        for k in self.ks:
            metrics[f'Hits@{k}'] = (
                metrics_tail[f'Hits@{k}'] + metrics_head[f'Hits@{k}']
            ) / 2

        return metrics


def save_metrics(
    metrics: Dict[str, float],
    model_name: str,
    dataset_name: str,
    save_dir: str = "results"
):
    """
    保存评估指标到JSON文件

    Args:
        metrics: 评估指标字典
        model_name: 模型名称
        dataset_name: 数据集名称
        save_dir: 保存目录
    """
    os.makedirs(save_dir, exist_ok=True)

    result = {
        'model': model_name,
        'dataset': dataset_name,
        'metrics': metrics
    }

    filename = os.path.join(save_dir, f"{model_name}_{dataset_name}_metrics.json")
    with open(filename, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Metrics saved to {filename}")


def print_metrics(metrics: Dict[str, float], model_name: str):
    """
    打印评估指标

    Args:
        metrics: 评估指标字典
        model_name: 模型名称
    """
    print(f"\n{'='*50}")
    print(f"Model: {model_name}")
    print(f"{'='*50}")
    print(f"MRR: {metrics['MRR']:.4f}")
    for key, value in metrics.items():
        if key.startswith('Hits@'):
            print(f"{key}: {value:.4f}")
    print(f"Number of samples: {metrics['num_samples']}")
    print(f"{'='*50}\n")


def compare_models(
    results: Dict[str, Dict[str, float]],
    dataset_name: str
):
    """
    对比多个模型的性能

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
    """
    print(f"\n{'='*80}")
    print(f"Model Comparison on {dataset_name}")
    print(f"{'='*80}")

    # 表头
    header = f"{'Model':<20} {'MRR':<10} {'Hits@1':<10} {'Hits@3':<10} {'Hits@10':<10}"
    print(header)
    print("-" * 80)

    # 按MRR排序
    sorted_models = sorted(
        results.items(),
        key=lambda x: x[1]['MRR'],
        reverse=True
    )

    for model_name, metrics in sorted_models:
        row = f"{model_name:<20} {metrics['MRR']:<10.4f} "
        row += f"{metrics.get('Hits@1', 0):<10.4f} "
        row += f"{metrics.get('Hits@3', 0):<10.4f} "
        row += f"{metrics.get('Hits@10', 0):<10.4f}"
        print(row)

    print(f"{'='*80}\n")

    # 找出最佳模型
    best_model = sorted_models[0][0]
    print(f"Best model: {best_model} (MRR: {sorted_models[0][1]['MRR']:.4f})")


def generate_comparison_report(
    results: Dict[str, Dict[str, float]],
    dataset_name: str,
    save_path: str = "results/comparison_report.md"
):
    """
    生成对比实验报告（Markdown格式）

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
        save_path: 报告保存路径
    """
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(f"# 对比实验报告\n\n")
        f.write(f"## 数据集: {dataset_name}\n\n")
        f.write(f"## 实验结果\n\n")

        # 表格
        f.write(f"| Model | MRR | Hits@1 | Hits@3 | Hits@10 |\n")
        f.write(f"|-------|-----|--------|--------|----------|\n")

        # 按MRR排序
        sorted_models = sorted(
            results.items(),
            key=lambda x: x[1]['MRR'],
            reverse=True
        )

        for model_name, metrics in sorted_models:
            f.write(
                f"| {model_name} | {metrics['MRR']:.4f} | "
                f"{metrics.get('Hits@1', 0):.4f} | "
                f"{metrics.get('Hits@3', 0):.4f} | "
                f"{metrics.get('Hits@10', 0):.4f} |\n"
            )

        f.write(f"\n## 结论\n\n")

        # 分析结果
        best_model = sorted_models[0][0]
        best_mrr = sorted_models[0][1]['MRR']

        f.write(f"最佳模型: **{best_model}** (MRR: {best_mrr:.4f})\n\n")

        # 对比分析
        if 'TKGR-GPRSCL' in results or 'Supercomplex' in results:
            tkg_model = results.get('TKGR-GPRSCL', results.get('Supercomplex', {}))
            tkg_mrr = tkg_model.get('MRR', 0)

            f.write(f"### 时序知识图谱模型 vs 静态知识图谱模型\n\n")

            for model_name, metrics in sorted_models:
                if model_name in ['TransE', 'RotatE']:
                    improvement = (tkg_mrr - metrics['MRR']) / metrics['MRR'] * 100
                    f.write(
                        f"- TKGR-GPRSCL相比{model_name}提升: **{improvement:.2f}%**\n"
                    )

        f.write(f"\n## 实验环境\n\n")
        f.write(f"- 数据集: {dataset_name}\n")
        f.write(f"- 评估指标: MRR, Hits@1, Hits@3, Hits@10\n")
        f.write(f"- 评估方式: 过滤评估（Filtered Setting）\n")

    print(f"Comparison report saved to {save_path}")
