"""
基础设施层 - 仓储实现
借鉴CIS的Repository实现
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from ...domain.entities.patient import Patient
from ...domain.interfaces.i_patient_repo import IPatientRepository
from ...domain.value_objects import PatientStatus


class PatientRepository(IPatientRepository):
    """
    患者仓储实现（借鉴CIS的Repository实现）

    实现患者数据访问的具体逻辑
    """

    def __init__(self, db: Session):
        self.db = db

    async def find_by_id(self, patient_id: str) -> Optional[Patient]:
        """根据ID查找"""
        query = """
        SELECT * FROM patients
        WHERE patient_id = :patient_id
        AND zt = '1'
        """
        result = self.db.execute(query, {"patient_id": patient_id})
        row = result.fetchone()
        return Patient.from_orm(row) if row else None

    async def find_by_medical_record_no(self, mr_no: str) -> Optional[Patient]:
        """根据病历号查找"""
        query = """
        SELECT * FROM patients
        WHERE medical_record_no = :mr_no
        AND zt = '1'
        """
        result = self.db.execute(query, {"mr_no": mr_no})
        row = result.fetchone()
        return Patient.from_orm(row) if row else None

    async def find_by_status(
        self,
        status: PatientStatus,
        organize_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Patient]:
        """根据状态查找列表（借鉴CIS的分页查询）"""
        offset = (page - 1) * page_size
        query = """
        SELECT * FROM patients
        WHERE current_status = :status
        AND organize_id = :organize_id
        AND zt = '1'
        ORDER BY create_time DESC
        LIMIT :page_size OFFSET :offset
        """
        result = self.db.execute(
            query,
            {
                "status": status.value,
                "organize_id": organize_id,
                "page_size": page_size,
                "offset": offset
            }
        )
        return [Patient.from_orm(row) for row in result.fetchall()]

    async def search(
        self,
        keyword: str,
        organize_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> List[Patient]:
        """搜索患者（借鉴CIS的模糊查询）"""
        offset = (page - 1) * page_size
        query = """
        SELECT * FROM patients
        WHERE organize_id = :organize_id
        AND zt = '1'
        AND (
            name LIKE :keyword
            OR medical_record_no LIKE :keyword
            OR phone LIKE :keyword
        )
        ORDER BY create_time DESC
        LIMIT :page_size OFFSET :offset
        """
        result = self.db.execute(
            query,
            {
                "organize_id": organize_id,
                "keyword": f"%{keyword}%",
                "page_size": page_size,
                "offset": offset
            }
        )
        return [Patient.from_orm(row) for row in result.fetchall()]

    async def save(self, patient: Patient) -> bool:
        """保存患者"""
        try:
            # 转换为字典
            data = patient.dict()
            # 构建INSERT语句
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{k}" for k in data.keys()])
            query = f"INSERT INTO patients ({columns}) VALUES ({placeholders})"
            self.db.execute(query, data)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"保存患者失败: {e}")
            return False

    async def update(self, patient: Patient) -> bool:
        """更新患者"""
        try:
            data = patient.dict()
            # 构建UPDATE语句
            set_clause = ", ".join([f"{k} = :{k}" for k in data.keys() if k != 'id'])
            query = f"UPDATE patients SET {set_clause} WHERE id = :id"
            self.db.execute(query, data)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            print(f"更新患者失败: {e}")
            return False

    async def count_by_status(
        self,
        status: PatientStatus,
        organize_id: str
    ) -> int:
        """统计某状态的患者数量"""
        query = """
        SELECT COUNT(*) as count
        FROM patients
        WHERE current_status = :status
        AND organize_id = :organize_id
        AND zt = '1'
        """
        result = self.db.execute(
            query,
            {
                "status": status.value,
                "organize_id": organize_id
            }
        )
        row = result.fetchone()
        return row['count'] if row else 0
