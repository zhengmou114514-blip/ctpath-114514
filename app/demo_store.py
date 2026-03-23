from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .schemas import DoctorPublic, PatientCase, PatientEventCreateRequest, PatientUpsertRequest, TimelineEvent


@dataclass(frozen=True)
class DoctorRecord:
    username: str
    password: str
    name: str
    title: str
    department: str

    def to_public(self) -> DoctorPublic:
        return DoctorPublic(
            username=self.username,
            name=self.name,
            title=self.title,
            department=self.department,
        )


DOCTORS = [
    DoctorRecord(
        username="doctor01",
        password="ctpath123",
        name="郑昌号",
        title="住院医师",
        department="内分泌与慢病管理中心",
    ),
    DoctorRecord(
        username="endocrine",
        password="diabetes123",
        name="林怡雯",
        title="主治医师",
        department="糖尿病专病门诊",
    ),
]


PATIENT_CASES = [
    PatientCase(
        patientId="PID0248",
        name="赵文静",
        age=44,
        gender="女",
        primaryDisease="2型糖尿病",
        currentStage="Late",
        riskLevel="高风险",
        lastVisit="2025-03-08",
        summary="近半年血糖波动明显，合并心血管病史，服药依从性下降，需要强化随访。",
        dataSupport="high",
        stats=[
            {"label": "收缩压", "value": "133 mmHg", "trend": "较上次 +6"},
            {"label": "空腹血糖", "value": "12.6 mmol/L", "trend": "持续偏高"},
            {"label": "BMI", "value": "29.7", "trend": "轻度上升"},
            {"label": "服药依从性", "value": "Low", "trend": "需重点干预"},
        ],
        timeline=[
            {"date": "2024-11-12", "type": "visit", "title": "慢病门诊复诊", "detail": "记录空腹血糖升高，睡眠质量下降，建议两周后复查。"},
            {"date": "2025-01-06", "type": "diagnosis", "title": "阶段更新为 Late", "detail": "病程进展速度加快，叠加心血管病史，系统评估风险上升。"},
            {"date": "2025-02-18", "type": "medication", "title": "调整降糖方案", "detail": "新增二甲双胍联合方案，并要求每日记录晨起血糖。"},
            {"date": "2025-03-08", "type": "risk", "title": "触发高风险预警", "detail": "血糖控制不佳且依从性低，预测未来 30 天并发症风险增加。"},
        ],
        predictions=[
            {"label": "并发症风险持续升高", "score": 0.83, "reason": "阶段为 Late，心血管病史存在，依从性偏低。"},
            {"label": "下次随访前血糖仍可能失控", "score": 0.71, "reason": "近期三次复诊空腹血糖均高于目标范围。"},
            {"label": "需要强化用药教育", "score": 0.42, "reason": "近期存在漏服药和复诊间隔拉长情况。"},
        ],
        pathExplanation=[
            "Patient -> has_disease -> 2型糖尿病",
            "2型糖尿病 @ t-2 -> stage -> Late",
            "Late + 心血管病史 + 依从性 Low -> risk -> 并发症上升",
        ],
        followUps=[
            {"title": "安排两周内复查糖化血红蛋白", "owner": "内分泌门诊", "dueDate": "2025-03-22", "priority": "high"},
            {"title": "电话确认用药执行情况", "owner": "慢病管理护士", "dueDate": "2025-03-14", "priority": "high"},
            {"title": "补充饮食与运动宣教", "owner": "健康管理师", "dueDate": "2025-03-16", "priority": "medium"},
        ],
        recommendationMode="model",
        careAdvice=[
            "未来 2 周内增加 1 次复诊，重点监测空腹血糖与血压。",
            "把药物提醒加入患者随访计划，优先解决依从性下降问题。",
            "联合营养与运动指导，降低体重和血糖波动幅度。",
        ],
        similarCases=[
            {
                "caseId": "SC-101",
                "disease": "2型糖尿病 + 心血管病史",
                "matchScore": 0.91,
                "summary": "同类患者在强化随访后 1 个月内血糖波动明显下降。",
                "suggestion": "优先做短周期复诊和依从性干预。",
            }
        ],
    ),
    PatientCase(
        patientId="PID0031",
        name="陈国良",
        age=68,
        gender="男",
        primaryDisease="慢性肾病",
        currentStage="Mid",
        riskLevel="中风险",
        lastVisit="2025-02-21",
        summary="肾功能指标缓慢恶化，睡眠和情绪评分下降，近期需要连续观察。",
        dataSupport="medium",
        stats=[
            {"label": "心率", "value": "70 bpm", "trend": "基本稳定"},
            {"label": "睡眠时长", "value": "5.9 h", "trend": "较上次 -0.6h"},
            {"label": "情绪评分", "value": "17", "trend": "轻度下降"},
            {"label": "服药依从性", "value": "High", "trend": "较稳定"},
        ],
        timeline=[
            {"date": "2024-10-10", "type": "visit", "title": "专病门诊复查", "detail": "记录夜间睡眠减少和疲乏症状加重。"},
            {"date": "2024-12-02", "type": "diagnosis", "title": "阶段维持 Mid", "detail": "肾功能指标较前略差，但仍未进入高风险阶段。"},
            {"date": "2025-01-15", "type": "medication", "title": "优化护肾用药", "detail": "调整药物剂量，并增加家庭血压记录频率。"},
            {"date": "2025-02-21", "type": "risk", "title": "中风险提醒", "detail": "当前预测显示 1 个月内存在阶段波动风险。"},
        ],
        predictions=[
            {"label": "阶段波动可能继续", "score": 0.68, "reason": "睡眠、情绪和近期指标变化共同推动风险上升。"},
            {"label": "建议缩短随访间隔", "score": 0.57, "reason": "病程虽未进入高风险，但波动趋势明显。"},
            {"label": "近期急性恶化概率较低", "score": 0.29, "reason": "依从性和生命体征目前仍较稳定。"},
        ],
        pathExplanation=[
            "Patient -> has_disease -> 慢性肾病",
            "慢性肾病 @ t-1 -> mood_bin -> Q2",
            "mood_bin=Q2 + sleep_bin=Q1 -> risk -> 波动增加",
        ],
        followUps=[
            {"title": "一周内补录家庭血压记录", "owner": "患者本人", "dueDate": "2025-02-28", "priority": "medium"},
            {"title": "复查肾功能和尿蛋白", "owner": "肾病门诊", "dueDate": "2025-03-03", "priority": "medium"},
            {"title": "评估情绪与睡眠干预方案", "owner": "全科医生", "dueDate": "2025-03-05", "priority": "low"},
        ],
        recommendationMode="model",
        careAdvice=[
            "建议 2 周内再次复诊，监测睡眠、情绪和肾功能变化。",
            "继续维持当前用药依从性，并补足家庭监测记录。",
            "必要时加做睡眠和心理干预评估。",
        ],
        similarCases=[
            {
                "caseId": "SC-210",
                "disease": "慢性肾病",
                "matchScore": 0.87,
                "summary": "同阶段患者在强化家庭监测后风险保持稳定。",
                "suggestion": "优先提升家庭监测完整度。",
            }
        ],
    ),
    PatientCase(
        patientId="PID0024",
        name="孙美兰",
        age=53,
        gender="女",
        primaryDisease="阿尔茨海默病",
        currentStage="Early",
        riskLevel="中风险",
        lastVisit="2025-01-26",
        summary="当前结构化事件较少，系统以相似病例匹配为主，辅助制定随访与照护建议。",
        dataSupport="low",
        stats=[
            {"label": "认知评分", "value": "11", "trend": "轻度下降"},
            {"label": "睡眠时长", "value": "4.5 h", "trend": "明显不足"},
            {"label": "家庭支持", "value": "Moderate", "trend": "需要增强"},
            {"label": "照护者状态", "value": "No", "trend": "缺少固定照护者"},
        ],
        timeline=[
            {"date": "2024-09-03", "type": "visit", "title": "记忆门诊初诊", "detail": "主诉近半年记忆力下降，日常安排依赖家属提醒。"},
            {"date": "2024-11-16", "type": "diagnosis", "title": "阶段评估为 Early", "detail": "当前认知功能轻度下降，但家庭照护资源不足。"},
            {"date": "2025-01-10", "type": "medication", "title": "开始认知干预", "detail": "增加睡眠管理与家庭陪护建议，药物方案保持保守。"},
            {"date": "2025-01-26", "type": "risk", "title": "进入案例辅助模式", "detail": "因样本支持较弱，系统切换到相似病例推荐策略。"},
        ],
        predictions=[
            {"label": "建议以相似病例辅助管理", "score": 0.64, "reason": "时序样本不足，当前更适合用案例检索支持决策。"},
            {"label": "短期内需加强家庭支持", "score": 0.49, "reason": "睡眠不足且缺少稳定照护者。"},
            {"label": "认知评分可能继续缓慢下降", "score": 0.21, "reason": "近期连续两次评估表现出下降趋势。"},
        ],
        pathExplanation=[
            "Patient -> has_disease -> 阿尔茨海默病",
            "阿尔茨海默病 @ t-1 -> support_system -> Moderate",
            "support_system=Moderate + caregiver=0 -> risk -> 波动增加",
        ],
        followUps=[
            {"title": "建立固定照护者计划", "owner": "家庭成员", "dueDate": "2025-02-05", "priority": "high"},
            {"title": "补录睡眠和行为观察", "owner": "健康管理师", "dueDate": "2025-02-02", "priority": "medium"},
            {"title": "安排 1 个月后认知复评", "owner": "神经内科门诊", "dueDate": "2025-02-26", "priority": "medium"},
        ],
        recommendationMode="similar-case",
        careAdvice=[
            "优先建立固定照护者和家庭提醒机制。",
            "在真实样本不足阶段，结合相似病例和规则策略辅助诊疗。",
            "补充连续随访数据后，再切回模型推演模式。",
        ],
        similarCases=[
            {
                "caseId": "SC-301",
                "disease": "阿尔茨海默病早期",
                "matchScore": 0.89,
                "summary": "类似患者在建立固定照护者和睡眠干预后认知下降速度减缓。",
                "suggestion": "优先补齐家庭支持与睡眠管理。",
            },
            {
                "caseId": "SC-318",
                "disease": "认知下降伴家庭支持不足",
                "matchScore": 0.84,
                "summary": "通过短周期复诊和家庭任务分工，可以提升随访质量。",
                "suggestion": "按周跟进家庭照护执行情况。",
            },
        ],
    ),
]


