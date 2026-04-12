from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from .security import hash_password, verify_password
from .schemas import (
    ContactLog,
    ContactLogCreateRequest,
    DoctorPublic,
    EncounterStatusUpdateRequest,
    MaintenanceCountItem,
    MaintenanceEventRow,
    MaintenanceIdentityAlertRow,
    MaintenanceOverviewResponse,
    MaintenancePatientRow,
    MaintenanceRelationStat,
    OutpatientTask,
    OutpatientTaskCreateRequest,
    OutpatientTaskLog,
    OutpatientTaskStatusUpdateRequest,
    PatientAuditLog,
    PatientCase,
    PatientEventCreateRequest,
    PatientUpsertRequest,
    RegisterRequest,
    TimelineEvent,
)


RELATION_LABELS = {
    "has_disease": "主要疾病",
    "stage": "疾病阶段",
    "med_adherence": "服药依从性",
    "medical_history": "既往病史",
    "support_system": "照护支持",
    "sleep_hours_bin": "睡眠分层",
    "mood_bin": "情绪分层",
    "bp_sys_bin": "收缩压分层",
    "bmi_bin": "BMI 分层",
    "cholesterol_bin": "胆固醇分层",
}


def relation_label(relation: str) -> str:
    return RELATION_LABELS.get(relation, relation)


def relation_type(relation: str) -> str:
    if relation in {"has_disease", "stage", "medical_history"}:
        return "diagnosis"
    if relation == "med_adherence":
        return "medication"
    if relation in {"support_system", "sleep_hours_bin", "mood_bin", "bp_sys_bin", "bmi_bin", "cholesterol_bin"}:
        return "risk"
    return "visit"


def to_date(value: str) -> str:
    return value[:10]


def patient_profile_defaults(record: Dict[str, object]) -> Dict[str, str]:
    return {
        "avatarUrl": str(record.get("avatarUrl", "")),
        "phone": str(record.get("phone", "")),
        "emergencyContactName": str(record.get("emergencyContactName", "")),
        "emergencyContactRelation": str(record.get("emergencyContactRelation", "")),
        "emergencyContactPhone": str(record.get("emergencyContactPhone", "")),
        "identityMasked": str(record.get("identityMasked", "3203********1234")),
        "insuranceType": str(record.get("insuranceType", "城镇职工")),
        "department": str(record.get("department", "慢病管理门诊")),
        "primaryDoctor": str(record.get("primaryDoctor", "周医生")),
        "caseManager": str(record.get("caseManager", "张护士")),
        "allergyHistory": str(record.get("allergyHistory", "无")),
        "familyHistory": str(record.get("familyHistory", "无特殊家族史")),
    }

def _build_audit_logs(record: Dict[str, object]) -> List[PatientAuditLog]:
    raw_logs = list(record.get("auditLogs", []))
    if not raw_logs:
        raw_logs = [
            {
                "logId": "alog-{0}-seed".format(record["patientId"]),
                "action": "archive_created",
                "operatorUsername": "system",
                "operatorName": "System",
                "detail": "Initial archive imported from demo seed data.",
                "createdAt": "{0}T08:00:00".format(record.get("lastVisit", "2025-01-01")),
            }
        ]
    return [PatientAuditLog(**item) for item in raw_logs]


@dataclass(frozen=True)
class DoctorRecord:
    username: str
    password_hash: str
    name: str
    title: str
    department: str
    role: str = "doctor"  # 默认角色为doctor

    def to_public(self) -> DoctorPublic:
        return DoctorPublic(
            username=self.username,
            name=self.name,
            title=self.title,
            department=self.department,
            role=self.role,
        )


DOCTORS = [
    DoctorRecord(
        username="demo_clinic",
        password_hash=hash_password("demo123456"),
        name="系统演示账号",
        title="门诊医生",
        department="慢病管理门诊",
        role="doctor",
    ),
    DoctorRecord(
        username="demo_nurse",
        password_hash=hash_password("demo123456"),
        name="护士演示账号",
        title="主管护士",
        department="慢病管理门诊",
        role="nurse",
    ),
    DoctorRecord(
        username="demo_archivist",
        password_hash=hash_password("demo123456"),
        name="档案管理员演示账号",
        title="档案管理员",
        department="病案室",
        role="archivist",
    ),
    DoctorRecord(
        username="demo_specialist",
        password_hash=hash_password("demo123456"),
        name="专科演示账号",
        title="专科医生",
        department="神经内科门诊",
        role="doctor",
    ),
]


