"""
领域层 - 值对象
借鉴CIS的ICD-10诊断编码设计
"""
from pydantic import BaseModel, validator, Field
from enum import Enum
from typing import Optional


class DiagnosisType(str, Enum):
    """诊断类型"""
    WESTERN = "western"  # 西医
    TCM = "tcm"  # 中医


class PatientStatus(str, Enum):
    """患者就诊状态（借鉴CIS状态流转）"""
    WAITING = "waiting"  # 待就诊
    CONSULTING = "consulting"  # 就诊中
    FINISHED = "finished"  # 已就诊
    SUSPENDED = "suspended"  # 挂起


class RiskLevel(int, Enum):
    """风险等级"""
    LOW = 0  # 低风险
    MEDIUM = 1  # 中风险
    HIGH = 2  # 高风险


class DiagnosisCode(BaseModel):
    """
    诊断编码值对象（借鉴CIS的ICD-10编码）

    包含：
    - ICD-10编码
    - 诊断名称
    - 诊断类型（西医/中医）
    - 是否主诊断
    - 拼音码（便于搜索）
    """
    code: str = Field(..., description="ICD-10编码")
    name: str = Field(..., description="诊断名称")
    type: DiagnosisType = Field(default=DiagnosisType.WESTERN, description="诊断类型")
    is_main: bool = Field(default=False, description="是否主诊断")
    pinyin_code: Optional[str] = Field(None, description="拼音码")

    @validator('code')
    def validate_icd10(cls, v):
        """验证ICD-10编码格式"""
        if not v or len(v) < 3:
            raise ValueError("ICD-10编码格式错误")
        return v.upper()

    class Config:
        frozen = True  # 不可变（值对象特性）


class PrescriptionType(str, Enum):
    """处方类型"""
    WESTERN_MEDICINE = "western"  # 西药
    CHINESE_HERBAL = "herbal"  # 中草药
    TREATMENT = "treatment"  # 治疗项目


class TemplateScope(str, Enum):
    """模板范围（借鉴CIS三级模板）"""
    PERSONAL = "personal"  # 个人模板
    DEPARTMENT = "department"  # 科室模板
    HOSPITAL = "hospital"  # 医院模板
