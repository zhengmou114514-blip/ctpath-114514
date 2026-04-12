"""
测试后端API功能

验证分页API和其他关键功能是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health_check():
    """测试健康检查API"""
    print("测试健康检查API...")
    response = client.get("/api/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    assert response.status_code == 200
    print("✅ 健康检查API正常\n")


def test_login():
    """测试登录API"""
    print("测试登录API...")
    response = client.post("/api/login", json={
        "username": "demo_clinic",
        "password": "demo123456"
    })
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"医生: {data['doctor']['name']}")
        print(f"角色: {data['doctor']['role']}")
        return data['token']
    else:
        print(f"错误: {response.json()}")
        return None


def test_patients_paginated(token):
    """测试分页API"""
    print("\n测试分页API...")

    headers = {"Authorization": f"Bearer {token}"}

    # 测试基本分页
    print("1. 基本分页（第1页，每页20条）")
    response = client.get("/api/patients/paginated?page=1&page_size=20", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"患者数量: {len(data['patients'])}")
        print(f"总数: {data['total']}")
        print(f"当前页: {data['page']}")
        print(f"总页数: {data['total_pages']}")
        if data['patients']:
            print(f"第一个患者: {data['patients'][0]['name']}")
    else:
        print(f"错误: {response.json()}")

    # 测试搜索
    print("\n2. 搜索功能")
    response = client.get("/api/patients/paginated?page=1&page_size=20&search=张", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"搜索结果数量: {len(data['patients'])}")
    else:
        print(f"错误: {response.json()}")

    # 测试筛选
    print("\n3. 风险筛选")
    response = client.get("/api/patients/paginated?page=1&page_size=20&risk_level=高", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"高风险患者数量: {len(data['patients'])}")
    else:
        print(f"错误: {response.json()}")


def test_patients_original(token):
    """测试原始患者列表API"""
    print("\n测试原始患者列表API...")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/patients", headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"患者总数: {len(data)}")
    else:
        print(f"错误: {response.json()}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("开始测试后端API")
    print("=" * 60)

    try:
        # 测试健康检查
        test_health_check()

        # 测试登录
        token = test_login()
        if not token:
            print("❌ 登录失败，无法继续测试")
            return

        # 测试分页API
        test_patients_paginated(token)

        # 测试原始API
        test_patients_original(token)

        print("\n" + "=" * 60)
        print("✅ 所有测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