PATIENT_RECORDS: List[Dict[str, object]] = [
    {
        "patientId": "PID0025",
        "name": "周建华",
        "age": 72,
        "gender": "男",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E5%91%A8%E5%BB%BA%E5%8D%8E",
        "phone": "13800010025",
        "emergencyContactName": "周敏",
        "emergencyContactRelation": "女儿",
        "emergencyContactPhone": "13800020025",
        "primaryDisease": "Parkinson's",
        "currentStage": "Mid",
        "riskLevel": "高风险",
        "lastVisit": "2025-03-18",
        "summary": "来源于 CHRONIC 的帕金森病病例模式，阶段已进入中期，近期需要重点关注步态波动与复诊节奏。",
        "dataSupport": "high",
        "contactLogs": [
            {
                "logId": "clog-demo-0025",
                "contactTime": "2025-03-19T10:00:00",
                "contactType": "phone",
                "contactTarget": "patient",
                "contactResult": "reached",
                "operatorUsername": "demo_clinic",
                "operatorName": "系统演示账号",
                "note": "电话随访已接通，提醒继续观察步态波动并按时复诊。",
                "nextContactDate": "2025-03-26",
            }
        ],
        "events": [
            {"event_time": "2024-12-12 09:00:00", "relation": "has_disease", "object_value": "Parkinson's", "note": "门诊首次建档，明确帕金森病诊断。", "source": "seed"},
            {"event_time": "2025-01-18 10:20:00", "relation": "stage", "object_value": "Mid", "note": "症状评估提示疾病进入中期阶段。", "source": "seed"},
            {"event_time": "2025-02-09 08:30:00", "relation": "med_adherence", "object_value": "High", "note": "近一月依从性较好。", "source": "seed"},
            {"event_time": "2025-02-26 15:00:00", "relation": "support_system", "object_value": "Moderate", "note": "家属可陪同复诊，但日常照护仍有缺口。", "source": "seed"},
            {"event_time": "2025-03-18 09:10:00", "relation": "medical_history", "object_value": "Heart_Disease", "note": "既往合并心脏病史。", "source": "seed"},
        ],
    },
    {
        "patientId": "PID0078",
        "name": "刘淑琴",
        "age": 79,
        "gender": "女",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E5%88%98%E6%B7%91%E7%90%B4",
        "phone": "13800010078",
        "emergencyContactName": "陈立",
        "emergencyContactRelation": "儿子",
        "emergencyContactPhone": "13800020078",
        "primaryDisease": "Alzheimer's",
        "currentStage": "Late",
        "riskLevel": "高风险",
        "lastVisit": "2025-03-16",
        "summary": "来源于 CHRONIC 的阿尔茨海默病晚期病例模式，需重点关注照护支持和连续随访。",
        "dataSupport": "high",
        "contactLogs": [
            {
                "logId": "clog-demo-0078",
                "contactTime": "2025-03-17T15:20:00",
                "contactType": "family",
                "contactTarget": "emergency_contact",
                "contactResult": "scheduled",
                "operatorUsername": "demo_specialist",
                "operatorName": "专科演示账号",
                "note": "与家属确认本周陪同复诊，补充夜间照护观察记录。",
                "nextContactDate": "2025-03-24",
            }
        ],
        "events": [
            {"event_time": "2024-11-05 14:00:00", "relation": "has_disease", "object_value": "Alzheimer's", "note": "记忆门诊复评，诊断明确。", "source": "seed"},
            {"event_time": "2025-01-08 09:15:00", "relation": "stage", "object_value": "Late", "note": "认知评估提示疾病进入晚期。", "source": "seed"},
            {"event_time": "2025-02-02 11:40:00", "relation": "support_system", "object_value": "Strong", "note": "家属轮班陪护，照护支持较强。", "source": "seed"},
            {"event_time": "2025-02-20 08:00:00", "relation": "med_adherence", "object_value": "Low", "note": "近期服药记录不完整。", "source": "seed"},
            {"event_time": "2025-03-16 10:10:00", "relation": "sleep_hours_bin", "object_value": "Q1", "note": "夜间睡眠不足，需要干预。", "source": "seed"},
        ],
    },
    {
        "patientId": "PID0217",
        "name": "张美兰",
        "age": 75,
        "gender": "女",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E5%BC%A0%E7%BE%8E%E5%85%B0",
        "phone": "13800010217",
        "emergencyContactName": "李芳",
        "emergencyContactRelation": "女儿",
        "emergencyContactPhone": "13800020217",
        "primaryDisease": "Alzheimer's",
        "currentStage": "Mid",
        "riskLevel": "中风险",
        "lastVisit": "2025-03-12",
        "summary": "来源于 CHRONIC 的阿尔茨海默病中期病例模式，当前支持系统较稳定，但仍需跟踪情绪与睡眠。",
        "dataSupport": "high",
        "contactLogs": [],
        "events": [
            {"event_time": "2024-12-18 10:00:00", "relation": "has_disease", "object_value": "Alzheimer's", "note": "神经内科随访确认病程延续。", "source": "seed"},
            {"event_time": "2025-01-26 09:30:00", "relation": "stage", "object_value": "Mid", "note": "综合量表评估为中期。", "source": "seed"},
            {"event_time": "2025-02-17 13:40:00", "relation": "support_system", "object_value": "Strong", "note": "家庭照护支持充足。", "source": "seed"},
            {"event_time": "2025-02-28 08:20:00", "relation": "med_adherence", "object_value": "Low", "note": "存在漏服现象。", "source": "seed"},
            {"event_time": "2025-03-12 09:00:00", "relation": "medical_history", "object_value": "Asthma", "note": "既往合并哮喘病史。", "source": "seed"},
        ],
    },
    {
        "patientId": "PID0191",
        "name": "王海峰",
        "age": 61,
        "gender": "男",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E7%8E%8B%E6%B5%B7%E5%B3%B0",
        "phone": "13800010191",
        "emergencyContactName": "王琳",
        "emergencyContactRelation": "配偶",
        "emergencyContactPhone": "13800020191",
        "primaryDisease": "Diabetes",
        "currentStage": "Mid",
        "riskLevel": "中风险",
        "lastVisit": "2025-03-20",
        "summary": "来源于 CHRONIC 的糖尿病中期病例模式，血糖管理和血压监测需要持续跟进。",
        "dataSupport": "high",
        "contactLogs": [
            {
                "logId": "clog-demo-0191",
                "contactTime": "2025-03-21T09:10:00",
                "contactType": "phone",
                "contactTarget": "patient",
                "contactResult": "reached",
                "operatorUsername": "demo_clinic",
                "operatorName": "系统演示账号",
                "note": "电话回访已接通，提醒继续监测血糖和血压，并准备下次门诊检查结果。",
                "nextContactDate": "2025-03-28",
            }
        ],
        "events": [
            {"event_time": "2024-12-10 08:40:00", "relation": "has_disease", "object_value": "Diabetes", "note": "确认为 2 型糖尿病持续管理对象。", "source": "seed"},
            {"event_time": "2025-01-14 09:10:00", "relation": "stage", "object_value": "Mid", "note": "综合评估为中期慢病管理阶段。", "source": "seed"},
            {"event_time": "2025-02-11 08:20:00", "relation": "med_adherence", "object_value": "Medium", "note": "依从性一般。", "source": "seed"},
            {"event_time": "2025-03-03 14:30:00", "relation": "bp_sys_bin", "object_value": "Q3", "note": "收缩压分层偏高。", "source": "seed"},
            {"event_time": "2025-03-20 09:15:00", "relation": "medical_history", "object_value": "Stroke", "note": "既往卒中史。", "source": "seed"},
        ],
    },
    {
        "patientId": "PID0313",
        "name": "陈素梅",
        "age": 57,
        "gender": "女",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E9%99%88%E7%B4%A0%E6%A2%85",
        "phone": "13800010313",
        "emergencyContactName": "赵辉",
        "emergencyContactRelation": "配偶",
        "emergencyContactPhone": "13800020313",
        "primaryDisease": "Diabetes",
        "currentStage": "Mid",
        "riskLevel": "中风险",
        "lastVisit": "2025-03-08",
        "summary": "来源于 CHRONIC 的糖尿病病例模式，样本支持较弱，更适合作为低样本辅助示例。",
        "dataSupport": "low",
        "contactLogs": [],
        "events": [
            {"event_time": "2025-01-06 10:00:00", "relation": "has_disease", "object_value": "Diabetes", "note": "首次录入门诊慢病台账。", "source": "seed"},
            {"event_time": "2025-02-01 09:50:00", "relation": "stage", "object_value": "Mid", "note": "当前阶段评估为中期。", "source": "seed"},
            {"event_time": "2025-03-08 08:40:00", "relation": "support_system", "object_value": "Weak", "note": "家庭支持较弱，建议加强随访。", "source": "seed"},
        ],
    },
    {
        "patientId": "PID0144",
        "name": "马惠春",
        "age": 70,
        "gender": "男",
        "avatarUrl": "https://api.dicebear.com/9.x/initials/svg?seed=%E9%A9%AC%E6%83%A0%E6%98%A5",
        "phone": "13800010144",
        "emergencyContactName": "马强",
        "emergencyContactRelation": "儿子",
        "emergencyContactPhone": "13800020144",
        "primaryDisease": "Parkinson's",
        "currentStage": "Late",
        "riskLevel": "高风险",
        "lastVisit": "2025-03-06",
        "summary": "来源于 CHRONIC 的帕金森病晚期病例模式，需重点处理跌倒风险和用药依从性。",
        "dataSupport": "high",
        "contactLogs": [],
        "events": [
            {"event_time": "2024-10-28 08:10:00", "relation": "has_disease", "object_value": "Parkinson's", "note": "专病门诊确诊并纳入随访。", "source": "seed"},
            {"event_time": "2025-01-12 09:30:00", "relation": "stage", "object_value": "Late", "note": "病程进展至晚期。", "source": "seed"},
            {"event_time": "2025-02-05 14:20:00", "relation": "support_system", "object_value": "Strong", "note": "家属陪护稳定。", "source": "seed"},
            {"event_time": "2025-02-22 08:15:00", "relation": "med_adherence", "object_value": "High", "note": "依从性良好。", "source": "seed"},
            {"event_time": "2025-03-06 11:00:00", "relation": "medical_history", "object_value": "Heart_Disease", "note": "合并心脏病史。", "source": "seed"},
        ],
    },
]


