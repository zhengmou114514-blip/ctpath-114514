"""
领域层 - 仓储接口
借鉴CIS的IRepository设计
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.patient import Patient
from ..value_objects import PatientStatus


class IPatientRepository(ABC):
    """
    患者仓储接口（借鉴CIS的IRepository设计）

    定义患者数据访问的抽象接口
    """

    @abstractmethod
    async def find_by_id(self, patient_id: str) -> Optional[Patient]:
        """根据ID查找患者"""
        pass

    @abstractmethod
    async def find_by_medical_record_no(self, mr_no: str) -> Optional[Patient]:
        """根据病历号查找患者"""
        pass

    @abstractmethod
    async def find_by_status(
        self,
        status: PatientStatus,
        organize_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Patient]:
        """根据状态查找患者列表（分页）"""
        pass

    @abstractmethod
    async def search(
        self,
        keyword: str,
        organize_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Patient]:
        """搜索患者（姓名、病历号、手机号）"""
        pass

    @abstractmethod
    async def save(self, patient: Patient) -> bool:
        """保存患者"""
        pass

    @abstractmethod
    async def update(self, patient: Patient) -> bool:
        """更新患者"""
        pass

    @abstractmethod
    async def count_by_status(
        self,
        status: PatientStatus,
        organize_id: str
    ) -> int:
        """统计某状态的患者数量"""
        pass
