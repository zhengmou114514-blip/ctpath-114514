"""
领域层 - 病历实体
借鉴CIS的MedicalRecordEntity设计
"""
from datetime import datetime
from typing import Optional, List
from pydantic import Field
from .base_entity import BaseEntity
from ..value_objects import DiagnosisCode


class MedicalRecord(BaseEntity):
    """
    病历实体（借鉴CIS病历表设计）

    包含：
    - 关联信息（患者ID、就诊ID、病历号）
    - 病历内容（主诉、现病史、既往史等）
    - 诊断信息（西医诊断、中医诊断）
    - 慢病特有（慢病评估、随访计划）
    """
    # 关联信息
    record_id: str = Field(..., description="病历ID")
    patient_id: str = Field(..., description="患者ID")
    visit_id: str = Field(..., description="就诊ID")
    medical_record_no: str = Field(..., description="病历号")

    # 就诊信息
    visit_date: datetime = Field(default_factory=datetime.now, description="就诊日期")
    department: Optional[str] = Field(None, description="科室")
    doctor_code: Optional[str] = Field(None, description="医生编码")
    doctor_name: Optional[str] = Field(None, description="医生姓名")

    # 病历内容（借鉴CIS字段）
    chief_complaint: str = Field(..., description="主诉")
    present_illness: str = Field(..., description="现病史")
    past_history: Optional[str] = Field(None, description="既往史")
    personal_history: Optional[str] = Field(None, description="个人史")
    family_history: Optional[str] = Field(None, description="家族史")
    physical_exam: Optional[str] = Field(None, description="体格检查")
    auxiliary_exam: Optional[str] = Field(None, description="辅助检查")
    treatment_plan: Optional[str] = Field(None, description="处理方案")

    # 诊断信息
    western_diagnosis: Optional[str] = Field(None, description="西医诊断")
    western_diagnosis_code: Optional[str] = Field(None, description="西医诊断编码")
    tcm_diagnosis: Optional[str] = Field(None, description="中医诊断")
    tcm_diagnosis_code: Optional[str] = Field(None, description="中医诊断编码")

    # 诊断列表（结构化）
    diagnoses: Optional[List[DiagnosisCode]] = Field(None, description="诊断列表")

    # 慢病特有
    chronic_assessment: Optional[str] = Field(None, description="慢病评估")
    risk_factors: Optional[str] = Field(None, description="危险因素")
    follow_up_plan: Optional[str] = Field(None, description="随访计划")
    next_follow_up_date: Optional[datetime] = Field(None, description="下次随访日期")

    # 状态
    record_status: str = Field(default="draft", description="病历状态：draft草稿 submitted已提交")
    submit_time: Optional[datetime] = Field(None, description="提交时间")

    def submit(self, doctor_code: str):
        """提交病历"""
        if self.record_status == "submitted":
            raise ValueError("病历已提交，不能重复提交")

        self.record_status = "submitted"
        self.submit_time = datetime.now()
        self.modify(doctor_code)

    def is_draft(self) -> bool:
        """是否草稿"""
        return self.record_status == "draft"

    def add_diagnosis(self, diagnosis: DiagnosisCode):
        """添加诊断"""
        if self.diagnoses is None:
            self.diagnoses = []

        # 如果是主诊断，清除其他主诊断标记
        if diagnosis.is_main:
            for d in self.diagnoses:
                d.is_main = False

        self.diagnoses.append(diagnosis)

    def get_main_diagnosis(self) -> Optional[DiagnosisCode]:
        """获取主诊断"""
        if not self.diagnoses:
            return None

        for d in self.diagnoses:
            if d.is_main:
                return d

        return self.diagnoses[0] if self.diagnoses else None


class MedicalRecordTemplate(BaseEntity):
    """
    病历模板实体（借鉴CIS模板设计）

    包含：
    - 模板基本信息
    - 模板内容
    - 适用范围（个人/科室/医院）
    """
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    template_scope: str = Field(..., description="模板范围：personal/department/hospital")

    # 适用范围
    department_code: Optional[str] = Field(None, description="科室编码（科室模板）")
    creator_code: str = Field(..., description="创建人编码")

    # 模板内容
    chief_complaint: Optional[str] = Field(None, description="主诉模板")
    present_illness: Optional[str] = Field(None, description="现病史模板")
    past_history: Optional[str] = Field(None, description="既往史模板")
    physical_exam: Optional[str] = Field(None, description="体格检查模板")
    treatment_plan: Optional[str] = Field(None, description="处理方案模板")

    # 诊断模板
    default_diagnosis: Optional[str] = Field(None, description="默认诊断")

    # 使用统计
    use_count: int = Field(default=0, description="使用次数")

    def increment_use_count(self):
        """增加使用次数"""
        self.use_count += 1
