"""
医疗场景数据集生成器
生成符合慢性病管理实际场景的数据集
"""
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class MedicalDatasetGenerator:
    """医疗数据集生成器"""

    def __init__(self):
        # 慢性病类型
        self.chronic_diseases = [
            "糖尿病",
            "高血压",
            "冠心病",
            "慢性肾病",
            "慢阻肺",
            "脑卒中后遗症"
        ]

        # 症状和体征
        self.symptoms = {
            "糖尿病": ["多饮", "多尿", "多食", "体重下降", "乏力", "视力模糊"],
            "高血压": ["头痛", "头晕", "心悸", "耳鸣", "失眠", "记忆力减退"],
            "冠心病": ["胸痛", "胸闷", "心悸", "气短", "乏力", "出汗"],
            "慢性肾病": ["水肿", "乏力", "食欲不振", "恶心", "贫血", "高血压"],
            "慢阻肺": ["咳嗽", "咳痰", "气短", "胸闷", "乏力", "呼吸困难"],
            "脑卒中后遗症": ["偏瘫", "语言障碍", "吞咽困难", "认知障碍", "情绪障碍", "感觉障碍"]
        }

        # 检查指标范围
        self.lab_ranges = {
            "血糖": {"min": 3.9, "max": 11.1, "unit": "mmol/L", "normal": [3.9, 6.1]},
            "糖化血红蛋白": {"min": 4.0, "max": 12.0, "unit": "%", "normal": [4.0, 6.0]},
            "收缩压": {"min": 90, "max": 180, "unit": "mmHg", "normal": [90, 140]},
            "舒张压": {"min": 60, "max": 110, "unit": "mmHg", "normal": [60, 90]},
            "BMI": {"min": 18.5, "max": 35.0, "unit": "kg/m²", "normal": [18.5, 24.0]},
            "心率": {"min": 60, "max": 120, "unit": "次/分", "normal": [60, 100]},
            "血肌酐": {"min": 44, "max": 354, "unit": "μmol/L", "normal": [44, 133]},
            "eGFR": {"min": 15, "max": 120, "unit": "ml/min", "normal": [90, 120]},
        }

        # 治疗措施
        self.treatments = {
            "糖尿病": ["口服降糖药", "胰岛素注射", "饮食控制", "运动治疗", "血糖监测"],
            "高血压": ["降压药", "利尿剂", "低盐饮食", "运动治疗", "血压监测"],
            "冠心病": ["抗血小板药", "他汀类药", "β受体阻滞剂", "冠脉造影", "支架植入"],
            "慢性肾病": ["降压药", "降糖药", "低蛋白饮食", "透析", "肾移植"],
            "慢阻肺": ["支气管扩张剂", "糖皮质激素", "氧疗", "肺康复训练", "戒烟"],
            "脑卒中后遗症": ["抗血小板药", "康复训练", "物理治疗", "语言训练", "心理治疗"]
        }

        # 并发症
        self.complications = {
            "糖尿病": ["糖尿病肾病", "糖尿病视网膜病变", "糖尿病足", "周围神经病变", "心血管病变"],
            "高血压": ["高血压心脏病", "高血压肾病", "脑卒中", "视网膜病变", "动脉硬化"],
            "冠心病": ["心肌梗死", "心力衰竭", "心律失常", "心源性休克", "猝死"],
            "慢性肾病": ["贫血", "骨矿物质代谢异常", "心血管疾病", "电解质紊乱", "尿毒症"],
            "慢阻肺": ["肺源性心脏病", "呼吸衰竭", "自发性气胸", "肺部感染", "睡眠呼吸障碍"],
            "脑卒中后遗症": ["吸入性肺炎", "压疮", "深静脉血栓", "抑郁", "癫痫"]
        }

    def generate_patient(
        self,
        patient_id: str,
        age: int,
        gender: str,
        primary_disease: str,
        diagnosis_date: str
    ) -> Dict[str, Any]:
        """生成患者基本信息"""
        return {
            "patientId": patient_id,
            "name": f"患者{patient_id[-4:]}",
            "age": age,
            "gender": gender,  # "男" or "女"
            "primaryDisease": primary_disease,
            "diagnosisDate": diagnosis_date,
            "riskLevel": random.choice(["低", "中", "高"]),
            "caseManager": f"管理师{random.randint(1, 10):03d}"
        }

    def generate_timeline_events(
        self,
        patient_id: str,
        primary_disease: str,
        diagnosis_date: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """
        生成时间线事件

        Args:
            patient_id: 患者ID
            primary_disease: 主要疾病
            diagnosis_date: 确诊日期
            months: 生成多少个月的数据
        """
        events = []
        start_date = datetime.strptime(diagnosis_date, "%Y-%m-%d")

        for month in range(months):
            current_date = start_date + timedelta(days=30 * month)
            current_date_str = current_date.strftime("%Y-%m-%d")

            # 1. 症状记录（每月1-2次）
            num_symptoms = random.randint(1, 2)
            for _ in range(num_symptoms):
                symptom = random.choice(self.symptoms[primary_disease])
                severity = random.choice(["轻度", "中度", "重度"])
                events.append({
                    "eventTime": current_date_str,
                    "relation": "症状",
                    "objectValue": f"{symptom}({severity})",
                    "note": f"患者主诉{symptom}，程度{severity}"
                })

            # 2. 检查指标（每月1次）
            for indicator, ranges in self.lab_ranges.items():
                # 根据风险等级调整指标值
                value = random.uniform(ranges["min"], ranges["max"])
                # 50%概率在正常范围内
                if random.random() < 0.5:
                    value = random.uniform(ranges["normal"][0], ranges["normal"][1])

                events.append({
                    "eventTime": current_date_str,
                    "relation": indicator,
                    "objectValue": f"{value:.1f}{ranges['unit']}",
                    "continuousValue": value,
                    "note": f"{indicator}检查结果"
                })

            # 3. 治疗措施（每月2-3次）
            num_treatments = random.randint(2, 3)
            selected_treatments = random.sample(
                self.treatments[primary_disease],
                min(num_treatments, len(self.treatments[primary_disease]))
            )
            for treatment in selected_treatments:
                events.append({
                    "eventTime": current_date_str,
                    "relation": "治疗",
                    "objectValue": treatment,
                    "note": f"执行{treatment}治疗"
                })

            # 4. 并发症（每3个月检查一次）
            if month % 3 == 0:
                # 20%概率出现并发症
                if random.random() < 0.2:
                    complication = random.choice(self.complications[primary_disease])
                    events.append({
                        "eventTime": current_date_str,
                        "relation": "并发症",
                        "objectValue": complication,
                        "note": f"发现并发症：{complication}"
                    })

            # 5. 随访评估（每月1次）
            compliance = random.choice(["良好", "一般", "差"])
            events.append({
                "eventTime": current_date_str,
                "relation": "随访评估",
                "objectValue": f"依从性{compliance}",
                "note": f"患者治疗依从性{compliance}"
            })

        # 按时间排序
        events.sort(key=lambda x: x["eventTime"])
        return events

    def generate_dataset(
        self,
        num_patients: int = 100,
        output_file: str = "medical_dataset.json"
    ) -> Dict[str, Any]:
        """
        生成完整数据集

        Args:
            num_patients: 患者数量
            output_file: 输出文件名
        """
        dataset = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "totalPatients": num_patients,
                "version": "1.0"
            },
            "patients": []
        }

        for i in range(num_patients):
            patient_id = f"P{str(i + 1).zfill(6)}"

            # 随机生成患者信息
            age = random.randint(40, 80)
            gender = random.choice(["男", "女"])
            primary_disease = random.choice(self.chronic_diseases)

            # 确诊日期（过去1-5年）
            years_ago = random.randint(1, 5)
            diagnosis_date = (datetime.now() - timedelta(days=365 * years_ago)).strftime("%Y-%m-%d")

            # 生成患者基本信息
            patient = self.generate_patient(
                patient_id, age, gender, primary_disease, diagnosis_date
            )

            # 生成时间线事件（过去12个月）
            events = self.generate_timeline_events(
                patient_id, primary_disease, diagnosis_date, months=12
            )

            # 组合数据
            patient_data = {
                "patientInfo": patient,
                "timelineEvents": events,
                "statistics": {
                    "totalEvents": len(events),
                    "eventTypes": self._count_event_types(events),
                    "lastVisit": events[-1]["eventTime"] if events else None
                }
            }

            dataset["patients"].append(patient_data)

        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)

        print(f"数据集已生成: {output_file}")
        print(f"总患者数: {num_patients}")
        print(f"总事件数: {sum(len(p['timelineEvents']) for p in dataset['patients'])}")

        return dataset

    def _count_event_types(self, events: List[Dict]) -> Dict[str, int]:
        """统计事件类型"""
        type_counts = {}
        for event in events:
            relation = event["relation"]
            type_counts[relation] = type_counts.get(relation, 0) + 1
        return type_counts


if __name__ == "__main__":
    # 生成数据集
    generator = MedicalDatasetGenerator()

    # 生成100个患者的数据
    dataset = generator.generate_dataset(
        num_patients=100,
        output_file="medical_dataset.json"
    )

    # 打印示例
    print("\n示例患者数据:")
    print(json.dumps(dataset["patients"][0], ensure_ascii=False, indent=2)[:500])