TOKENS: Dict[str, str] = {}
ENCOUNTER_STATUS: Dict[str, str] = {}
OUTPATIENT_TASKS: Dict[str, List[Dict[str, object]]] = {}


def _find_record(patient_id: str) -> Optional[Dict[str, object]]:
    for record in PATIENT_RECORDS:
        if record["patientId"] == patient_id:
            return record
    return None


def _default_encounter_status(record: Dict[str, object]) -> str:
    return "pending_review" if str(record["dataSupport"]) == "low" else "waiting"


def _actor_display_name(username: Optional[str], name: Optional[str]) -> Optional[str]:
    if name:
        return name
    if username:
        return username
    return None


def _build_outpatient_tasks(patient_id: str) -> List[OutpatientTask]:
    return [
        OutpatientTask(
            taskId=item["taskId"],
            category=item["category"],
            title=item["title"],
            owner=item["owner"],
            dueDate=item["dueDate"],
            priority=item["priority"],
            status=item["status"],
            note=item["note"],
            source=item["source"],
            updatedBy=item.get("updatedBy"),
            updatedAt=item.get("updatedAt"),
            logs=[
                OutpatientTaskLog(
                    logId=str(log["logId"]),
                    action=str(log["action"]),
                    actorUsername=log.get("actorUsername"),
                    actorName=log.get("actorName"),
                    createdAt=str(log["createdAt"]),
                    note=str(log.get("note") or ""),
                )
                for log in item.get("logs", [])
            ],
        )
        for item in OUTPATIENT_TASKS.get(patient_id, [])
    ]


