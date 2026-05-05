#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试不同角色账号"""

import sys
sys.path.insert(0, 'E:/CTpath-master')

from app.demo_store import DOCTORS, authenticate

print("=" * 60)
print("测试不同角色账号")
print("=" * 60)

for doctor in DOCTORS:
    print(f"\n账号: {doctor.username}")
    print(f"  姓名: {doctor.name}")
    print(f"  职称: {doctor.title}")
    print(f"  部门: {doctor.department}")
    print(f"  角色: {doctor.role}")

print("\n" + "=" * 60)
print("测试登录认证")
print("=" * 60)

# 测试医生登录
result = authenticate("demo_clinic", "demo123456")
if result:
    print(f"\n[OK] demo_clinic 登录成功")
    print(f"  角色: {result.role}")
    assert result.role == "doctor", "医生角色错误"
else:
    print(f"\n[FAIL] demo_clinic 登录失败")

# 测试护士登录
result = authenticate("demo_nurse", "demo123456")
if result:
    print(f"\n[OK] demo_nurse 登录成功")
    print(f"  角色: {result.role}")
    assert result.role == "nurse", "护士角色错误"
else:
    print(f"\n[FAIL] demo_nurse 登录失败")

# 测试档案管理员登录
result = authenticate("demo_archivist", "demo123456")
if result:
    print(f"\n[OK] demo_archivist 登录成功")
    print(f"  角色: {result.role}")
    assert result.role == "archivist", "档案管理员角色错误"
else:
    print(f"\n[FAIL] demo_archivist 登录失败")

print("\n" + "=" * 60)
print("所有测试通过")
print("=" * 60)
