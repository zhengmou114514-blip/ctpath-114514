"""
时序基线模型训练脚本

在CHRONIC数据集上训练TTransE、TComplEx、TRotatE模型
"""

import os
import sys
import torch
import argparse
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.baseline import TTransE, TComplEx, TRotatE
from models.baseline.tkg_trainer import (
    TKGTrainer,
    load_tkg_data,
    build_tkg_filters
)


def main():
    parser = argparse.ArgumentParser(description='Train temporal KG baseline models')
    parser.add_argument('--model', type=str, required=True, choices=['TTransE', 'TComplEx', 'TRotatE'],
                        help='Model name')
    parser.add_argument('--dataset', type=str, default='CHRONIC',
                        help='Dataset name')
    parser.add_argument('--data_path', type=str, default='data/CHRONIC',
                        help='Dataset path')
    parser.add_argument('--dim', type=int, default=200,
                        help='Embedding dimension')
    parser.add_argument('--lr', type=float, default=0.001,
                        help='Learning rate')
    parser.add_argument('--margin', type=float, default=1.0,
                        help='Margin for loss')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Number of epochs')
    parser.add_argument('--batch_size', type=int, default=1000,
                        help='Batch size')
    parser.add_argument('--num_neg', type=int, default=1,
                        help='Number of negative samples')
    parser.add_argument('--device', type=str, default='cuda:0',
                        help='Device')
    parser.add_argument('--save_dir', type=str, default='models/checkpoints/baselines',
                        help='Directory to save models')

    args = parser.parse_args()

    print(f"Training {args.model} on {args.dataset}")
    print(f"Arguments: {args}")

    # 检查CUDA
    if args.device.startswith('cuda') and not torch.cuda.is_available():
        print("CUDA not available, using CPU")
        args.device = 'cpu'

    # 加载数据
    print("Loading data...")
    train_data, valid_data, test_data, num_entities, num_relations, num_timestamps = \
        load_tkg_data(args.data_path)

    print(f"Entities: {num_entities}, Relations: {num_relations}, Timestamps: {num_timestamps}")
    print(f"Train: {len(train_data)}, Valid: {len(valid_data)}, Test: {len(test_data)}")

    # 构建过滤字典
    print("Building filters...")
    filters = build_tkg_filters(train_data, valid_data, test_data)

    # 创建模型
    print("Creating model...")
    if args.model == 'TTransE':
        model = TTransE(
            num_entities=num_entities,
            num_relations=num_relations,
            num_timestamps=num_timestamps,
            embedding_dim=args.dim,
            margin=args.margin,
            is_cuda=args.device.startswith('cuda')
        )
    elif args.model == 'TComplEx':
        model = TComplEx(
            num_entities=num_entities,
            num_relations=num_relations,
            num_timestamps=num_timestamps,
            embedding_dim=args.dim,
            margin=args.margin,
            is_cuda=args.device.startswith('cuda')
        )
    elif args.model == 'TRotatE':
        model = TRotatE(
            num_entities=num_entities,
            num_relations=num_relations,
            num_timestamps=num_timestamps,
            embedding_dim=args.dim,
            margin=args.margin,
            is_cuda=args.device.startswith('cuda')
        )

    # 创建训练器
    trainer = TKGTrainer(
        model=model,
        model_name=args.model,
        dataset_name=args.dataset,
        num_entities=num_entities,
        num_relations=num_relations,
        num_timestamps=num_timestamps,
        device=args.device,
        lr=args.lr,
        margin=args.margin,
        num_neg=args.num_neg
    )

    # 训练
    save_path = os.path.join(
        args.save_dir,
        args.dataset,
        f"{args.model}_{args.dim}d.pt"
    )

    print("Training...")
    best_metrics = trainer.train(
        train_data=train_data,
        valid_data=valid_data,
        filters=filters,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        save_path=save_path,
        early_stop_patience=10
    )

    print(f"\nBest validation metrics:")
    print(f"MRR: {best_metrics['mrr']:.4f}")
    print(f"Hits@1: {best_metrics['hits@1']:.4f}")
    print(f"Hits@3: {best_metrics['hits@3']:.4f}")
    print(f"Hits@10: {best_metrics['hits@10']:.4f}")

    # 测试
    print("\nTesting on test set...")
    trainer.load_model(save_path)
    test_metrics = trainer.evaluate(test_data, filters)

    print(f"\nTest metrics:")
    print(f"MRR: {test_metrics['mrr']:.4f}")
    print(f"Hits@1: {test_metrics['hits@1']:.4f}")
    print(f"Hits@3: {test_metrics['hits@3']:.4f}")
    print(f"Hits@10: {test_metrics['hits@10']:.4f}")

    # 保存结果
    results = {
        'model': args.model,
        'dataset': args.dataset,
        'dim': args.dim,
        'lr': args.lr,
        'margin': args.margin,
        'epochs': args.epochs,
        'best_valid_metrics': best_metrics,
        'test_metrics': test_metrics,
        'timestamp': datetime.now().isoformat()
    }

    results_path = os.path.join(
        'results',
        args.dataset,
        f"{args.model}_results.json"
    )
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to {results_path}")


if __name__ == '__main__':
    main()