def _build_contact_logs(record: Dict[str, object]) -> List[ContactLog]:
    logs = record.get("contactLogs", [])
    if not isinstance(logs, list):
        return []
    return [
        ContactLog(
            logId=str(item["logId"]),
            contactTime=str(item["contactTime"]),
            contactType=str(item["contactType"]),
            contactTarget=str(item["contactTarget"]),
            contactResult=str(item["contactResult"]),
            operatorUsername=item.get("operatorUsername"),
            operatorName=item.get("operatorName"),
            note=str(item.get("note") or ""),
            nextContactDate=item.get("nextContactDate"),
        )
        for item in logs
    ]


def _latest_value(events: List[Dict[str, str]], relation: str) -> Optional[str]:
    matched = [item["object_value"] for item in events if item["relation"] == relation]
    return matched[-1] if matched else None


def _build_stats(record: Dict[str, object]) -> List[dict]:
    events = record["events"]  # type: ignore[assignment]
    candidates = [
        ("stage", "疾病阶段"),
        ("med_adherence", "服药依从性"),
        ("support_system", "照护支持"),
        ("bp_sys_bin", "收缩压分层"),
        ("sleep_hours_bin", "睡眠分层"),
        ("medical_history", "既往病史"),
    ]
    stats = []
    for relation, label in candidates:
        value = _latest_value(events, relation)
        if not value:
            continue
        stats.append({"label": label, "value": value, "trend": "来自最近一次结构化事件"})
    return stats[:4]


def _build_timeline(record: Dict[str, object]) -> List[TimelineEvent]:
    timeline: List[TimelineEvent] = []
    for event in record["events"]:  # type: ignore[index]
        timeline.append(
            TimelineEvent(
                date=to_date(event["event_time"]),
                type=relation_type(event["relation"]),
                title="{0}: {1}".format(relation_label(event["relation"]), event["object_value"]),
                detail=event["note"] or "{0} -> {1}".format(event["relation"], event["object_value"]),
            )
        )
    return timeline


def _build_predictions(record: Dict[str, object]) -> List[dict]:
    disease = str(record["primaryDisease"])
    stage = str(record["currentStage"])
    risk = str(record["riskLevel"])
    base = 0.74 if risk == "高风险" else 0.61

    if disease == "Diabetes":
        return [
            {"label": "血糖控制波动上升", "score": base, "reason": "结合阶段、依从性和近期血压/支持系统事件综合给出。"},
            {"label": "复诊延迟风险增加", "score": base - 0.1, "reason": "门诊随访节奏需要继续强化。"},
            {"label": "并发症筛查优先级提升", "score": base - 0.18, "reason": "糖尿病中期患者需要更连续的检查提醒。"},
        ]
    if disease == "Alzheimer's":
        return [
            {"label": "认知功能继续下降", "score": base + 0.03, "reason": "病程阶段和照护/睡眠线索提示需要加强监测。"},
            {"label": "照护压力持续上升", "score": base - 0.08, "reason": "随病程推进，家属照护负担会继续增加。"},
            {"label": "夜间行为问题风险增加", "score": base - 0.16, "reason": "睡眠分层与当前阶段共同影响夜间症状。"},
        ]
    return [
        {"label": "步态波动与跌倒风险升高", "score": base + (0.04 if stage == "Late" else 0.0), "reason": "帕金森病阶段进展后需重点关注运动症状。"},
        {"label": "药效穿透期缩短", "score": base - 0.09, "reason": "建议结合复诊和依从性记录进一步评估。"},
        {"label": "居家照护强度增加", "score": base - 0.17, "reason": "病程阶段与支持系统共同决定后续照护需求。"},
    ]


def _build_followups(record: Dict[str, object]) -> List[dict]:
    last_visit = str(record["lastVisit"])
    risk = str(record["riskLevel"])
    if risk == "高风险":
        return [
            {"title": "7 天内完成重点复诊复核", "owner": "慢病门诊", "dueDate": last_visit, "priority": "high"},
            {"title": "补录结构化风险事件", "owner": "病案管理", "dueDate": last_visit, "priority": "high"},
            {"title": "核对家庭照护与用药执行", "owner": "随访护士", "dueDate": last_visit, "priority": "medium"},
        ]
    return [
        {"title": "14 天内完成常规复诊", "owner": "慢病门诊", "dueDate": last_visit, "priority": "medium"},
        {"title": "更新随访记录", "owner": "病案管理", "dueDate": last_visit, "priority": "medium"},
        {"title": "提醒生活方式管理", "owner": "随访护士", "dueDate": last_visit, "priority": "low"},
    ]


