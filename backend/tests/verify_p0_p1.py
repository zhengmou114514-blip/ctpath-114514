"""
快速验证脚本 - 验证P0和P1任务完成情况
"""

import os
import sys

def check_files(file_list, task_name):
    """检查文件是否存在"""
    print(f"\n{task_name}文件检查:")
    all_exist = True
    for f in file_list:
        if os.path.exists(f):
            size = os.path.getsize(f) if os.path.isfile(f) else 0
            print(f"  [OK] {f} ({size} bytes)")
        else:
            print(f"  [MISS] {f} - 缺失")
            all_exist = False
    return all_exist

def main():
    print("="*70)
    print("P0和P1任务完成情况验证")
    print("="*70)
    
    # 检查P0文件
    p0_files = [
        "models/baseline/__init__.py",
        "models/baseline/transe.py",
        "models/baseline/rotate.py",
        "models/baseline/trainer.py",
        "models/evaluator.py",
        "models/visualization.py",
        "run_comparison.py",
        "test_visualization.py",
        "docs/对比实验与数据适用性说明.md"
    ]
    
    p0_ok = check_files(p0_files, "P0（对比实验）")
    
    # 检查P1文件
    p1_files = [
        "app/services/suggestion_service.py",
        "app/api/suggestions.py"
    ]
    
    p1_ok = check_files(p1_files, "P1（诊疗建议）")
    
    # 检查文档文件
    doc_files = [
        ".codeartsdoer/specs/chronic_treatment/spec.md",
        ".codeartsdoer/specs/chronic_treatment/design.md",
        ".codeartsdoer/specs/chronic_treatment/tasks.md",
        ".codeartsdoer/specs/chronic_treatment/code_review_report.md",
        ".codeartsdoer/specs/chronic_treatment/dataset_selection_guide.md"
    ]
    
    doc_ok = check_files(doc_files, "文档")
    
    # 检查可视化结果
    print("\n可视化结果检查:")
    viz_dir = "results/comparison_test"
    if os.path.exists(viz_dir):
        viz_files = os.listdir(viz_dir)
        for f in viz_files:
            if f.endswith('.png'):
                size = os.path.getsize(os.path.join(viz_dir, f)) / 1024
                print(f"  [OK] {f} ({size:.1f}KB)")
    else:
        print(f"  [WARN] 可视化结果未生成，请运行: python test_visualization.py")
    
    # 统计代码行数
    print("\n代码统计:")
    total_lines = 0
    code_files = p0_files + p1_files
    for f in code_files:
        if os.path.exists(f) and os.path.isfile(f):
            with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                lines = len(file.readlines())
                total_lines += lines
    
    print(f"  总代码行数: {total_lines} 行")
    print(f"  文档文件: {len(doc_files)} 个")
    print(f"  代码文件: {len(code_files)} 个")
    
    # 总结
    print("\n" + "="*70)
    print("验证总结:")
    print("="*70)
    
    if p0_ok and p1_ok and doc_ok:
        print("[OK] 所有文件检查通过！")
        print("\n下一步操作:")
        print("1. 运行可视化测试: python test_visualization.py")
        print("2. 查看图片: explorer results\\comparison_test")
        print("3. 启动API服务: python -m uvicorn app.main:app --reload")
        print("4. 访问API文档: http://localhost:8000/docs")
    else:
        print("[WARN] 部分文件缺失，请检查")
    
    print("="*70)

if __name__ == "__main__":
    main()
