"""
领域层 - 诊断领域服务
借鉴CIS的TreatmentDmnService，结合知识图谱推理
"""
from typing import List, Optional
from ..entities.patient import Patient
from ..entities.medical_record import MedicalRecord
from ..value_objects import DiagnosisCode, DiagnosisType


class DiagnosisDomainService:
    """
    诊断领域服务（借鉴CIS的TreatmentDmnService）

    结合知识图谱推理，提供诊断建议
    """

    def __init__(self, knowledge_graph_client):
        """
        初始化

        Args:
            knowledge_graph_client: 知识图谱客户端
        """
        self.kg_client = knowledge_graph_client

    async def get_diagnosis_suggestions(
        self,
        patient: Patient,
        medical_record: MedicalRecord
    ) -> List[DiagnosisCode]:
        """
        获取诊断建议（结合知识图谱）

        Args:
            patient: 患者实体
            medical_record: 病历实体

        Returns:
            诊断建议列表（Top-10）
        """
        # 1. 从知识图谱获取预测
        predictions = await self.kg_client.predict_diagnosis(
            chronic_disease_type=patient.chronic_disease_type,
            chief_complaint=medical_record.chief_complaint,
            present_illness=medical_record.present_illness,
            past_history=medical_record.past_history,
            age=patient.calculate_age(),
            gender=patient.gender
        )

        # 2. 转换为诊断编码
        suggestions = []
        for idx, pred in enumerate(predictions[:10]):
            suggestion = DiagnosisCode(
                code=pred.get('icd_code', f'Z00.{idx}'),
                name=pred.get('diagnosis_name', ''),
                type=DiagnosisType.WESTERN,
                is_main=(idx == 0),  # 第一个为主诊断
                pinyin_code=pred.get('pinyin_code')
            )
            suggestions.append(suggestion)

        return suggestions

    async def validate_diagnosis(
        self,
        diagnosis: DiagnosisCode,
        patient: Patient
    ) -> tuple[bool, str]:
        """
        验证诊断合理性

        Args:
            diagnosis: 诊断编码
            patient: 患者实体

        Returns:
            (是否合理, 原因说明)
        """
        # 1. 检查诊断编码有效性
        if not diagnosis.code or len(diagnosis.code) < 3:
            return False, "诊断编码格式错误"

        # 2. 检查与患者信息匹配度
        # TODO: 实现更详细的验证逻辑

        # 3. 检查诊断互斥关系
        # TODO: 实现诊断互斥检查

        return True, "诊断合理"

    async def get_icd10_info(self, code: str) -> Optional[dict]:
        """
        获取ICD-10诊断信息

        Args:
            code: ICD-10编码

        Returns:
            诊断信息
        """
        # TODO: 从ICD-10数据库查询
        return {
            'code': code,
            'name': '待实现',
            'category': code[0] if code else None
        }

    async def search_diagnosis(
        self,
        keyword: str,
        limit: int = 20
    ) -> List[DiagnosisCode]:
        """
        搜索诊断（支持拼音码、名称）

        Args:
            keyword: 搜索关键词
            limit: 返回数量限制

        Returns:
            诊断列表
        """
        # TODO: 从诊断库搜索
        # 支持拼音码、五笔码、名称搜索
        return []


class PatientDomainService:
    """
    患者领域服务

    处理患者相关的业务逻辑
    """

    def __init__(self, patient_repo):
        self.patient_repo = patient_repo

    async def start_consultation(
        self,
        patient_id: str,
        doctor_code: str
    ) -> Patient:
        """
        开始诊疗（借鉴CIS流程）

        Args:
            patient_id: 患者ID
            doctor_code: 医生编码

        Returns:
            更新后的患者实体
        """
        # 1. 获取患者信息
        patient = await self.patient_repo.find_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")

        # 2. 调用实体的业务方法
        patient.start_consultation(doctor_code)

        # 3. 保存更新
        await self.patient_repo.update(patient)

        return patient

    async def finish_consultation(
        self,
        patient_id: str,
        doctor_code: str,
        diagnosis: str
    ) -> Patient:
        """
        结束诊疗

        Args:
            patient_id: 患者ID
            doctor_code: 医生编码
            diagnosis: 诊断结果

        Returns:
            更新后的患者实体
        """
        patient = await self.patient_repo.find_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")

        patient.finish_consultation(doctor_code, diagnosis)
        await self.patient_repo.update(patient)

        return patient

    async def suspend_consultation(
        self,
        patient_id: str,
        doctor_code: str
    ) -> Patient:
        """挂起诊疗"""
        patient = await self.patient_repo.find_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")

        patient.suspend_consultation(doctor_code)
        await self.patient_repo.update(patient)

        return patient

    async def resume_consultation(
        self,
        patient_id: str,
        doctor_code: str
    ) -> Patient:
        """恢复诊疗"""
        patient = await self.patient_repo.find_by_id(patient_id)
        if not patient:
            raise ValueError("患者不存在")

        patient.resume_consultation(doctor_code)
        await self.patient_repo.update(patient)

        return patient
