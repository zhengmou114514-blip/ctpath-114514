"""
对比实验脚本

在CHRONIC数据集上对比TKGR-GPRSCL、TransE、RotatE三个模型的性能
"""

import torch
import os
import sys
import json
import time
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.baseline import TransE, RotatE, BaselineTrainer, load_data, build_filters
from models.evaluator import (
    KGEvaluator,
    save_metrics,
    print_metrics,
    compare_models,
    generate_comparison_report
)
from models.visualization import generate_all_visualizations


def run_comparison_experiment(
    dataset_path: str = "data/CHRONIC",
    embedding_dim: int = 200,
    num_epochs: int = 50,
    batch_size: int = 1000,
    lr: float = 0.001,
    margin: float = 1.0,
    device: str = 'cuda:0',
    save_dir: str = "results/comparison"
):
    """
    运行对比实验

    Args:
        dataset_path: 数据集路径
        embedding_dim: 嵌入维度
        num_epochs: 训练轮数
        batch_size: 批次大小
        lr: 学习率
        margin: margin值
        device: 计算设备
        save_dir: 结果保存目录
    """
    print(f"\n{'='*80}")
    print(f"对比实验开始")
    print(f"数据集: {dataset_path}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)

    # 加载数据
    print("加载数据集...")
    train_data, valid_data, test_data, num_entities, num_relations = load_data(dataset_path)

    # 构建过滤字典
    print("构建过滤字典...")
    filters = build_filters(train_data, valid_data, test_data)

    # 存储所有模型的结果
    all_results = {}

    # ==================== 训练TransE ====================
    print(f"\n{'='*80}")
    print(f"训练TransE模型")
    print(f"{'='*80}\n")

    transe_model = TransE(
        num_entities=num_entities,
        num_relations=num_relations,
        embedding_dim=embedding_dim,
        norm='L1',
        margin=margin,
        is_cuda=(device != 'cpu')
    )

    transe_trainer = BaselineTrainer(
        model=transe_model,
        model_name='TransE',
        dataset_name='CHRONIC',
        num_entities=num_entities,
        num_relations=num_relations,
        device=device,
        lr=lr,
        margin=margin
    )

    # 训练
    transe_trainer.train(
        train_data=train_data,
        valid_data=valid_data,
        filters=filters,
        num_epochs=num_epochs,
        batch_size=batch_size,
        early_stop_patience=10,
        save_dir=os.path.join(save_dir, "checkpoints")
    )

    # 测试
    transe_metrics = transe_trainer.test(
        test_data=test_data,
        filters=filters,
        batch_size=batch_size
    )

    all_results['TransE'] = transe_metrics

    # 保存指标
    save_metrics(
        transe_metrics,
        'TransE',
        'CHRONIC',
        save_dir=save_dir
    )

    # 保存训练日志
    transe_trainer.save_training_log(save_dir=save_dir)

    # ==================== 训练RotatE ====================
    print(f"\n{'='*80}")
    print(f"训练RotatE模型")
    print(f"{'='*80}\n")

    rotate_model = RotatE(
        num_entities=num_entities,
        num_relations=num_relations,
        embedding_dim=embedding_dim,
        margin=margin,
        is_cuda=(device != 'cpu')
    )

    rotate_trainer = BaselineTrainer(
        model=rotate_model,
        model_name='RotatE',
        dataset_name='CHRONIC',
        num_entities=num_entities,
        num_relations=num_relations,
        device=device,
        lr=lr,
        margin=margin
    )

    # 训练
    rotate_trainer.train(
        train_data=train_data,
        valid_data=valid_data,
        filters=filters,
        num_epochs=num_epochs,
        batch_size=batch_size,
        early_stop_patience=10,
        save_dir=os.path.join(save_dir, "checkpoints")
    )

    # 测试
    rotate_metrics = rotate_trainer.test(
        test_data=test_data,
        filters=filters,
        batch_size=batch_size
    )

    all_results['RotatE'] = rotate_metrics

    # 保存指标
    save_metrics(
        rotate_metrics,
        'RotatE',
        'CHRONIC',
        save_dir=save_dir
    )

    # 保存训练日志
    rotate_trainer.save_training_log(save_dir=save_dir)

    # ==================== 加载TKGR-GPRSCL结果 ====================
    # 必须先运行Supercomplex模型训练，生成结果文件
    tkg_result_path = os.path.join(save_dir, "Supercomplex_CHRONIC_metrics.json")
    if os.path.exists(tkg_result_path):
        with open(tkg_result_path, 'r') as f:
            tkg_result = json.load(f)
            all_results['TKGR-GPRSCL'] = tkg_result['metrics']
        print(f"\n已加载TKGR-GPRSCL模型结果: {tkg_result_path}")
    else:
        print(f"\n错误: 未找到TKGR-GPRSCL模型结果文件")
        print(f"请先运行以下命令训练Supercomplex模型:")
        print(f"  cd models")
        print(f"  python learner.py --dataset CHRONIC --model Supercomplex --max_epochs 20")
        print(f"\n然后将生成的评估结果保存到: {tkg_result_path}")
        print(f"格式示例:")
        print(f"""{{
  "model": "Supercomplex",
  "dataset": "CHRONIC",
  "metrics": {{
    "MRR": 0.xxx,
    "Hits@1": 0.xxx,
    "Hits@3": 0.xxx,
    "Hits@10": 0.xxx,
    "num_samples": 14040
  }}
}}""")
        sys.exit(1)

    # ==================== 对比结果 ====================
    print(f"\n{'='*80}")
    print(f"对比实验结果")
    print(f"{'='*80}\n")

    # 打印对比表格
    compare_models(all_results, 'CHRONIC')

    # 生成对比报告
    generate_comparison_report(
        all_results,
        'CHRONIC',
        save_path=os.path.join(save_dir, "comparison_report.md")
    )

    # ==================== 生成可视化图表 ====================
    generate_all_visualizations(
        all_results,
        'CHRONIC',
        save_dir=save_dir
    )

    # 保存完整结果
    complete_results = {
        'dataset': 'CHRONIC',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'config': {
            'embedding_dim': embedding_dim,
            'num_epochs': num_epochs,
            'batch_size': batch_size,
            'learning_rate': lr,
            'margin': margin
        },
        'results': all_results
    }

    with open(os.path.join(save_dir, "complete_results.json"), 'w') as f:
        json.dump(complete_results, f, indent=2)

    print(f"\n对比实验完成！")
    print(f"结果保存在: {save_dir}")

    return all_results


if __name__ == "__main__":
    # 运行对比实验
    results = run_comparison_experiment(
        dataset_path="data/CHRONIC",
        embedding_dim=200,
        num_epochs=50,
        batch_size=1000,
        lr=0.001,
        margin=1.0,
        device='cuda:0' if torch.cuda.is_available() else 'cpu',
        save_dir="results/comparison"
    )