for index in range(1, 19):
    template = PATIENT_CASES[(index - 1) % 3]
    payload = template.model_dump()
    payload["patientId"] = "PX{0:02d}{1}".format(index, template.patientId[-2:])
    payload["name"] = "{0}{1}".format(template.name, index)
    payload["age"] = template.age + (index % 4)
    payload["lastVisit"] = "2025-{0:02d}-{1:02d}".format(((index - 1) % 9) + 1, ((index - 1) % 18) + 10)
    PATIENT_CASES.append(PatientCase(**payload))


TOKENS: Dict[str, str] = {}


def authenticate(username: str, password: str) -> Optional[DoctorPublic]:
    for doctor in DOCTORS:
        if doctor.username == username and doctor.password == password:
            return doctor.to_public()
    return None


def issue_token(username: str) -> str:
    token = "demo-{0}-{1}".format(username, uuid4().hex)
    TOKENS[token] = username
    return token


def is_token_valid(token: Optional[str]) -> bool:
    return bool(token and token in TOKENS)


def list_patients() -> List[dict]:
    return [
        {
            "patientId": item.patientId,
            "name": item.name,
            "age": item.age,
            "gender": item.gender,
            "primaryDisease": item.primaryDisease,
            "currentStage": item.currentStage,
            "riskLevel": item.riskLevel,
            "lastVisit": item.lastVisit,
            "summary": item.summary,
            "dataSupport": item.dataSupport,
        }
        for item in PATIENT_CASES
    ]


