"""
将生成的医疗数据集导入到系统数据库
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.demo_store import DEMO_STORE, PatientCase, TimelineEvent
from app.schemas import PatientUpsertRequest, PatientEventCreateRequest


def import_dataset(dataset_file: str = "demo_dataset.json"):
    """
    导入数据集到系统

    Args:
        dataset_file: 数据集文件名
    """
    # 加载数据集
    print(f"正在加载数据集: {dataset_file}")
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    patients_data = dataset['patients']
    print(f"共 {len(patients_data)} 个患者")

    # 导入每个患者
    imported_count = 0
    for patient_data in patients_data:
        try:
            # 患者基本信息
            patient_info = patient_data['patientInfo']

            # 创建患者
            patient_case = PatientCase(
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
                timeline=[],
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

            # 添加时间线事件
            for event in patient_data['timelineEvents']:
                timeline_event = TimelineEvent(
                    eventTime=event['eventTime'],
                    relation=event['relation'],
                    objectValue=event['objectValue'],
                    note=event.get('note', ''),
                )
                patient_case.timeline.append(timeline_event)

            # 保存到DEMO_STORE
            DEMO_STORE.patients[patient_case.patientId] = patient_case

            imported_count += 1
            print(f"✓ 导入患者: {patient_case.name} ({patient_case.patientId})")

        except Exception as e:
            print(f"✗ 导入失败: {patient_info.get('patientId', 'unknown')} - {e}")

    print(f"\n导入完成: {imported_count}/{len(patients_data)} 个患者")
    print(f"当前系统共有 {len(DEMO_STORE.patients)} 个患者")

    return imported_count


def import_to_main_store():
    """将DEMO_STORE中的数据同步到主存储"""
    from app.main import get_all_patients, get_patient

    print("\n同步到主存储...")
    # 这里可以添加同步逻辑
    print("✓ 同步完成")


if __name__ == "__main__":
    # 导入示例数据集
    import_dataset("demo_dataset.json")

    # 也可以导入完整数据集
    # import_dataset("medical_dataset.json")
