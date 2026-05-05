"""
领域层 - 实体基类
借鉴CIS的IEntity设计，实现审计字段和软删除
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BaseEntity(BaseModel):
    """
    实体基类（借鉴CIS的IEntity设计）

    包含：
    - 主键ID
    - 组织ID（多租户支持）
    - 审计字段（创建时间、创建人、修改时间、修改人）
    - 软删除标记（zt: 1有效 0无效）
    """
    id: str = Field(..., description="主键ID")
    organize_id: str = Field(..., description="组织ID（多租户）")

    # 审计字段
    create_time: datetime = Field(default_factory=datetime.now, description="创建时间")
    creator_code: str = Field(..., description="创建人编码")
    last_modify_time: Optional[datetime] = Field(None, description="最后修改时间")
    last_modifier_code: Optional[str] = Field(None, description="最后修改人编码")

    # 软删除标记
    zt: str = Field(default="1", description="状态：1有效 0无效")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def create(self, creator_code: str, organize_id: str = "org001"):
        """创建时设置"""
        self.creator_code = creator_code
        self.organize_id = organize_id
        self.create_time = datetime.now()
        self.zt = "1"

    def modify(self, modifier_code: str):
        """修改时设置"""
        self.last_modify_time = datetime.now()
        self.last_modifier_code = modifier_code

    def delete(self):
        """软删除"""
        self.zt = "0"

    def is_valid(self) -> bool:
        """是否有效"""
        return self.zt == "1"
