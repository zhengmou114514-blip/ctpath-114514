"""
诊疗建议生成服务

基于病情预测结果生成结构化的诊疗建议，包括：
- 推荐检查项目
- 用药调整建议
- 随访时间建议
- 生活方式建议
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import json


class RiskLevel(Enum):
    """风险等级"""
    LOW = "低风险"
    MEDIUM = "中风险"
    HIGH = "高风险"
    VERY_HIGH = "极高风险"


class SuggestionType(Enum):
    """建议类型"""
    EXAMINATION = "检查"
    MEDICATION = "用药"
    FOLLOW_UP = "随访"
    LIFESTYLE = "生活方式"


class Suggestion:
    """诊疗建议"""
    
    def __init__(
        self,
        suggestion_type: SuggestionType,
        content: str,
        risk_level: RiskLevel,
        valid_days: int = 7,
        priority: int = 1,
        reason: str = ""
    ):
        """
        初始化建议
        
        Args:
            suggestion_type: 建议类型
            content: 建议内容
            risk_level: 风险等级
            valid_days: 有效天数
            priority: 优先级（1-5，1最高）
            reason: 建议理由
        """
        self.type = suggestion_type
        self.content = content
        self.risk_level = risk_level
        self.valid_days = valid_days
        self.priority = priority
        self.reason = reason
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.type.value,
            "content": self.content,
            "risk_level": self.risk_level.value,
            "valid_days": self.valid_days,
            "priority": self.priority,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "expires_at": (self.created_at + timedelta(days=self.valid_days)).isoformat()
        }


class SuggestionRule:
    """建议规则"""
    
    def __init__(
        self,
        disease_pattern: str,
        risk_threshold: float,
        suggestions: List[Dict]
    ):
        """
        初始化规则
        
        Args:
            disease_pattern: 疾病模式（支持正则表达式）
            risk_threshold: 风险阈值
            suggestions: 建议列表
        """
        self.disease_pattern = disease_pattern
        self.risk_threshold = risk_threshold
        self.suggestions = suggestions


class SuggestionService:
    """诊疗建议生成服务"""
    
    def __init__(self):
        """初始化服务"""
        self.rules = self._load_rules()
        self.medication_conflicts = self._load_medication_conflicts()
    
    def _load_rules(self) -> List[SuggestionRule]:
        """加载建议规则库"""
        rules = [
            # 高血压相关规则
            SuggestionRule(
                disease_pattern="高血压|HTN|I10",
                risk_threshold=0.3,
                suggestions=[
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行24小时动态血压监测，评估血压波动情况",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行心电图和心脏超声检查，评估心脏结构功能",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.MEDICATION,
                        "content": "考虑调整降压药物方案，可能需要联合用药",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.FOLLOW_UP,
                        "content": "建议2周后复查血压，评估治疗效果",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.LIFESTYLE,
                        "content": "建议低盐饮食（每日盐摄入<6g），控制体重，规律运动",
                        "priority": 3
                    }
                ]
            ),
            
            # 糖尿病相关规则
            SuggestionRule(
                disease_pattern="糖尿病|DM|E11",
                risk_threshold=0.3,
                suggestions=[
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行糖化血红蛋白(HbA1c)检测，评估血糖控制情况",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行眼底检查和尿微量白蛋白检测，筛查并发症",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.MEDICATION,
                        "content": "根据血糖水平考虑调整降糖药物剂量或种类",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.FOLLOW_UP,
                        "content": "建议3个月后复查HbA1c，评估血糖控制效果",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.LIFESTYLE,
                        "content": "建议控制饮食总热量，规律运动，监测血糖",
                        "priority": 3
                    }
                ]
            ),
            
            # 脑卒中风险规则
            SuggestionRule(
                disease_pattern="脑卒中|中风|I63",
                risk_threshold=0.5,
                suggestions=[
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议紧急进行头颅CT或MRI检查，明确卒中类型",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行颈动脉超声检查，评估血管狭窄情况",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.MEDICATION,
                        "content": "根据卒中类型考虑抗凝或抗血小板治疗",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.FOLLOW_UP,
                        "content": "建议1周后复查，评估病情变化",
                        "priority": 1
                    }
                ]
            ),
            
            # 冠心病相关规则
            SuggestionRule(
                disease_pattern="冠心病|CHD|I25",
                risk_threshold=0.4,
                suggestions=[
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行心电图和心肌酶谱检查，评估心肌缺血情况",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行冠状动脉CTA或造影检查，评估冠脉狭窄程度",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.MEDICATION,
                        "content": "考虑抗血小板、他汀类、β受体阻滞剂等药物治疗",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.FOLLOW_UP,
                        "content": "建议1个月后复查心电图和血脂",
                        "priority": 2
                    }
                ]
            ),
            
            # 肾功能不全规则
            SuggestionRule(
                disease_pattern="肾功能不全|肾衰|N18",
                risk_threshold=0.4,
                suggestions=[
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行肾功能、电解质、尿常规检查",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.EXAMINATION,
                        "content": "建议进行肾脏超声检查，评估肾脏形态",
                        "priority": 2
                    },
                    {
                        "type": SuggestionType.MEDICATION,
                        "content": "注意避免肾毒性药物，调整经肾排泄药物剂量",
                        "priority": 1
                    },
                    {
                        "type": SuggestionType.LIFESTYLE,
                        "content": "建议低蛋白饮食，控制血压和血糖",
                        "priority": 2
                    }
                ]
            )
        ]
        
        return rules
    
    def _load_medication_conflicts(self) -> Dict[str, List[str]]:
        """加载药物冲突信息"""
        return {
            "青霉素": ["阿莫西林", "氨苄西林", "哌拉西林"],
            "磺胺": ["复方新诺明", "磺胺嘧啶"],
            "阿司匹林": ["布洛芬", "双氯芬酸", "吲哚美辛"],
            "华法林": ["阿司匹林", "氯吡格雷", "肝素"]
        }
    
    def generate_suggestions(
        self,
        predictions: List[Dict],
        patient_allergies: List[str] = None,
        current_medications: List[str] = None
    ) -> List[Suggestion]:
        """
        生成诊疗建议
        
        Args:
            predictions: 预测结果列表，每个元素包含entity和confidence
            patient_allergies: 患者过敏史
            current_medications: 当前用药列表
        
        Returns:
            suggestions: 建议列表
        """
        if patient_allergies is None:
            patient_allergies = []
        if current_medications is None:
            current_medications = []
        
        all_suggestions = []
        
        # 为每个预测结果生成建议
        for pred in predictions:
            entity = pred.get('entity', '')
            confidence = pred.get('confidence', 0)
            
            # 计算风险等级
            risk_level = self._calculate_risk_level(entity, confidence)
            
            # 匹配规则
            matched_rules = self._match_rules(entity, confidence)
            
            # 生成建议
            for rule in matched_rules:
                for sug_dict in rule.suggestions:
                    suggestion = Suggestion(
                        suggestion_type=sug_dict['type'],
                        content=sug_dict['content'],
                        risk_level=risk_level,
                        priority=sug_dict.get('priority', 3),
                        reason=f"基于{entity}风险预测（置信度：{confidence:.2%}）"
                    )
                    all_suggestions.append(suggestion)
        
        # 过滤冲突建议
        all_suggestions = self._filter_conflicts(
            all_suggestions,
            patient_allergies,
            current_medications
        )
        
        # 去重和排序
        all_suggestions = self._deduplicate_and_sort(all_suggestions)
        
        return all_suggestions
    
    def _calculate_risk_level(self, entity: str, confidence: float) -> RiskLevel:
        """
        计算风险等级
        
        Args:
            entity: 疾病实体
            confidence: 置信度
        
        Returns:
            risk_level: 风险等级
        """
        # 高危疾病列表
        high_risk_diseases = ["脑卒中", "心肌梗死", "肾衰竭", "心衰"]
        
        # 极高危疾病列表
        very_high_risk_diseases = ["脑卒中", "心肌梗死"]
        
        # 判断风险等级
        if any(d in entity for d in very_high_risk_diseases) and confidence > 0.7:
            return RiskLevel.VERY_HIGH
        elif any(d in entity for d in high_risk_diseases) and confidence > 0.5:
            return RiskLevel.HIGH
        elif confidence > 0.6:
            return RiskLevel.HIGH
        elif confidence > 0.4:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _match_rules(self, entity: str, confidence: float) -> List[SuggestionRule]:
        """
        匹配建议规则
        
        Args:
            entity: 疾病实体
            confidence: 置信度
        
        Returns:
            matched_rules: 匹配的规则列表
        """
        import re
        
        matched = []
        for rule in self.rules:
            # 检查疾病模式是否匹配
            if re.search(rule.disease_pattern, entity, re.IGNORECASE):
                # 检查置信度是否超过阈值
                if confidence >= rule.risk_threshold:
                    matched.append(rule)
        
        return matched
    
    def _filter_conflicts(
        self,
        suggestions: List[Suggestion],
        allergies: List[str],
        current_medications: List[str]
    ) -> List[Suggestion]:
        """
        过滤冲突建议
        
        Args:
            suggestions: 建议列表
            allergies: 过敏史
            current_medications: 当前用药
        
        Returns:
            filtered_suggestions: 过滤后的建议列表
        """
        filtered = []
        
        for sug in suggestions:
            # 检查用药建议是否与过敏史冲突
            if sug.type == SuggestionType.MEDICATION:
                has_conflict = False
                for allergy in allergies:
                    # 检查是否包含过敏药物
                    conflict_drugs = self.medication_conflicts.get(allergy, [])
                    if any(drug in sug.content for drug in conflict_drugs):
                        has_conflict = True
                        break
                    if allergy in sug.content:
                        has_conflict = True
                        break
                
                if has_conflict:
                    # 标记为冲突，但仍保留（添加警告）
                    sug.reason += " [警告：可能与过敏史冲突]"
            
            filtered.append(sug)
        
        return filtered
    
    def _deduplicate_and_sort(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """
        去重并排序
        
        Args:
            suggestions: 建议列表
        
        Returns:
            sorted_suggestions: 排序后的建议列表
        """
        # 去重（基于内容）
        seen = set()
        unique = []
        for sug in suggestions:
            if sug.content not in seen:
                seen.add(sug.content)
                unique.append(sug)
        
        # 排序：按优先级和风险等级
        risk_order = {
            RiskLevel.VERY_HIGH: 0,
            RiskLevel.HIGH: 1,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 3
        }
        
        unique.sort(key=lambda x: (x.priority, risk_order[x.risk_level]))
        
        return unique
    
    def get_generic_suggestions(self) -> List[Suggestion]:
        """
        获取通用建议（当无匹配规则时使用）
        
        Returns:
            suggestions: 通用建议列表
        """
        return [
            Suggestion(
                suggestion_type=SuggestionType.FOLLOW_UP,
                content="建议定期复查，监测病情变化",
                risk_level=RiskLevel.MEDIUM,
                priority=3
            ),
            Suggestion(
                suggestion_type=SuggestionType.LIFESTYLE,
                content="建议保持健康生活方式，合理饮食，适量运动",
                risk_level=RiskLevel.LOW,
                priority=4
            ),
            Suggestion(
                suggestion_type=SuggestionType.EXAMINATION,
                content="建议进行常规体检，及早发现潜在问题",
                risk_level=RiskLevel.LOW,
                priority=5
            )
        ]
