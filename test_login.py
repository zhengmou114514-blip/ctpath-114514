#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试不同角色登录API"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_login(username, password):
    """测试登录"""
    print(f"\n测试登录: {username}")
    print("-" * 50)

    try:
        response = requests.post(
            f"{BASE_URL}/api/login",
            json={"username": username, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] 登录成功")
            print(f"  用户名: {data['doctor']['username']}")
            print(f"  姓名: {data['doctor']['name']}")
            print(f"  职称: {data['doctor']['title']}")
            print(f"  部门: {data['doctor']['department']}")
            print(f"  角色: {data['doctor']['role']}")
            return data
        else:
            print(f"[FAIL] 登录失败: {response.status_code}")
            print(f"  错误: {response.text}")
            return None
    except Exception as e:
        print(f"[ERROR] 请求失败: {e}")
        return None

def main():
    print("=" * 60)
    print("测试不同角色登录")
    print("=" * 60)

    # 测试医生登录
    doctor = test_login("demo_clinic", "demo123456")
    if doctor and doctor['doctor']['role'] == 'doctor':
        print("  [OK] 医生角色正确")
    else:
        print("  [FAIL] 医生角色错误")

    # 测试护士登录
    nurse = test_login("demo_nurse", "demo123456")
    if nurse and nurse['doctor']['role'] == 'nurse':
        print("  [OK] 护士角色正确")
    else:
        print("  [FAIL] 护士角色错误")

    # 测试档案管理员登录
    archivist = test_login("demo_archivist", "demo123456")
    if archivist and archivist['doctor']['role'] == 'archivist':
        print("  [OK] 档案管理员角色正确")
    else:
        print("  [FAIL] 档案管理员角色错误")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
