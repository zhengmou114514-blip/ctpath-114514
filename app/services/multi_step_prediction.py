"""
多步预测服务
支持预测未来1个月、3个月、半年等时间点的状态
"""
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ConfidenceInterval(BaseModel):
    """置信区间"""
    lower: float
    upper: float
    std: float


class PredictionItem(BaseModel):
    """预测项"""
    label: str
    score: float
    relation: str
    reason: Optional[str] = None
    confidenceInterval: Optional[ConfidenceInterval] = None
    relativeConfidence: Optional[float] = None


class MultiStepPredictionItem(BaseModel):
    """多步预测项"""
    step: int
    timestamp: str
    daysAhead: int
    predictions: List[PredictionItem]
    mode: str
    strategy: str
    evidence: Dict[str, Any]


class MultiStepPredictRequest(BaseModel):
    """多步预测请求"""
    patientId: str
    startTime: str
    steps: int = Field(default=3, ge=1, le=6)
    stepDays: int = Field(default=30, ge=7, le=180)
    topk: int = Field(default=3, ge=1, le=10)


class MultiStepPredictResponse(BaseModel):
    """多步预测响应"""
    patientId: str
    startTime: str
    steps: int
    stepDays: int
    multiStepPredictions: List[MultiStepPredictionItem]
    generatedAt: str


class MultiStepPredictionService:
    """多步预测服务"""

    def __init__(self, model_service):
        """
        初始化

        Args:
            model_service: 模型服务实例
        """
        self.model_service = model_service

        # 离散化规则
        self.discretization_rules = {
            "血糖": {
                "thresholds": [6.1, 7.0, 8.0],
                "labels": ["正常", "轻度升高", "中度升高", "重度升高"]
            },
            "糖化血红蛋白": {
                "thresholds": [6.0, 7.0, 8.0],
                "labels": ["达标", "轻度升高", "中度升高", "重度升高"]
            },
            "收缩压": {
                "thresholds": [120, 140, 160],
                "labels": ["正常", "轻度升高", "中度升高", "重度升高"]
            },
            "舒张压": {
                "thresholds": [80, 90, 100],
                "labels": ["正常", "轻度升高", "中度升高", "重度升高"]
            },
            "BMI": {
                "thresholds": [24, 28, 32],
                "labels": ["正常", "超重", "肥胖", "重度肥胖"]
            },
            "心率": {
                "thresholds": [80, 100, 120],
                "labels": ["正常", "轻度升高", "中度升高", "重度升高"]
            },
        }

    def predict_multi_step(
        self,
        patient_id: str,
        primary_disease: str,
        start_time: str,
        events: List[dict],
        steps: int = 3,
        step_days: int = 30,
        topk: int = 3,
    ) -> dict:
        """
        多步预测：预测未来多个时间点的状态

        Args:
            patient_id: 患者ID
            primary_disease: 主要疾病
            start_time: 起始时间
            events: 历史事件列表
            steps: 预测步数（默认3步）
            step_days: 每步间隔天数（默认30天）
            topk: 每步返回的预测数量

        Returns:
            包含多步预测结果的字典
        """
        multi_step_predictions = []
        current_time = datetime.strptime(start_time, "%Y-%m-%d")

        # 累积事件（用于后续预测）
        accumulated_events = list(events)

        for step in range(1, steps + 1):
            # 计算当前预测时间点
            prediction_time = current_time + timedelta(days=step * step_days)
            prediction_time_str = prediction_time.strftime("%Y-%m-%d")

            # 执行预测
            result = self.model_service.predict_with_events(
                patient_id=patient_id,
                primary_disease=primary_disease,
                timestamp=prediction_time_str,
                events=accumulated_events,
                topk=topk,
            )

            # 计算置信区间
            predictions_with_confidence = self._add_confidence_intervals(
                result["predictions"]
            )

            # 记录预测结果
            step_result = {
                "step": step,
                "timestamp": prediction_time_str,
                "daysAhead": step * step_days,
                "predictions": predictions_with_confidence,
                "mode": result["mode"],
                "strategy": result["strategy"],
                "evidence": result["evidence"],
            }
            multi_step_predictions.append(step_result)

            # 将预测结果作为新事件加入累积事件（用于下一步预测）
            for pred in predictions_with_confidence:
                if " -> " in pred["label"]:
                    relation, object_value = pred["label"].split(" -> ")
                    accumulated_events.append({
                        "event_time": prediction_time_str,
                        "relation": relation,
                        "object_value": object_value,
                        "note": f"第{step}步预测结果",
                        "is_predicted": True,
                    })

        return {
            "patientId": patient_id,
            "startTime": start_time,
            "steps": steps,
            "stepDays": step_days,
            "multiStepPredictions": multi_step_predictions,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
        }

    def _add_confidence_intervals(
        self,
        predictions: List[dict]
    ) -> List[dict]:
        """
        为预测结果添加置信区间

        Args:
            predictions: 预测结果列表

        Returns:
            添加了置信区间的预测结果
        """
        if not predictions:
            return predictions

        # 计算得分统计量
        scores = [p["score"] for p in predictions]
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        std_score = variance ** 0.5

        # 最高分
        max_score = max(scores)

        # 添加置信区间
        for pred in predictions:
            score = pred["score"]

            # 95%置信区间
            confidence_lower = max(0, score - 1.96 * std_score)
            confidence_upper = min(1, score + 1.96 * std_score)

            # 相对置信度
            relative_confidence = score / max_score if max_score > 0 else 0

            pred["confidenceInterval"] = {
                "lower": confidence_lower,
                "upper": confidence_upper,
                "std": std_score,
            }
            pred["relativeConfidence"] = relative_confidence

        return predictions

    def _discretize_continuous_value(
        self,
        relation: str,
        value: float
    ) -> str:
        """
        将连续值离散化为分层

        Args:
            relation: 关系类型
            value: 连续值

        Returns:
            离散化后的分层标签
        """
        if relation not in self.discretization_rules:
            return str(value)

        rule = self.discretization_rules[relation]
        thresholds = rule["thresholds"]
        labels = rule["labels"]

        for i, threshold in enumerate(thresholds):
            if value < threshold:
                return labels[i]

        return labels[-1]

    def _process_continuous_event(
        self,
        event: dict
    ) -> dict:
        """
        处理包含连续值的事件

        Args:
            event: 事件字典，可能包含 continuous_value 字段

        Returns:
            处理后的事件字典
        """
        if "continuous_value" in event:
            relation = event.get("relation", "")
            continuous_value = event["continuous_value"]

            # 离散化
            discrete_value = self._discretize_continuous_value(
                relation, continuous_value
            )

            # 更新事件
            event["object_value"] = discrete_value
            event["original_continuous_value"] = continuous_value
            event["discretization_note"] = (
                f"连续值 {continuous_value} 已离散化为 {discrete_value}"
            )

        return event


# 预测时间范围配置
PREDICTION_RANGES = {
    "1个月": {"steps": 1, "stepDays": 30},
    "3个月": {"steps": 3, "stepDays": 30},
    "半年": {"steps": 6, "stepDays": 30},
    "1年": {"steps": 12, "stepDays": 30},
}


def get_prediction_config(range_name: str) -> dict:
    """
    获取预测配置

    Args:
        range_name: 预测范围名称（"1个月", "3个月", "半年", "1年"）

    Returns:
        预测配置字典
    """
    return PREDICTION_RANGES.get(range_name, PREDICTION_RANGES["1个月"])