def _build_similar_cases(record: Dict[str, object]) -> List[dict]:
    return [
        {
            "caseId": "SIM-{0}".format(record["patientId"]),
            "disease": str(record["primaryDisease"]),
            "matchScore": 0.84 if str(record["dataSupport"]) != "low" else 0.78,
            "summary": "该相似病例来自 CHRONIC 同病种轨迹，用于辅助解释当前患者的病程走势。",
            "suggestion": "建议将相似病例路径与当前结构化事件一并展示，供医生复核。",
        }
    ]


def _build_advice(record: Dict[str, object]) -> List[str]:
    disease = str(record["primaryDisease"])
    support = str(record["dataSupport"])
    advice = ["先核对最近一次就诊后的关键事件，确保阶段、依从性和支持系统信息完整。"]
    if disease == "Diabetes":
        advice.append("建议优先查看血糖、血压和并发症筛查是否按计划完成。")
    elif disease == "Alzheimer's":
        advice.append("建议同步关注照护者负担、夜间睡眠和安全风险。")
    else:
        advice.append("建议重点核查步态变化、跌倒风险与用药调整记录。")
    if support == "low":
        advice.append("当前样本支持较弱，应优先补录 2 到 3 个结构化事件后再运行模型推理。")
    else:
        advice.append("可结合 T+1 预测结果和相似病例进行辅助决策，不替代医生最终判断。")
    return advice


def _build_path_explanation(record: Dict[str, object]) -> List[str]:
    steps = []
    for event in record["events"][-4:]:  # type: ignore[index]
        steps.append("{0} -> {1}: {2}".format(to_date(event["event_time"]), event["relation"], event["object_value"]))
    return steps


def _build_case(record: Dict[str, object]) -> PatientCase:
    recommendation_mode = "similar-case" if record["dataSupport"] == "low" else "model"
    profile = patient_profile_defaults(record)
    return PatientCase(
        patientId=str(record["patientId"]),
        name=str(record["name"]),
        age=int(record["age"]),
        gender=str(record["gender"]),
        avatarUrl=profile["avatarUrl"],
        phone=profile["phone"],
        emergencyContactName=profile["emergencyContactName"],
        emergencyContactRelation=profile["emergencyContactRelation"],
        emergencyContactPhone=profile["emergencyContactPhone"],
        identityMasked=profile["identityMasked"],
        insuranceType=profile["insuranceType"],
        department=profile["department"],
        primaryDoctor=profile["primaryDoctor"],
        caseManager=profile["caseManager"],
        medicalRecordNumber=str(record.get("medicalRecordNumber", record["patientId"])),
        archiveSource=str(record.get("archiveSource", "outpatient")),
        archiveStatus=str(record.get("archiveStatus", "active")),
        consentStatus=str(record.get("consentStatus", "signed")),
        allergyHistory=profile["allergyHistory"],
        familyHistory=profile["familyHistory"],
        primaryDisease=str(record["primaryDisease"]),
        currentStage=str(record["currentStage"]),
        riskLevel=str(record["riskLevel"]),
        lastVisit=str(record["lastVisit"]),
        summary=str(record["summary"]),
        dataSupport=str(record["dataSupport"]),
        encounterStatus=ENCOUNTER_STATUS.get(str(record["patientId"]), _default_encounter_status(record)),
        stats=_build_stats(record),
        timeline=_build_timeline(record),
        predictions=_build_predictions(record),
        pathExplanation=_build_path_explanation(record),
        followUps=_build_followups(record),
        outpatientTasks=_build_outpatient_tasks(str(record["patientId"])),
        contactLogs=_build_contact_logs(record),
        auditLogs=_build_audit_logs(record),
        recommendationMode=recommendation_mode,
        careAdvice=_build_advice(record),
        similarCases=_build_similar_cases(record),
    )


def authenticate(username: str, password: str) -> Optional[DoctorPublic]:
    for doctor in DOCTORS:
        if doctor.username == username and verify_password(password, doctor.password_hash):
            return doctor.to_public()
    return None


def register_doctor(payload: RegisterRequest) -> Optional[DoctorPublic]:
    for doctor in DOCTORS:
        if doctor.username == payload.username:
            return None
    DOCTORS.append(
        DoctorRecord(
            username=payload.username,
            password_hash=hash_password(payload.password),
            name=payload.name,
            title=payload.title,
            department=payload.department,
            role=payload.role,
        )
    )
    return DoctorPublic(
        username=payload.username,
        name=payload.name,
        title=payload.title,
        department=payload.department,
        role=payload.role,
    )


