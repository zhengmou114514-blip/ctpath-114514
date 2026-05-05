"""
领域层 - 患者实体
借鉴CIS的TreatmentEntity设计
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import Field
from .base_entity import BaseEntity
from ..value_objects import PatientStatus, RiskLevel


class Patient(BaseEntity):
    """
    患者实体（借鉴CIS的就诊实体设计）

    包含：
    - 基本信息（姓名、性别、出生日期等）
    - 联系信息（电话、地址）
    - 就诊信息（病历号、就诊状态、最后就诊时间）
    - 慢病特有字段（慢病类型、风险等级）
    """
    # 基本信息
    patient_id: str = Field(..., description="患者ID")
    name: str = Field(..., description="姓名")
    gender: str = Field(..., description="性别：1男 2女")
    birth_date: date = Field(..., description="出生日期")

    # 证件信息
    id_card_type: Optional[int] = Field(None, description="证件类型")
    id_card_no: Optional[str] = Field(None, description="证件号")

    # 联系信息
    phone: Optional[str] = Field(None, description="联系电话")
    emergency_contact: Optional[str] = Field(None, description="紧急联系人")
    emergency_phone: Optional[str] = Field(None, description="紧急联系电话")
    address: Optional[str] = Field(None, description="地址")

    # 就诊信息（借鉴CIS的冗余字段设计）
    medical_record_no: str = Field(..., description="病历号")
    current_status: PatientStatus = Field(
        default=PatientStatus.WAITING,
        description="当前就诊状态"
    )
    last_visit_time: Optional[datetime] = Field(None, description="最后就诊时间")
    last_diagnosis: Optional[str] = Field(None, description="最后诊断")
    last_doctor_code: Optional[str] = Field(None, description="最后接诊医生")

    # 慢病特有字段
    chronic_disease_type: Optional[str] = Field(None, description="慢病类型")
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="风险等级")
    diagnosis_date: Optional[date] = Field(None, description="确诊日期")
    case_manager: Optional[str] = Field(None, description="病案管理师")

    # 既往史
    allergy_history: Optional[str] = Field(None, description="过敏史")
    past_history: Optional[str] = Field(None, description="既往史")
    family_history: Optional[str] = Field(None, description="家族史")

    def calculate_age(self) -> int:
        """计算年龄"""
        today = date.today()
        age = today.year - self.birth_date.year
        if (today.month, today.day) < (self.birth_date.month, self.birth_date.day):
            age -= 1
        return age

    def start_consultation(self, doctor_code: str):
        """开始诊疗（借鉴CIS状态流转）"""
        if self.current_status != PatientStatus.WAITING:
            raise ValueError(f"患者当前状态为{self.current_status}，无法开始诊疗")

        self.current_status = PatientStatus.CONSULTING
        self.last_doctor_code = doctor_code
        self.modify(doctor_code)

    def finish_consultation(self, doctor_code: str, diagnosis: str):
        """结束诊疗"""
        if self.current_status != PatientStatus.CONSULTING:
            raise ValueError(f"患者当前状态为{self.current_status}，无法结束诊疗")

        self.current_status = PatientStatus.FINISHED
        self.last_visit_time = datetime.now()
        self.last_diagnosis = diagnosis
        self.modify(doctor_code)

    def suspend_consultation(self, doctor_code: str):
        """挂起诊疗"""
        if self.current_status != PatientStatus.CONSULTING:
            raise ValueError(f"患者当前状态为{self.current_status}，无法挂起")

        self.current_status = PatientStatus.SUSPENDED
        self.modify(doctor_code)

    def resume_consultation(self, doctor_code: str):
        """恢复诊疗"""
        if self.current_status != PatientStatus.SUSPENDED:
            raise ValueError(f"患者当前状态为{self.current_status}，无法恢复")

        self.current_status = PatientStatus.CONSULTING
        self.modify(doctor_code)

    def update_risk_level(self, risk_level: RiskLevel, modifier_code: str):
        """更新风险等级"""
        self.risk_level = risk_level
        self.modify(modifier_code)
