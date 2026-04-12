"""
可视化模块 - 生成对比实验结果的可视化图片

使用matplotlib生成高质量的对比图表
"""

import matplotlib.pyplot as plt
import matplotlib
import numpy as np
from typing import Dict, List, Optional
import os

# 设置中文字体支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

# 设置绘图风格
plt.style.use('seaborn-v0_8-darkgrid')


def plot_metrics_comparison(
    results: Dict[str, Dict[str, float]],
    dataset_name: str,
    save_path: str = "results/comparison/metrics_comparison.png",
    figsize: tuple = (12, 6)
):
    """
    绘制所有模型的指标对比柱状图

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
        save_path: 图片保存路径
        figsize: 图片大小
    """
    # 准备数据
    models = list(results.keys())
    metrics_names = ['MRR', 'Hits@1', 'Hits@3', 'Hits@10']

    # 创建数据矩阵
    data = {}
    for metric in metrics_names:
        data[metric] = [results[model].get(metric, 0) for model in models]

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)

    # 设置柱状图参数
    x = np.arange(len(models))
    width = 0.2
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']

    # 绘制柱状图
    for i, (metric, values) in enumerate(data.items()):
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, values, width, label=metric, color=colors[i], alpha=0.8)

        # 在柱状图上添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{value:.3f}',
                ha='center',
                va='bottom',
                fontsize=9,
                fontweight='bold'
            )

    # 设置图表属性
    ax.set_xlabel('模型', fontsize=12, fontweight='bold')
    ax.set_ylabel('指标值', fontsize=12, fontweight='bold')
    ax.set_title(f'{dataset_name}数据集 - 模型性能对比', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11)
    ax.legend(loc='upper right', fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.grid(axis='y', alpha=0.3)

    # 添加背景色
    ax.set_facecolor('#f8f9fa')

    plt.tight_layout()

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"指标对比图已保存: {save_path}")


def plot_radar_chart(
    results: Dict[str, Dict[str, float]],
    dataset_name: str,
    save_path: str = "results/comparison/radar_chart.png",
    figsize: tuple = (10, 10)
):
    """
    绘制雷达图对比所有模型

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
        save_path: 图片保存路径
        figsize: 图片大小
    """
    # 准备数据
    models = list(results.keys())
    metrics = ['MRR', 'Hits@1', 'Hits@3', 'Hits@10']
    num_metrics = len(metrics)

    # 创建角度
    angles = np.linspace(0, 2 * np.pi, num_metrics, endpoint=False).tolist()
    angles += angles[:1]  # 闭合图形

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize, subplot_kw=dict(polar=True))

    # 颜色列表
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']

    # 绘制每个模型的雷达图
    for i, model in enumerate(models):
        values = [results[model].get(metric, 0) for metric in metrics]
        values += values[:1]  # 闭合图形

        ax.plot(angles, values, 'o-', linewidth=2, label=model, color=colors[i % len(colors)])
        ax.fill(angles, values, alpha=0.15, color=colors[i % len(colors)])

    # 设置图表属性
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, fontsize=12, fontweight='bold')
    ax.set_ylim(0, 1.0)
    ax.set_title(f'{dataset_name}数据集 - 模型性能雷达图', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"雷达图已保存: {save_path}")


def plot_improvement_chart(
    results: Dict[str, Dict[str, float]],
    baseline_model: str = 'TransE',
    dataset_name: str = 'CHRONIC',
    save_path: str = "results/comparison/improvement_chart.png",
    figsize: tuple = (10, 6)
):
    """
    绘制改进百分比图（相对于基线模型）

    Args:
        results: 模型名称到指标的映射
        baseline_model: 基线模型名称
        dataset_name: 数据集名称
        save_path: 图片保存路径
        figsize: 图片大小
    """
    if baseline_model not in results:
        print(f"警告: 基线模型 {baseline_model} 不在结果中")
        return

    # 准备数据
    models = [m for m in results.keys() if m != baseline_model]
    metrics = ['MRR', 'Hits@1', 'Hits@3', 'Hits@10']

    # 计算改进百分比
    improvements = {}
    for metric in metrics:
        baseline_value = results[baseline_model].get(metric, 0)
        improvements[metric] = []
        for model in models:
            model_value = results[model].get(metric, 0)
            if baseline_value > 0:
                improvement = (model_value - baseline_value) / baseline_value * 100
            else:
                improvement = 0
            improvements[metric].append(improvement)

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)

    # 设置柱状图参数
    x = np.arange(len(models))
    width = 0.2
    colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']

    # 绘制柱状图
    for i, (metric, values) in enumerate(improvements.items()):
        offset = (i - 1.5) * width
        bars = ax.bar(x + offset, values, width, label=metric, color=colors[i], alpha=0.8)

        # 在柱状图上添加数值标签
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height,
                f'{value:.1f}%',
                ha='center',
                va='bottom' if height >= 0 else 'top',
                fontsize=9,
                fontweight='bold'
            )

    # 添加零线
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)

    # 设置图表属性
    ax.set_xlabel('模型', fontsize=12, fontweight='bold')
    ax.set_ylabel('相对改进 (%)', fontsize=12, fontweight='bold')
    ax.set_title(
        f'{dataset_name}数据集 - 相对于{baseline_model}的改进',
        fontsize=14,
        fontweight='bold',
        pad=20
    )
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=11)
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(axis='y', alpha=0.3)

    # 添加背景色
    ax.set_facecolor('#f8f9fa')

    plt.tight_layout()

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"改进对比图已保存: {save_path}")