def get_doctor(username: str) -> Optional[DoctorPublic]:
    for doctor in DOCTORS:
        if doctor.username == username:
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
            "patientId": str(record["patientId"]),
            "name": str(record["name"]),
            "age": int(record["age"]),
            "gender": str(record["gender"]),
            **patient_profile_defaults(record),
            "medicalRecordNumber": str(record.get("medicalRecordNumber", record["patientId"])),
            "archiveSource": str(record.get("archiveSource", "outpatient")),
            "archiveStatus": str(record.get("archiveStatus", "active")),
            "consentStatus": str(record.get("consentStatus", "signed")),
            "primaryDisease": str(record["primaryDisease"]),
            "currentStage": str(record["currentStage"]),
            "riskLevel": str(record["riskLevel"]),
            "lastVisit": str(record["lastVisit"]),
            "summary": str(record["summary"]),
            "dataSupport": str(record["dataSupport"]),
        }
        for record in sorted(PATIENT_RECORDS, key=lambda item: (str(item["lastVisit"]), str(item["patientId"])), reverse=True)
    ]


def get_patient(patient_id: str) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    return _build_case(record) if record else None


def get_timeline(patient_id: str) -> Optional[List[TimelineEvent]]:
    record = _find_record(patient_id)
    return _build_timeline(record) if record else None


def list_event_rows(patient_id: Optional[str] = None) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for record in PATIENT_RECORDS:
        if patient_id and record["patientId"] != patient_id:
            continue
        for event in record["events"]:  # type: ignore[index]
            rows.append(
                {
                    "patient_id": str(record["patientId"]),
                    "patient_name": str(record["name"]),
                    "event_time": event["event_time"],
                    "relation": event["relation"],
                    "object_value": event["object_value"],
                    "note": event["note"],
                    "source": event.get("source", "demo"),
                }
            )
    rows.sort(key=lambda item: item["event_time"], reverse=True)
    return rows


