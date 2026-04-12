"""
启动时自动加载医疗数据集
"""
import json
import os
from pathlib import Path
from typing import Dict, List
from datetime import datetime

from .schemas import PatientCase, TimelineEvent


def load_medical_dataset() -> Dict[str, PatientCase]:
    """
    加载医疗数据集

    Returns:
        患者字典 {patientId: PatientCase}
    """
    patients = {}

    # 尝试加载示例数据集
    dataset_files = [
        "demo_dataset.json",
        "medical_dataset.json"
    ]

    for dataset_file in dataset_files:
        if os.path.exists(dataset_file):
            print(f"正在加载数据集: {dataset_file}")
            try:
                with open(dataset_file, 'r', encoding='utf-8') as f:
                    dataset = json.load(f)

                for patient_data in dataset['patients']:
                    patient_info = patient_data['patientInfo']

                    # 创建时间线事件
                    timeline = []
                    for event in patient_data.get('timelineEvents', []):
                        timeline.append(TimelineEvent(
                            eventTime=event['eventTime'],
                            relation=event['relation'],
                            objectValue=event['objectValue'],
                            note=event.get('note', ''),
                        ))

                    # 创建患者
                    patient = PatientCase(
                        patientId=patient_info['patientId'],
                        name=patient_info['name'],
                        age=patient_info['age'],
                        gender=patient_info['gender'],
                        phone=None,
                        primaryDisease=patient_info['primaryDisease'],
                        primaryDoctor="demo_clinic",
                        caseManager=patient_info.get('caseManager', '管理师001'),
                        riskLevel=patient_info['riskLevel'],
                        dataSupport="充分",
                        currentStage="稳定期",
                        encounterStatus="waiting",
                        lastVisit=patient_info['diagnosisDate'],
                        nextVisit=None,
                        timeline=timeline,
                        contactLogs=[],
                        quadruples=[],
                        auditLogs=[],
                        chronicDiseaseType=patient_info['primaryDisease'],
                        diagnosisDate=patient_info['diagnosisDate'],
                        lastDiagnosis=patient_info['primaryDisease'],
                        followupCount=0,
                        alertCount=0,
                        emergencyContactName=None,
                        emergencyContactPhone=None,
                        allergyHistory=None,
                        department="慢病管理门诊",
                    )

                    patients[patient.patientId] = patient

                print(f"✓ 成功加载 {len(patients)} 个患者")
                break  # 成功加载后退出循环

            except Exception as e:
                print(f"✗ 加载失败: {e}")
                continue

    if not patients:
        print("未找到数据集文件，使用默认数据")

    return patients


# 全局变量存储加载的数据
LOADED_PATIENTS: Dict[str, PatientCase] = {}


def init_dataset():
    """初始化数据集"""
    global LOADED_PATIENTS
    LOADED_PATIENTS = load_medical_dataset()
    return LOADED_PATIENTS


def get_loaded_patients() -> Dict[str, PatientCase]:
    """获取已加载的患者数据"""
    return LOADED_PATIENTS