def plot_training_curves(
    train_losses: List[float],
    valid_mrrs: List[float],
    model_name: str,
    dataset_name: str,
    save_path: str = "results/comparison/training_curves.png",
    figsize: tuple = (12, 5)
):
    """
    绘制训练曲线（损失和验证MRR）

    Args:
        train_losses: 训练损失列表
        valid_mrrs: 验证MRR列表
        model_name: 模型名称
        dataset_name: 数据集名称
        save_path: 图片保存路径
        figsize: 图片大小
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    epochs = range(1, len(train_losses) + 1)

    # 绘制训练损失
    ax1.plot(epochs, train_losses, 'b-', linewidth=2, label='训练损失')
    ax1.set_xlabel('Epoch', fontsize=11, fontweight='bold')
    ax1.set_ylabel('损失', fontsize=11, fontweight='bold')
    ax1.set_title(f'{model_name} - 训练损失', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_facecolor('#f8f9fa')

    # 绘制验证MRR
    ax2.plot(epochs, valid_mrrs, 'g-', linewidth=2, label='验证MRR')
    ax2.set_xlabel('Epoch', fontsize=11, fontweight='bold')
    ax2.set_ylabel('MRR', fontsize=11, fontweight='bold')
    ax2.set_title(f'{model_name} - 验证MRR', fontsize=12, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)
    ax2.set_facecolor('#f8f9fa')

    plt.suptitle(
        f'{dataset_name}数据集 - {model_name}训练曲线',
        fontsize=14,
        fontweight='bold',
        y=1.02
    )
    plt.tight_layout()

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"训练曲线已保存: {save_path}")


def plot_all_metrics_heatmap(
    results: Dict[str, Dict[str, float]],
    dataset_name: str,
    save_path: str = "results/comparison/metrics_heatmap.png",
    figsize: tuple = (8, 6)
):
    """
    绘制所有指标的热力图

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
        save_path: 图片保存路径
        figsize: 图片大小
    """
    # 准备数据
    models = list(results.keys())
    metrics = ['MRR', 'Hits@1', 'Hits@3', 'Hits@10']

    # 创建数据矩阵
    data = np.array([[results[model].get(metric, 0) for metric in metrics] for model in models])

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)

    # 绘制热力图
    im = ax.imshow(data, cmap='YlGn', aspect='auto', vmin=0, vmax=1)

    # 设置刻度
    ax.set_xticks(np.arange(len(metrics)))
    ax.set_yticks(np.arange(len(models)))
    ax.set_xticklabels(metrics, fontsize=11, fontweight='bold')
    ax.set_yticklabels(models, fontsize=11, fontweight='bold')

    # 旋转x轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # 在每个单元格中显示数值
    for i in range(len(models)):
        for j in range(len(metrics)):
            text = ax.text(
                j, i,
                f'{data[i, j]:.3f}',
                ha="center",
                va="center",
                color="black" if data[i, j] < 0.5 else "white",
                fontsize=10,
                fontweight='bold'
            )

    # 设置标题
    ax.set_title(f'{dataset_name}数据集 - 指标热力图', fontsize=14, fontweight='bold', pad=20)

    # 添加颜色条
    cbar = ax.figure.colorbar(im, ax=ax)
    cbar.ax.set_ylabel('指标值', rotation=-90, va="bottom", fontsize=11, fontweight='bold')

    plt.tight_layout()

    # 保存图片
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"热力图已保存: {save_path}")


def generate_all_visualizations(
    results: Dict[str, Dict[str, float]],
    dataset_name: str,
    save_dir: str = "results/comparison"
):
    """
    生成所有可视化图表

    Args:
        results: 模型名称到指标的映射
        dataset_name: 数据集名称
        save_dir: 保存目录
    """
    print(f"\n{'='*60}")
    print(f"生成可视化图表")
    print(f"{'='*60}\n")

    os.makedirs(save_dir, exist_ok=True)

    # 1. 指标对比柱状图
    plot_metrics_comparison(
        results,
        dataset_name,
        save_path=os.path.join(save_dir, "metrics_comparison.png")
    )

    # 2. 雷达图
    plot_radar_chart(
        results,
        dataset_name,
        save_path=os.path.join(save_dir, "radar_chart.png")
    )

    # 3. 改进百分比图
    if 'TransE' in results:
        plot_improvement_chart(
            results,
            baseline_model='TransE',
            dataset_name=dataset_name,
            save_path=os.path.join(save_dir, "improvement_chart.png")
        )

    # 4. 热力图
    plot_all_metrics_heatmap(
        results,
        dataset_name,
        save_path=os.path.join(save_dir, "metrics_heatmap.png")
    )

    print(f"\n所有可视化图表已生成！")
    print(f"保存目录: {save_dir}")
    print(f"生成的图表:")
    print(f"  - metrics_comparison.png  (指标对比柱状图)")
    print(f"  - radar_chart.png        (雷达图)")
    print(f"  - improvement_chart.png  (改进百分比图)")
    print(f"  - metrics_heatmap.png    (热力图)")
