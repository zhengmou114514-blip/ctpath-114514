from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "docs" / "assets" / "chronic_model_comparison.svg"

# Use the confirmed report values from prior project analysis/docs instead of
# the failed static-baseline trial files under results/comparison.
CONFIRMED_METRICS = {
    "CTpath / TKGR-GPRSCL": {
        "MRR": 0.3441,
        "Hits@1": 0.2294,
        "Hits@3": 0.4489,
        "Hits@10": 0.5163,
    },
    "RotatE": {
        "MRR": 0.3180,
        "Hits@1": 0.1950,
        "Hits@3": 0.4290,
        "Hits@10": 0.5101,
    },
    "TransE": {
        "MRR": 0.2954,
        "Hits@1": 0.1746,
        "Hits@3": 0.3700,
        "Hits@10": 0.5149,
    },
}

METRICS = ["MRR", "Hits@1", "Hits@3", "Hits@10"]
COLORS = {
    "CTpath / TKGR-GPRSCL": "#0f766e",
    "RotatE": "#2563eb",
    "TransE": "#94a3b8",
}


def chart_y(value: float, chart_top: float, chart_height: float, max_value: float) -> float:
    return chart_top + chart_height - (value / max_value) * chart_height


def make_svg(metrics_by_model: dict[str, dict[str, float]]) -> str:
    width = 1200
    height = 760
    chart_left = 95
    chart_top = 190
    chart_width = 960
    chart_height = 420
    max_value = 0.55
    metric_centers = [210, 440, 670, 900]
    bar_width = 44
    bar_gap = 10
    models = list(metrics_by_model.keys())
    offsets = [-(bar_width + bar_gap), 0, bar_width + bar_gap]

    parts: list[str] = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">',
        "<title id=\"title\">CHRONIC 数据集模型对比图</title>",
        "<desc id=\"desc\">使用已确认的汇报数据，对比 CTpath、RotatE、TransE 在 CHRONIC 数据集上的 MRR、Hits@1、Hits@3、Hits@10。</desc>",
        f'<rect width="{width}" height="{height}" fill="#f4f7fb"/>',
        '<rect x="40" y="40" width="1120" height="680" rx="24" fill="#ffffff" stroke="#d8e0eb"/>',
        '<text x="80" y="96" font-size="28" font-family="Microsoft YaHei, Segoe UI, sans-serif" font-weight="700" fill="#15314b">CHRONIC 数据集模型对比</text>',
    ]

    legend_y = 78
    for index, model_name in enumerate(models):
        y = legend_y + index * 28
        color = COLORS[model_name]
        parts.append(f'<rect x="770" y="{y}" width="16" height="16" rx="3" fill="{color}"/>')
        parts.append(
            f'<text x="796" y="{y + 13}" font-size="14" font-family="Microsoft YaHei, Segoe UI, sans-serif" fill="#446079">{model_name}</text>'
        )

    parts.append(f'<line x1="{chart_left}" y1="{chart_top + chart_height}" x2="{chart_left + chart_width}" y2="{chart_top + chart_height}" stroke="#9db0c3" stroke-width="1.5"/>')
    parts.append(f'<line x1="{chart_left}" y1="{chart_top}" x2="{chart_left}" y2="{chart_top + chart_height}" stroke="#9db0c3" stroke-width="1.5"/>')

    grid_values = [0.55, 0.45, 0.35, 0.25, 0.15, 0.05, 0.0]
    for grid_value in grid_values:
        y = chart_y(grid_value, chart_top, chart_height, max_value)
        label = "0" if grid_value == 0 else f"{grid_value:.2f}"
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_left + chart_width}" y2="{y:.1f}" stroke="#edf2f7"/>')
        parts.append(f'<text x="{chart_left - 42}" y="{y + 5:.1f}" font-size="13" font-family="Microsoft YaHei, Segoe UI, sans-serif" fill="#6d8397">{label}</text>')

    for center, metric_name in zip(metric_centers, METRICS):
        parts.append(f'<text x="{center - 18}" y="{chart_top + chart_height + 36}" font-size="16" font-family="Microsoft YaHei, Segoe UI, sans-serif" font-weight="600" fill="#15314b">{metric_name}</text>')

    for metric_index, metric_name in enumerate(METRICS):
        center = metric_centers[metric_index]
        for model_index, model_name in enumerate(models):
            value = metrics_by_model[model_name][metric_name]
            color = COLORS[model_name]
            x = center + offsets[model_index]
            y = chart_y(value, chart_top, chart_height, max_value)
            bar_height = chart_top + chart_height - y
            parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" rx="8" fill="{color}"/>')
            label_color = "#0f766e" if model_name == "CTpath / TKGR-GPRSCL" else ("#2563eb" if model_name == "RotatE" else "#64748b")
            parts.append(f'<text x="{x + 2}" y="{y - 10:.1f}" font-size="12" font-family="Microsoft YaHei, Segoe UI, sans-serif" fill="{label_color}">{value:.4f}</text>')

    parts.extend(
        [
            '<text x="80" y="650" font-size="18" font-family="Microsoft YaHei, Segoe UI, sans-serif" font-weight="700" fill="#15314b">结论</text>',
            '<text x="80" y="680" font-size="15" font-family="Microsoft YaHei, Segoe UI, sans-serif" fill="#456277">1. CTpath 在 MRR、Hits@1、Hits@3 上均优于两个静态 KG 基线。</text>',
            '<text x="80" y="706" font-size="15" font-family="Microsoft YaHei, Segoe UI, sans-serif" fill="#456277">2. Hits@10 差距较小，但时序建模在关键排序指标上更有优势。</text>',
            "</svg>",
        ]
    )

    return "\n".join(parts)


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(make_svg(CONFIRMED_METRICS), encoding="utf-8")
    print(f"generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
