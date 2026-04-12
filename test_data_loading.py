"""
测试基线模型数据加载功能
"""
import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import torch
import numpy as np
from typing import Tuple

def load_data_with_mapping(dataset_path: str) -> Tuple[torch.LongTensor, ...]:
    """加载包含字符串实体的数据集，构建ID映射"""
    entity2id = {}
    relation2id = {}
    time2id = {}

    def get_or_add(mapping, key):
        if key not in mapping:
            mapping[key] = len(mapping)
        return mapping[key]

    def load_file(filepath):
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 4:
                    s, r, o, t = parts[0], parts[1], parts[2], parts[3]
                    s_id = get_or_add(entity2id, s)
                    r_id = get_or_add(relation2id, r)
                    o_id = get_or_add(entity2id, o)
                    t_id = get_or_add(time2id, t)
                    data.append([s_id, r_id, o_id, t_id])
        return np.array(data, dtype=np.int64)

    train_data = load_file(os.path.join(dataset_path, 'train'))
    valid_data = load_file(os.path.join(dataset_path, 'valid'))
    test_data = load_file(os.path.join(dataset_path, 'test'))

    train_data = torch.from_numpy(train_data)
    valid_data = torch.from_numpy(valid_data)
    test_data = torch.from_numpy(test_data)

    num_entities = len(entity2id)
    num_relations = len(relation2id)

    print(f"Dataset loaded (with string entity mapping):")
    print(f"  Train: {len(train_data)} samples")
    print(f"  Valid: {len(valid_data)} samples")
    print(f"  Test: {len(test_data)} samples")
    print(f"  Entities: {num_entities}")
    print(f"  Relations: {num_relations}")
    print(f"  Timestamps: {len(time2id)}")

    return train_data, valid_data, test_data, num_entities, num_relations

if __name__ == '__main__':
    print("Testing CHRONIC data loading...")
    dataset_path = os.path.join(project_root, 'data', 'CHRONIC')

    train_data, valid_data, test_data, num_entities, num_relations = load_data_with_mapping(dataset_path)

    print(f"\n✅ Test passed!")
    print(f"Train data shape: {train_data.shape}")
    print(f"Sample: {train_data[0]}")
    print(f"Entities: {num_entities}, Relations: {num_relations}")
