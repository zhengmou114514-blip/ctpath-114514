"""
生成小型示例数据集用于快速测试
"""
import json
from datetime import datetime, timedelta
import random

# 示例患者数据
patients = [
    {
        "patientId": "P000001",
        "name": "张三",
        "age": 65,
        "gender": "男",
        "primaryDisease": "糖尿病",
        "diagnosisDate": "2023-01-15",
        "riskLevel": "中",
        "caseManager": "管理师001"
    },
    {
        "patientId": "P000002",
        "name": "李四",
        "age": 58,
        "gender": "女",
        "primaryDisease": "高血压",
        "diagnosisDate": "2022-06-20",
        "riskLevel": "高",
        "caseManager": "管理师002"
    },
    {
        "patientId": "P000003",
        "name": "王五",
        "age": 72,
        "gender": "男",
        "primaryDisease": "冠心病",
        "diagnosisDate": "2021-03-10",
        "riskLevel": "高",
        "caseManager": "管理师001"
    }
]

# 为每个患者生成时间线事件
for patient in patients:
    events = []
    start_date = datetime.strptime(patient["diagnosisDate"], "%Y-%m-%d")

    # 生成过去6个月的数据
    for month in range(6):
        current_date = start_date + timedelta(days=30 * month)
        date_str = current_date.strftime("%Y-%m-%d")

        # 症状
        if patient["primaryDisease"] == "糖尿病":
            events.append({
                "eventTime": date_str,
                "relation": "症状",
                "objectValue": "多饮(轻度)",
                "note": "患者主诉多饮"
            })
            events.append({
                "eventTime": date_str,
                "relation": "血糖",
                "objectValue": f"{random.uniform(6.0, 9.0):.1f}mmol/L",
                "continuousValue": random.uniform(6.0, 9.0),
                "note": "血糖检查"
            })
        elif patient["primaryDisease"] == "高血压":
            events.append({
                "eventTime": date_str,
                "relation": "症状",
                "objectValue": "头晕(中度)",
                "note": "患者主诉头晕"
            })
            events.append({
                "eventTime": date_str,
                "relation": "收缩压",
                "objectValue": f"{random.randint(130, 160)}mmHg",
                "continuousValue": random.randint(130, 160),
                "note": "血压检查"
            })
        elif patient["primaryDisease"] == "冠心病":
            events.append({
                "eventTime": date_str,
                "relation": "症状",
                "objectValue": "胸闷(中度)",
                "note": "患者主诉胸闷"
            })
            events.append({
                "eventTime": date_str,
                "relation": "心率",
                "objectValue": f"{random.randint(70, 100)}次/分",
                "continuousValue": random.randint(70, 100),
                "note": "心率检查"
            })

        # 治疗
        events.append({
            "eventTime": date_str,
            "relation": "治疗",
            "objectValue": "药物治疗",
            "note": "按时服药"
        })

        # 随访
        events.append({
            "eventTime": date_str,
            "relation": "随访评估",
            "objectValue": "依从性良好",
            "note": "患者依从性良好"
        })

    patient["timelineEvents"] = events
    patient["statistics"] = {
        "totalEvents": len(events),
        "lastVisit": events[-1]["eventTime"] if events else None
    }

# 创建数据集
dataset = {
    "metadata": {
        "generatedAt": datetime.now().isoformat(),
        "totalPatients": len(patients),
        "version": "1.0-demo"
    },
    "patients": patients
}

# 保存
with open('demo_dataset.json', 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=2)

print(f"示例数据集已生成: demo_dataset.json")
print(f"患者数: {len(patients)}")
print(f"总事件数: {sum(len(p['timelineEvents']) for p in patients)}")