def save_patient(payload: PatientUpsertRequest) -> PatientCase:
    record = _find_record(payload.patientId)
    data = {
        "patientId": payload.patientId,
        "name": payload.name,
        "age": payload.age,
        "gender": payload.gender,
        "avatarUrl": payload.avatarUrl,
        "phone": payload.phone,
        "emergencyContactName": payload.emergencyContactName,
        "emergencyContactRelation": payload.emergencyContactRelation,
        "emergencyContactPhone": payload.emergencyContactPhone,
        "identityMasked": payload.identityMasked,
        "insuranceType": payload.insuranceType,
        "department": payload.department,
        "primaryDoctor": payload.primaryDoctor,
        "caseManager": payload.caseManager,
        "medicalRecordNumber": payload.medicalRecordNumber or payload.patientId,
        "archiveSource": payload.archiveSource or "outpatient",
        "archiveStatus": payload.archiveStatus or "active",
        "consentStatus": payload.consentStatus or "signed",
        "allergyHistory": payload.allergyHistory,
        "familyHistory": payload.familyHistory,
        "primaryDisease": payload.primaryDisease,
        "currentStage": payload.currentStage,
        "riskLevel": payload.riskLevel,
        "lastVisit": payload.lastVisit,
        "summary": payload.summary,
        "dataSupport": payload.dataSupport,
        "contactLogs": record.get("contactLogs", []) if record else [],
        "auditLogs": list(record.get("auditLogs", [])) if record else [],
        "events": record["events"] if record else [],
    }
    action = "archive_updated" if record else "archive_created"
    data["auditLogs"].insert(
        0,
        {
            "logId": "alog-{0}".format(uuid4().hex[:12]),
            "action": action,
            "operatorUsername": payload.actorUsername,
            "operatorName": payload.actorName,
            "detail": "Archive profile {0}.".format("updated" if record else "created"),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    if record:
        PATIENT_RECORDS.remove(record)
    PATIENT_RECORDS.insert(0, data)
    return _build_case(data)


def add_event(patient_id: str, payload: PatientEventCreateRequest) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    if not record:
        return None

    event_row = {
        "event_time": payload.eventTime.replace("T", " "),
        "relation": payload.relation,
        "object_value": payload.objectValue,
        "note": payload.note or "{0}: {1}".format(relation_label(payload.relation), payload.objectValue),
        "source": payload.source,
    }
    events = list(record["events"])  # type: ignore[arg-type]
    events.append(event_row)
    events.sort(key=lambda item: item["event_time"])
    record["events"] = events
    record["lastVisit"] = max(str(record["lastVisit"]), to_date(event_row["event_time"]))
    audit_logs = list(record.get("auditLogs", []))
    audit_logs.insert(
        0,
        {
            "logId": "alog-{0}".format(uuid4().hex[:12]),
            "action": "event_added",
            "operatorUsername": payload.actorUsername,
            "operatorName": payload.actorName,
            "detail": "Structured event added: {0} -> {1}".format(payload.relation, payload.objectValue),
            "createdAt": datetime.now(timezone.utc).isoformat(),
        },
    )
    record["auditLogs"] = audit_logs
    return _build_case(record)


def add_contact_log(patient_id: str, payload: ContactLogCreateRequest) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    if not record:
        return None

    contact_logs = list(record.get("contactLogs", []))
    contact_logs.insert(
        0,
        {
            "logId": "clog-{0}".format(uuid4().hex[:12]),
            "contactTime": payload.contactTime,
            "contactType": payload.contactType,
            "contactTarget": payload.contactTarget,
            "contactResult": payload.contactResult,
            "operatorUsername": payload.actorUsername,
            "operatorName": payload.actorName,
            "note": payload.note,
            "nextContactDate": payload.nextContactDate,
        },
    )
    record["contactLogs"] = contact_logs
    return _build_case(record)


def update_encounter_status(patient_id: str, payload: EncounterStatusUpdateRequest) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    if not record:
        return None
    ENCOUNTER_STATUS[patient_id] = payload.status
    return _build_case(record)


def add_outpatient_task(patient_id: str, payload: OutpatientTaskCreateRequest) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    if not record:
        return None
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    task_row = {
        "taskId": "task-{0}".format(uuid4().hex[:12]),
        "category": payload.category,
        "title": payload.title,
        "owner": payload.owner,
        "dueDate": payload.dueDate,
        "priority": payload.priority,
        "status": payload.status,
        "note": payload.note,
        "source": payload.source,
        "updatedBy": _actor_display_name(payload.actorUsername, payload.actorName),
        "updatedAt": created_at,
        "logs": [
            {
                "logId": "log-{0}".format(uuid4().hex[:12]),
                "action": "created",
                "actorUsername": payload.actorUsername,
                "actorName": payload.actorName,
                "createdAt": created_at,
                "note": payload.note,
            }
        ],
    }
    OUTPATIENT_TASKS.setdefault(patient_id, []).insert(0, task_row)
    return _build_case(record)


def update_outpatient_task_status(
    patient_id: str,
    task_id: str,
    payload: OutpatientTaskStatusUpdateRequest,
) -> Optional[PatientCase]:
    record = _find_record(patient_id)
    if not record:
        return None
    task_rows = OUTPATIENT_TASKS.get(patient_id, [])
    updated = False
    for item in task_rows:
        if item["taskId"] == task_id:
            item["status"] = payload.status
            item["updatedBy"] = _actor_display_name(payload.actorUsername, payload.actorName)
            item["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            logs = item.setdefault("logs", [])
            if isinstance(logs, list):
                logs.insert(
                    0,
                    {
                        "logId": "log-{0}".format(uuid4().hex[:12]),
                        "action": "completed" if payload.status == "已完成" else "closed",
                        "actorUsername": payload.actorUsername,
                        "actorName": payload.actorName,
                        "createdAt": item["updatedAt"],
                        "note": "状态更新为 {0}".format(payload.status),
                    },
                )
            updated = True
            break
    if not updated:
        return None
    if all(item["status"] in {"已完成", "已关闭"} for item in task_rows):
        if ENCOUNTER_STATUS.get(patient_id) in {"in_progress", "pending_review"}:
            ENCOUNTER_STATUS[patient_id] = "completed"
    return _build_case(record)


def get_followup_worklist_rows() -> List[dict]:
    rows: List[dict] = []
    for patient in PATIENT_RECORDS:
        patient_case = _build_case(patient)
        for task in patient_case.followUps:
            rows.append(
                {
                    "taskId": None,
                    "patientId": patient_case.patientId,
                    "patientName": patient_case.name,
                    "primaryDisease": patient_case.primaryDisease,
                    "riskLevel": patient_case.riskLevel,
                    "dataSupport": patient_case.dataSupport,
                    "dueDate": task.dueDate,
                    "owner": task.owner,
                    "priority": task.priority,
                    "taskType": task.title,
                    "status": "待处理",
                    "source": "followup",
                }
            )
        for task in patient_case.outpatientTasks:
            rows.append(
                {
                    "taskId": task.taskId,
                    "patientId": patient_case.patientId,
                    "patientName": patient_case.name,
                    "primaryDisease": patient_case.primaryDisease,
                    "riskLevel": patient_case.riskLevel,
                    "dataSupport": patient_case.dataSupport,
                    "dueDate": task.dueDate,
                    "owner": task.owner,
                    "priority": task.priority,
                    "taskType": "检查申请" if task.category == "exam" else "复查计划",
                    "status": task.status,
                    "source": "outpatient-task",
                    "lastActionBy": task.updatedBy,
                    "lastActionAt": task.updatedAt,
                }
            )
    return rows


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


def maintenance_overview() -> MaintenanceOverviewResponse:
    patients = list_patients()
    events = list_event_rows()
    high_risk_count = sum(1 for item in patients if item["riskLevel"] == "高风险")
    low_support_count = sum(1 for item in patients if item["dataSupport"] == "low")
    overdue_count = sum(1 for item in patients if item["lastVisit"] <= "2025-03-09")

    disease_counter: Dict[str, int] = {}
    relation_counter: Dict[str, int] = {}
    for item in patients:
        disease_counter[item["primaryDisease"]] = disease_counter.get(item["primaryDisease"], 0) + 1
    for event in events:
        relation_counter[event["relation"]] = relation_counter.get(event["relation"], 0) + 1

    return MaintenanceOverviewResponse(
        mode="demo",
        modelAvailable=True,
        modelError=None,
        patientCount=len(patients),
        eventCount=len(events),
        highRiskCount=high_risk_count,
        lowSupportCount=low_support_count,
        overdueFollowupCount=overdue_count,
        topDiseases=[
            MaintenanceCountItem(label=label, value=value)
            for label, value in sorted(disease_counter.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        relationStats=[
            MaintenanceRelationStat(relation=relation, label=relation_label(relation), count=count)
            for relation, count in sorted(relation_counter.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        recentPatients=[
            MaintenancePatientRow(**item)
            for item in patients[:6]
        ],
        recentEvents=[
            MaintenanceEventRow(
                patientId=item["patient_id"],
                patientName=item["patient_name"],
                eventTime=item["event_time"].replace(" ", "T"),
                relation=item["relation"],
                relationLabel=relation_label(item["relation"]),
                objectValue=item["object_value"],
                source=item["source"],
            )
            for item in events[:10]
        ],
    )


def _build_master_index_alerts(
    patients: List[dict],
) -> tuple[int, int, int, Dict[str, int], List[MaintenanceIdentityAlertRow]]:
    missing_mrn_count = 0
    pending_consent_count = 0
    source_counter: Dict[str, int] = {}
    phone_groups: Dict[str, List[dict]] = {}
    alerts: List[MaintenanceIdentityAlertRow] = []

    for item in patients:
        source_key = str(item.get("archiveSource") or "unknown")
        source_counter[source_key] = source_counter.get(source_key, 0) + 1

        if not item.get("medicalRecordNumber"):
            missing_mrn_count += 1
            alerts.append(
                MaintenanceIdentityAlertRow(
                    patientId=item["patientId"],
                    name=item["name"],
                    issueType="missing_mrn",
                    issueLabel="缺失 MRN",
                    detail="患者主索引尚未补齐病案号，需优先完成主索引维护。",
                    archiveSource=source_key,
                )
            )

        if item.get("consentStatus") == "pending":
            pending_consent_count += 1
            alerts.append(
                MaintenanceIdentityAlertRow(
                    patientId=item["patientId"],
                    name=item["name"],
                    issueType="pending_consent",
                    issueLabel="待签知情同意",
                    detail="档案已建立，但知情同意状态仍需补齐。",
                    archiveSource=source_key,
                )
            )

        phone_value = str(item.get("phone") or "").strip()
        if phone_value:
            phone_groups.setdefault(phone_value, []).append(item)

    duplicate_groups = [group for group in phone_groups.values() if len(group) > 1]
    duplicate_risk_count = sum(len(group) for group in duplicate_groups)
    for group in duplicate_groups:
        for item in group:
            alerts.append(
                MaintenanceIdentityAlertRow(
                    patientId=item["patientId"],
                    name=item["name"],
                    issueType="duplicate_phone",
                    issueLabel="疑似重复主数据",
                    detail=f"联系电话 {item['phone']} 与其他档案重复，建议核对患者主索引。",
                    archiveSource=str(item.get("archiveSource") or "unknown"),
                )
            )

    return missing_mrn_count, pending_consent_count, duplicate_risk_count, source_counter, alerts[:8]


def maintenance_overview() -> MaintenanceOverviewResponse:
    patients = list_patients()
    events = list_event_rows()
    high_risk_count = sum(1 for item in patients if "高" in item["riskLevel"] or "high" in item["riskLevel"].lower())
    low_support_count = sum(1 for item in patients if item["dataSupport"] == "low")
    overdue_count = sum(1 for item in patients if item["lastVisit"] <= "2025-03-09")
    missing_mrn_count, pending_consent_count, duplicate_risk_count, source_counter, alerts = _build_master_index_alerts(
        patients
    )

    disease_counter: Dict[str, int] = {}
    relation_counter: Dict[str, int] = {}
    for item in patients:
        disease_counter[item["primaryDisease"]] = disease_counter.get(item["primaryDisease"], 0) + 1
    for event in events:
        relation_counter[event["relation"]] = relation_counter.get(event["relation"], 0) + 1

    return MaintenanceOverviewResponse(
        mode="demo",
        modelAvailable=True,
        modelError=None,
        patientCount=len(patients),
        eventCount=len(events),
        highRiskCount=high_risk_count,
        lowSupportCount=low_support_count,
        overdueFollowupCount=overdue_count,
        missingMrnCount=missing_mrn_count,
        pendingConsentCount=pending_consent_count,
        duplicateRiskCount=duplicate_risk_count,
        topDiseases=[
            MaintenanceCountItem(label=label, value=value)
            for label, value in sorted(disease_counter.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        sourceStats=[
            MaintenanceCountItem(label=label, value=value)
            for label, value in sorted(source_counter.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        relationStats=[
            MaintenanceRelationStat(relation=relation, label=relation_label(relation), count=count)
            for relation, count in sorted(relation_counter.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        recentPatients=[MaintenancePatientRow(**item) for item in patients[:6]],
        masterIndexAlerts=alerts,
        recentEvents=[
            MaintenanceEventRow(
                patientId=item["patient_id"],
                patientName=item["patient_name"],
                eventTime=item["event_time"].replace(" ", "T"),
                relation=item["relation"],
                relationLabel=relation_label(item["relation"]),
                objectValue=item["object_value"],
                source=item["source"],
            )
            for item in events[:10]
        ],
    )