def get_patient(patient_id: str) -> Optional[PatientCase]:
    for item in PATIENT_CASES:
        if item.patientId == patient_id:
            return item
    return None


def get_timeline(patient_id: str) -> Optional[List[TimelineEvent]]:
    patient = get_patient(patient_id)
    return patient.timeline if patient else None


def save_patient(payload: PatientUpsertRequest) -> PatientCase:
    existing = get_patient(payload.patientId)
    if existing:
        data = existing.model_dump()
    else:
        data = {
            "patientId": payload.patientId,
            "name": payload.name,
            "age": payload.age,
            "gender": payload.gender,
            "primaryDisease": payload.primaryDisease,
            "currentStage": payload.currentStage,
            "riskLevel": payload.riskLevel,
            "lastVisit": payload.lastVisit,
            "summary": payload.summary,
            "dataSupport": payload.dataSupport,
            "stats": [],
            "timeline": [],
            "predictions": [],
            "pathExplanation": [],
            "followUps": [],
            "recommendationMode": "similar-case" if payload.dataSupport == "low" else "model",
            "careAdvice": ["请补充结构化病历事件后再进行进一步推演。"],
            "similarCases": [],
        }

    data.update(payload.model_dump())
    data["recommendationMode"] = "similar-case" if payload.dataSupport == "low" else "model"
    patient_case = PatientCase(**data)

    if existing:
        PATIENT_CASES.remove(existing)
    PATIENT_CASES.insert(0, patient_case)
    return patient_case


def add_event(patient_id: str, payload: PatientEventCreateRequest) -> Optional[PatientCase]:
    patient = get_patient(patient_id)
    if not patient:
        return None

    timeline = list(patient.timeline)
    timeline.append(
        TimelineEvent(
            date=payload.eventTime[:10],
            type="visit",
            title="{0}: {1}".format(payload.relation, payload.objectValue),
            detail=payload.note or "{0} -> {1}".format(payload.relation, payload.objectValue),
        )
    )
    timeline.sort(key=lambda item: item.date)

    updated = PatientCase(
        **{
            **patient.model_dump(),
            "timeline": timeline,
            "pathExplanation": [*patient.pathExplanation[-2:], "{0} -> {1}".format(payload.eventTime[:10], payload.objectValue)],
        }
    )

    PATIENT_CASES.remove(patient)
    PATIENT_CASES.insert(0, updated)
    return updated


def predict_for_patient(patient_id: str, topk: int) -> Optional[dict]:
    patient = get_patient(patient_id)
    if patient is None:
        return None
    return {
        "patientId": patient.patientId,
        "mode": patient.recommendationMode,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "topk": patient.predictions[:topk],
        "advice": patient.careAdvice,
        "pathExplanation": patient.pathExplanation,
        "similarCases": patient.similarCases,
    }
