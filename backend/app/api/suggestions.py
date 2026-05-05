"""
诊疗建议API端点
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..services.suggestion_service import SuggestionService, Suggestion


router = APIRouter(prefix="/api/v1/suggestions", tags=["suggestions"])

# 初始化服务
suggestion_service = SuggestionService()


class SuggestionRequest(BaseModel):
    """建议请求"""
    prediction_id: str = Field(..., description="预测结果ID")
    predictions: List[dict] = Field(default_factory=list, description="真实预测结果")
    patient_allergies: List[str] = Field(default=[], description="患者过敏史")
    current_medications: List[str] = Field(default=[], description="当前用药")


class SuggestionResponse(BaseModel):
    """建议响应"""
    suggestion_id: str
    prediction_id: str
    suggestions: List[dict]
    generated_at: str


class PredictionInput(BaseModel):
    """预测输入（用于人工校验）"""
    entity: str
    confidence: float = Field(..., ge=0, le=1)


@router.post("/generate", response_model=SuggestionResponse)
async def generate_suggestions(request: SuggestionRequest):
    """
    生成诊疗建议
    
    需要先通过预测API获取预测结果，然后使用预测ID生成建议
    """
    if not request.predictions:
        raise HTTPException(status_code=400, detail="predictions is required; call /api/predict first or use the manual suggestion endpoint.")
    
    suggestions = suggestion_service.generate_suggestions(
        predictions=request.predictions,
        patient_allergies=request.patient_allergies,
        current_medications=request.current_medications
    )
    
    suggestion_dicts = [sug.to_dict() for sug in suggestions]
    
    return SuggestionResponse(
        suggestion_id=f"sug_{request.prediction_id}",
        prediction_id=request.prediction_id,
        suggestions=suggestion_dicts,
        generated_at=datetime.now().isoformat()
    )


@router.post("/test", response_model=SuggestionResponse)
async def test_suggestions(
    predictions: List[PredictionInput],
    patient_allergies: List[str] = []
):
    """
    人工校验建议生成（不需要预测ID）

    直接输入预测结果，快速校验建议生成功能
    """
    # 转换预测格式
    pred_dicts = [p.dict() for p in predictions]
    
    # 生成建议
    suggestions = suggestion_service.generate_suggestions(
        predictions=pred_dicts,
        patient_allergies=patient_allergies
    )
    
    # 转换为字典
    suggestion_dicts = [sug.to_dict() for sug in suggestions]
    
    return SuggestionResponse(
        suggestion_id="manual_sug",
        prediction_id="manual_pred",
        suggestions=suggestion_dicts,
        generated_at=datetime.now().isoformat()
    )


@router.get("/rules")
async def get_suggestion_rules():
    """
    获取建议规则列表
    
    返回所有已配置的建议规则
    """
    rules_info = []
    for rule in suggestion_service.rules:
        rules_info.append({
            "disease_pattern": rule.disease_pattern,
            "risk_threshold": rule.risk_threshold,
            "num_suggestions": len(rule.suggestions)
        })
    
    return {
        "total_rules": len(rules_info),
        "rules": rules_info
    }
