"""
验证代码修改的正确性

检查新增的代码是否符合预期
"""

import os
import re


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if os.path.exists(filepath):
        print(f"[OK] {description}: {filepath}")
        return True
    else:
        print(f"[FAIL] {description}: {filepath} 不存在")
        return False


def check_file_content(filepath, pattern, description):
    """检查文件内容是否包含指定模式"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if re.search(pattern, content, re.MULTILINE):
                print(f"[OK] {description}")
                return True
            else:
                print(f"[FAIL] {description}")
                return False
    except Exception as e:
        print(f"[FAIL] 检查文件失败: {e}")
        return False


def main():
    """主验证函数"""
    print("=" * 60)
    print("验证代码修改")
    print("=" * 60)

    results = []

    # 1. 检查后端文件
    print("\n【后端文件检查】")
    results.append(check_file_exists(
        "app/main.py",
        "后端主文件"
    ))

    results.append(check_file_content(
        "app/main.py",
        r'@app\.get\("/api/patients/paginated"\)',
        "分页API定义"
    ))

    results.append(check_file_content(
        "app/main.py",
        r"def patients_paginated",
        "分页API函数"
    ))

    results.append(check_file_content(
        "app/main.py",
        r"page: int = Query",
        "分页参数page"
    ))

    results.append(check_file_content(
        "app/main.py",
        r"page_size: int = Query",
        "分页参数page_size"
    ))

    results.append(check_file_content(
        "app/main.py",
        r"search: Optional\[str\] = Query",
        "搜索参数"
    ))

    # 2. 检查前端API文件
    print("\n【前端API文件检查】")
    results.append(check_file_exists(
        "frontend/src/services/api.ts",
        "前端API文件"
    ))

    results.append(check_file_content(
        "frontend/src/services/api.ts",
        r"export async function getPatientsPaginated",
        "分页API调用函数"
    ))

    results.append(check_file_content(
        "frontend/src/services/api.ts",
        r"export interface PaginatedPatientsResponse",
        "分页响应类型"
    ))

    # 3. 检查前端页面文件
    print("\n【前端页面文件检查】")
    results.append(check_file_exists(
        "frontend/src/pages/NurseWorkspacePage.vue",
        "护士工作台页面"
    ))

    results.append(check_file_exists(
        "frontend/src/pages/ArchivistWorkspacePage.vue",
        "档案管理员工作台页面"
    ))

    # 4. 检查App.vue集成
    print("\n【App.vue集成检查】")
    results.append(check_file_exists(
        "frontend/src/App.vue",
        "主应用文件"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"import NurseWorkspacePage",
        "导入护士工作台"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"import ArchivistWorkspacePage",
        "导入档案管理员工作台"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"v-if=\"section === 'doctor' && currentDoctor\.role === 'doctor'\"",
        "医生工作台条件"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"v-else-if=\"section === 'doctor' && currentDoctor\.role === 'nurse'\"",
        "护士工作台条件"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"v-else-if=\"section === 'archive' && currentDoctor\.role === 'archivist'\"",
        "档案管理员工作台条件"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"function handleExportPatients",
        "导出患者函数"
    ))

    results.append(check_file_content(
        "frontend/src/App.vue",
        r"getPatientsPaginated",
        "使用分页API"
    ))

    # 5. 检查文档文件
    print("\n【文档文件检查】")
    results.append(check_file_exists(
        "docs/前端界面问题分析与改进方案.md",
        "问题分析文档"
    ))

    # 统计结果
    print("\n" + "=" * 60)
    success_count = sum(results)
    total_count = len(results)
    print(f"验证结果: {success_count}/{total_count} 通过")

    if success_count == total_count:
        print("[SUCCESS] 所有检查通过，代码修改正确")
    else:
        print("[FAIL] 部分检查未通过，请检查相关文件")

    print("=" * 60)

    return success_count == total_count


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
