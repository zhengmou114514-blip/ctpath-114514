from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from . import demo_store
from .model_service import MODEL_SERVICE
from .security import hash_password, is_hashed_password, verify_password
from .schemas import (
    ContactLog,
    ContactLogCreateRequest,
    DoctorPublic,
    EncounterStatusUpdateRequest,
    ExperimentMetric,
    FlowBoardResponse,
    FlowBoardRow,
    FollowupTaskRow,
    FollowupWorklistResponse,
    MaintenanceCountItem,
    MaintenanceEventRow,
    MaintenanceIdentityAlertRow,
    MaintenanceOverviewResponse,
    MaintenancePatientRow,
    MaintenanceRelationStat,
    ModelMetricsResponse,
    OutpatientTask,
    OutpatientTaskCreateRequest,
    OutpatientTaskLog,
    OutpatientTaskStatusUpdateRequest,
    PatientAuditLog,
    PatientCase,
    PatientEventCreateRequest,
    PatientQuadruple,
    PatientUpsertRequest,
    RegisterRequest,
    TimelineEvent,
)
from .services.suggestion_service import SuggestionService

try:
    from sqlalchemy import create_engine, text
except Exception:  # pragma: no cover
    create_engine = None
    text = None


DB_URL = os.getenv("CTPATH_DB_URL", "")
TOKENS: Dict[str, str] = {}
STORE = None
SUGGESTION_SERVICE = SuggestionService()

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


class MySQLStore:
    def __init__(self, db_url: str) -> None:
        if not create_engine or not text:
            raise RuntimeError("sqlalchemy is not installed")
        self.engine = create_engine(db_url, pool_pre_ping=True, future=True)
        self._table_columns_cache: Dict[str, set[str]] = {}

    def _fetch_all(self, query: str, **params: Any) -> List[Dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(text(query), params).mappings().all()
        return [dict(row) for row in rows]

    def _fetch_one(self, query: str, **params: Any) -> Optional[Dict[str, Any]]:
        rows = self._fetch_all(query, **params)
        return rows[0] if rows else None

    def _execute(self, query: str, **params: Any) -> None:
        with self.engine.begin() as conn:
            conn.execute(text(query), params)

    def _table_columns(self, table_name: str) -> set[str]:
        cached = self._table_columns_cache.get(table_name)
        if cached is not None:
            return cached
        rows = self._fetch_all(
            """
            SELECT COLUMN_NAME AS columnName
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = :table_name
            """,
            table_name=table_name,
        )
        columns = {str(row["columnName"]).lower() for row in rows}
        self._table_columns_cache[table_name] = columns
        return columns

    def _has_columns(self, table_name: str, *columns: str) -> bool:
        existing_columns = self._table_columns(table_name)
        return all(column.lower() in existing_columns for column in columns)

    def _supports_patient_profile_fields(self) -> bool:
        return self._has_columns(
            "patients",
            "avatar_url",
            "phone",
            "emergency_contact_name",
            "emergency_contact_relation",
            "emergency_contact_phone",
            "identity_masked",
            "insurance_type",
            "department",
            "primary_doctor",
            "case_manager",
            "medical_record_number",
            "archive_source",
            "archive_status",
            "consent_status",
            "allergy_history",
            "family_history",
        )

    def _supports_patient_audit_logs(self) -> bool:
        return self._has_columns(
            "patient_audit_logs",
            "log_id",
            "patient_id",
            "action",
            "operator_username",
            "operator_name",
            "detail",
            "created_at",
        )

    def _apply_patient_profile_defaults(self, item: Dict[str, Any]) -> Dict[str, Any]:
        item["avatarUrl"] = item.get("avatarUrl", "") or ""
        item["phone"] = item.get("phone", "") or ""
        item["emergencyContactName"] = item.get("emergencyContactName", "") or ""
        item["emergencyContactRelation"] = item.get("emergencyContactRelation", "") or ""
        item["emergencyContactPhone"] = item.get("emergencyContactPhone", "") or ""
        item["identityMasked"] = item.get("identityMasked", "") or ""
        item["insuranceType"] = item.get("insuranceType", "") or ""
        item["department"] = item.get("department", "") or ""
        item["primaryDoctor"] = item.get("primaryDoctor", "") or ""
        item["caseManager"] = item.get("caseManager", "") or ""
        item["medicalRecordNumber"] = item.get("medicalRecordNumber", "") or ""
        item["archiveSource"] = item.get("archiveSource", "") or ""
        item["archiveStatus"] = item.get("archiveStatus", "") or ""
        item["consentStatus"] = item.get("consentStatus", "") or ""
        item["allergyHistory"] = item.get("allergyHistory", "") or ""
        item["familyHistory"] = item.get("familyHistory", "") or ""
        return item

    def authenticate(self, username: str, password: str) -> Optional[DoctorPublic]:
        if self._has_columns("doctor_users", "role"):
            row = self._fetch_one(
                """
                SELECT username, password_hash, name, title, department, role
                FROM doctor_users
                WHERE username = :username
                """,
                username=username,
            )
        else:
            row = self._fetch_one(
                """
                SELECT username, password_hash, name, title, department
                FROM doctor_users
                WHERE username = :username
                """,
                username=username,
            )
        if not row or not verify_password(password, row["password_hash"]):
            return None
        if not is_hashed_password(row["password_hash"]):
            self._execute(
                """
                UPDATE doctor_users
                SET password_hash = :password_hash
                WHERE username = :username
                """,
                username=username,
                password_hash=hash_password(password),
            )
        return DoctorPublic(
            username=row["username"],
            name=row["name"],
            title=row["title"],
            department=row["department"],
            role=row.get("role") or "doctor",
        )

    def register_doctor(self, payload: RegisterRequest) -> Optional[DoctorPublic]:
        existing = self._fetch_one(
            """
            SELECT username
            FROM doctor_users
            WHERE username = :username
            """,
            username=payload.username,
        )
        if existing:
            return None
        if self._has_columns("doctor_users", "role"):
            self._execute(
                """
                INSERT INTO doctor_users (username, password_hash, name, title, department, role)
                VALUES (:username, :password_hash, :name, :title, :department, :role)
                """,
                username=payload.username,
                password_hash=hash_password(payload.password),
                name=payload.name,
                title=payload.title,
                department=payload.department,
                role=payload.role,
            )
        else:
            self._execute(
                """
                INSERT INTO doctor_users (username, password_hash, name, title, department)
                VALUES (:username, :password_hash, :name, :title, :department)
                """,
                username=payload.username,
                password_hash=hash_password(payload.password),
                name=payload.name,
                title=payload.title,
                department=payload.department,
            )
        return DoctorPublic(
            username=payload.username,
            name=payload.name,
            title=payload.title,
            department=payload.department,
            role=payload.role,
        )

    def get_doctor(self, username: str) -> Optional[DoctorPublic]:
        if self._has_columns("doctor_users", "role"):
            row = self._fetch_one(
                """
                SELECT username, name, title, department, role
                FROM doctor_users
                WHERE username = :username
                """,
                username=username,
            )
        else:
            row = self._fetch_one(
                """
                SELECT username, name, title, department
                FROM doctor_users
                WHERE username = :username
                """,
                username=username,
            )
        if not row:
            return None
        return DoctorPublic(
            username=row["username"],
            name=row["name"],
            title=row["title"],
            department=row["department"],
            role=row.get("role") or "doctor",
        )

    def list_patients(self) -> List[dict]:
        if self._supports_patient_profile_fields():
            rows = self._fetch_all(
                """
                SELECT patient_id AS patientId,
                       name,
                       age,
                       gender,
                       COALESCE(avatar_url, '') AS avatarUrl,
                       COALESCE(phone, '') AS phone,
                       COALESCE(emergency_contact_name, '') AS emergencyContactName,
                       COALESCE(emergency_contact_relation, '') AS emergencyContactRelation,
                       COALESCE(emergency_contact_phone, '') AS emergencyContactPhone,
                       COALESCE(identity_masked, '') AS identityMasked,
                       COALESCE(insurance_type, '') AS insuranceType,
                       COALESCE(department, '') AS department,
                       COALESCE(primary_doctor, '') AS primaryDoctor,
                       COALESCE(case_manager, '') AS caseManager,
                       COALESCE(medical_record_number, '') AS medicalRecordNumber,
                       COALESCE(archive_source, '') AS archiveSource,
                       COALESCE(archive_status, '') AS archiveStatus,
                       COALESCE(consent_status, '') AS consentStatus,
                       COALESCE(allergy_history, '') AS allergyHistory,
                       COALESCE(family_history, '') AS familyHistory,
                       primary_disease AS primaryDisease,
                       current_stage AS currentStage,
                       risk_level AS riskLevel,
                       DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                       summary,
                       data_support AS dataSupport
                FROM patients
                ORDER BY last_visit DESC, patient_id ASC
                """
            )
            return [self._apply_patient_profile_defaults(item) for item in rows]
        rows = self._fetch_all(
            """
            SELECT patient_id AS patientId,
                   name,
                   age,
                   gender,
                   primary_disease AS primaryDisease,
                   current_stage AS currentStage,
                   risk_level AS riskLevel,
                   DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                   summary,
                   data_support AS dataSupport
            FROM patients
            ORDER BY last_visit DESC, patient_id ASC
            """
        )
        for item in rows:
            self._apply_patient_profile_defaults(item)
        return rows

    def get_patient_row(self, patient_id: str) -> Optional[Dict[str, Any]]:
        if self._supports_patient_profile_fields():
            item = self._fetch_one(
                """
                SELECT patient_id AS patientId,
                       name,
                       age,
                       gender,
                       COALESCE(avatar_url, '') AS avatarUrl,
                       COALESCE(phone, '') AS phone,
                       COALESCE(emergency_contact_name, '') AS emergencyContactName,
                       COALESCE(emergency_contact_relation, '') AS emergencyContactRelation,
                       COALESCE(emergency_contact_phone, '') AS emergencyContactPhone,
                       COALESCE(identity_masked, '') AS identityMasked,
                       COALESCE(insurance_type, '') AS insuranceType,
                       COALESCE(department, '') AS department,
                       COALESCE(primary_doctor, '') AS primaryDoctor,
                       COALESCE(case_manager, '') AS caseManager,
                       COALESCE(medical_record_number, '') AS medicalRecordNumber,
                       COALESCE(archive_source, '') AS archiveSource,
                       COALESCE(archive_status, '') AS archiveStatus,
                       COALESCE(consent_status, '') AS consentStatus,
                       COALESCE(allergy_history, '') AS allergyHistory,
                       COALESCE(family_history, '') AS familyHistory,
                       primary_disease AS primaryDisease,
                       current_stage AS currentStage,
                       risk_level AS riskLevel,
                       DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                       summary,
                       data_support AS dataSupport
                FROM patients
                WHERE patient_id = :patient_id
                """,
                patient_id=patient_id,
            )
            return self._apply_patient_profile_defaults(item) if item else None
        item = self._fetch_one(
            """
            SELECT patient_id AS patientId,
                   name,
                   age,
                   gender,
                   primary_disease AS primaryDisease,
                   current_stage AS currentStage,
                   risk_level AS riskLevel,
                   DATE_FORMAT(last_visit, '%Y-%m-%d') AS lastVisit,
                   summary,
                   data_support AS dataSupport
            FROM patients
            WHERE patient_id = :patient_id
            """,
            patient_id=patient_id,
        )
        if item:
            self._apply_patient_profile_defaults(item)
        return item

    def get_events(self, patient_id: str) -> List[dict]:
        return self._fetch_all(
            """
            SELECT id, event_time, relation, object_value, note, source
            FROM patient_events
            WHERE patient_id = :patient_id
            ORDER BY event_time ASC, id ASC
            """,
            patient_id=patient_id,
        )

    def save_patient(self, payload: PatientUpsertRequest) -> dict:
        params = dict(
            patient_id=payload.patientId,
            name=payload.name,
            gender=payload.gender,
            age=payload.age,
            avatar_url=payload.avatarUrl,
            phone=payload.phone,
            emergency_contact_name=payload.emergencyContactName,
            emergency_contact_relation=payload.emergencyContactRelation,
            emergency_contact_phone=payload.emergencyContactPhone,
            identity_masked=payload.identityMasked,
            insurance_type=payload.insuranceType,
            department=payload.department,
            primary_doctor=payload.primaryDoctor,
            case_manager=payload.caseManager,
            medical_record_number=payload.medicalRecordNumber,
            archive_source=payload.archiveSource,
            archive_status=payload.archiveStatus,
            consent_status=payload.consentStatus,
            allergy_history=payload.allergyHistory,
            family_history=payload.familyHistory,
            primary_disease=payload.primaryDisease,
            current_stage=payload.currentStage,
            risk_level=payload.riskLevel,
            last_visit=payload.lastVisit,
            summary=payload.summary,
            data_support=payload.dataSupport,
        )
        existing = self.get_patient_row(payload.patientId)
        if self._supports_patient_profile_fields():
            self._execute(
                """
                INSERT INTO patients (
                  patient_id, name, gender, age, avatar_url, phone,
                  emergency_contact_name, emergency_contact_relation, emergency_contact_phone,
                  identity_masked, insurance_type, department, primary_doctor, case_manager,
                  medical_record_number, archive_source, archive_status, consent_status,
                  allergy_history, family_history,
                  primary_disease, current_stage, risk_level, last_visit, summary, data_support
                ) VALUES (
                  :patient_id, :name, :gender, :age, :avatar_url, :phone,
                  :emergency_contact_name, :emergency_contact_relation, :emergency_contact_phone,
                  :identity_masked, :insurance_type, :department, :primary_doctor, :case_manager,
                  :medical_record_number, :archive_source, :archive_status, :consent_status,
                  :allergy_history, :family_history,
                  :primary_disease, :current_stage, :risk_level, :last_visit, :summary, :data_support
                )
                ON DUPLICATE KEY UPDATE
                  name = VALUES(name),
                  gender = VALUES(gender),
                  age = VALUES(age),
                  avatar_url = VALUES(avatar_url),
                  phone = VALUES(phone),
                  emergency_contact_name = VALUES(emergency_contact_name),
                  emergency_contact_relation = VALUES(emergency_contact_relation),
                  emergency_contact_phone = VALUES(emergency_contact_phone),
                  identity_masked = VALUES(identity_masked),
                  insurance_type = VALUES(insurance_type),
                  department = VALUES(department),
                  primary_doctor = VALUES(primary_doctor),
                  case_manager = VALUES(case_manager),
                  medical_record_number = VALUES(medical_record_number),
                  archive_source = VALUES(archive_source),
                  archive_status = VALUES(archive_status),
                  consent_status = VALUES(consent_status),
                  allergy_history = VALUES(allergy_history),
                  family_history = VALUES(family_history),
                  primary_disease = VALUES(primary_disease),
                  current_stage = VALUES(current_stage),
                  risk_level = VALUES(risk_level),
                  last_visit = VALUES(last_visit),
                  summary = VALUES(summary),
                  data_support = VALUES(data_support)
                """,
                **params,
            )
        else:
            self._execute(
                """
                INSERT INTO patients (
                  patient_id, name, gender, age, primary_disease, current_stage,
                  risk_level, last_visit, summary, data_support
                ) VALUES (
                  :patient_id, :name, :gender, :age, :primary_disease, :current_stage,
                  :risk_level, :last_visit, :summary, :data_support
                )
                ON DUPLICATE KEY UPDATE
                  name = VALUES(name),
                  gender = VALUES(gender),
                  age = VALUES(age),
                  primary_disease = VALUES(primary_disease),
                  current_stage = VALUES(current_stage),
                  risk_level = VALUES(risk_level),
                  last_visit = VALUES(last_visit),
                  summary = VALUES(summary),
                  data_support = VALUES(data_support)
                """,
                **params,
            )
        if self._supports_patient_audit_logs():
            action = "archive_updated" if existing else "archive_created"
            detail = "Archive profile {0}.".format("updated" if existing else "created")
            self.add_patient_audit_log(
                payload.patientId,
                action=action,
                detail=detail,
                operator_username=payload.actorUsername,
                operator_name=payload.actorName,
            )
        return self.get_patient_row(payload.patientId) or payload.model_dump()

    def add_event(self, patient_id: str, payload: PatientEventCreateRequest) -> None:
        self._execute(
            """
            INSERT INTO patient_events (
              patient_id, event_time, relation, object_value, note, source
            ) VALUES (
              :patient_id, :event_time, :relation, :object_value, :note, :source
            )
            """,
            patient_id=patient_id,
            event_time=payload.eventTime,
            relation=payload.relation,
            object_value=payload.objectValue,
            note=payload.note,
            source=payload.source,
        )
        self._execute(
            """
            UPDATE patients
            SET last_visit = GREATEST(last_visit, DATE(:event_time))
            WHERE patient_id = :patient_id
            """,
            patient_id=patient_id,
            event_time=payload.eventTime,
        )
        if self._supports_patient_audit_logs():
            self.add_patient_audit_log(
                patient_id,
                action="event_added",
                detail="Structured event added: {0} -> {1}".format(payload.relation, payload.objectValue),
                operator_username=payload.actorUsername,
                operator_name=payload.actorName,
            )

    def add_patient_audit_log(
        self,
        patient_id: str,
        action: str,
        detail: str,
        operator_username: Optional[str] = None,
        operator_name: Optional[str] = None,
    ) -> None:
        if not self._supports_patient_audit_logs():
            return
        self._execute(
            """
            INSERT INTO patient_audit_logs (
              log_id, patient_id, action, operator_username, operator_name, detail
            ) VALUES (
              :log_id, :patient_id, :action, :operator_username, :operator_name, :detail
            )
            """,
            log_id="alog-{0}".format(uuid4().hex[:12]),
            patient_id=patient_id,
            action=action,
            operator_username=operator_username,
            operator_name=operator_name,
            detail=detail,
        )

    def list_patient_audit_logs(self, patient_id: str) -> List[dict]:
        if not self._supports_patient_audit_logs():
            return []
        return self._fetch_all(
            """
            SELECT log_id AS logId,
                   action,
                   operator_username AS operatorUsername,
                   operator_name AS operatorName,
                   detail,
                   DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%s') AS createdAt
            FROM patient_audit_logs
            WHERE patient_id = :patient_id
            ORDER BY created_at DESC, log_id DESC
            """,
            patient_id=patient_id,
        )

    def list_recent_events(self, limit: int = 10) -> List[dict]:
        return self._fetch_all(
            """
            SELECT e.patient_id AS patientId,
                   p.name AS patientName,
                   DATE_FORMAT(e.event_time, '%Y-%m-%dT%H:%i:%s') AS eventTime,
                   e.relation AS relation,
                   e.object_value AS objectValue,
                   e.source AS source
            FROM patient_events e
            JOIN patients p ON p.patient_id = e.patient_id
            ORDER BY e.event_time DESC, e.id DESC
            LIMIT :limit_value
            """,
            limit_value=limit,
        )

    def get_encounter_status(self, patient_id: str) -> Optional[str]:
        row = self._fetch_one(
            """
            SELECT encounter_status AS encounterStatus
            FROM patient_encounter_state
            WHERE patient_id = :patient_id
            """,
            patient_id=patient_id,
        )
        if not row:
            return None
        return row["encounterStatus"]

    def set_encounter_status(self, patient_id: str, status: str) -> None:
        self._execute(
            """
            INSERT INTO patient_encounter_state (patient_id, encounter_status)
            VALUES (:patient_id, :encounter_status)
            ON DUPLICATE KEY UPDATE
              encounter_status = VALUES(encounter_status),
              updated_at = CURRENT_TIMESTAMP
            """,
            patient_id=patient_id,
            encounter_status=status,
        )

    def list_outpatient_tasks(self, patient_id: Optional[str] = None) -> List[dict]:
        params: Dict[str, Any] = {}
        query = """
            SELECT task_id AS taskId,
                   patient_id AS patientId,
                   category,
                   title,
                   owner,
                   DATE_FORMAT(due_date, '%Y-%m-%d') AS dueDate,
                   priority,
                   status,
                   note,
                   source,
                   updated_by AS updatedBy,
                   DATE_FORMAT(updated_at, '%Y-%m-%dT%H:%i:%s') AS updatedAt
            FROM outpatient_tasks
        """
        if patient_id:
            query += " WHERE patient_id = :patient_id"
            params["patient_id"] = patient_id
        query += " ORDER BY due_date ASC, created_at DESC"
        if self._has_columns("outpatient_tasks", "updated_by"):
            rows = self._fetch_all(query, **params)
        else:
            fallback_query = """
                SELECT task_id AS taskId,
                       patient_id AS patientId,
                       category,
                       title,
                       owner,
                       DATE_FORMAT(due_date, '%Y-%m-%d') AS dueDate,
                       priority,
                       status,
                       note,
                       source,
                       NULL AS updatedBy,
                       DATE_FORMAT(updated_at, '%Y-%m-%dT%H:%i:%s') AS updatedAt
                FROM outpatient_tasks
            """
            if patient_id:
                fallback_query += " WHERE patient_id = :patient_id"
            fallback_query += " ORDER BY due_date ASC, created_at DESC"
            rows = self._fetch_all(fallback_query, **params)
        for item in rows:
            if self._has_columns("outpatient_task_logs", "actor_username", "actor_name", "created_at", "note"):
                item["logs"] = self._fetch_all(
                    """
                    SELECT log_id AS logId,
                           action,
                           actor_username AS actorUsername,
                           actor_name AS actorName,
                           DATE_FORMAT(created_at, '%Y-%m-%dT%H:%i:%s') AS createdAt,
                           COALESCE(note, '') AS note
                    FROM outpatient_task_logs
                    WHERE task_id = :task_id
                    ORDER BY created_at DESC, log_id DESC
                    """,
                    task_id=item["taskId"],
                )
            else:
                item["logs"] = []
        return rows

    def add_outpatient_task(self, patient_id: str, payload: OutpatientTaskCreateRequest) -> str:
        task_id = "task-{0}".format(uuid4().hex[:12])
        self._execute(
            """
            INSERT INTO outpatient_tasks (
              task_id, patient_id, category, title, owner, due_date,
              priority, status, note, source, updated_by
            ) VALUES (
              :task_id, :patient_id, :category, :title, :owner, :due_date,
              :priority, :status, :note, :source, :updated_by
            )
            """,
            task_id=task_id,
            patient_id=patient_id,
            category=payload.category,
            title=payload.title,
            owner=payload.owner,
            due_date=payload.dueDate,
            priority=payload.priority,
            status=payload.status,
            note=payload.note,
            source=payload.source,
            updated_by=_actor_display_name(payload.actorUsername, payload.actorName),
        )
        self._execute(
            """
            INSERT INTO outpatient_task_logs (
              log_id, task_id, patient_id, action, actor_username, actor_name, note
            ) VALUES (
              :log_id, :task_id, :patient_id, :action, :actor_username, :actor_name, :note
            )
            """,
            log_id="log-{0}".format(uuid4().hex[:12]),
            task_id=task_id,
            patient_id=patient_id,
            action="created",
            actor_username=payload.actorUsername,
            actor_name=payload.actorName,
            note=payload.note,
        )
        return task_id

    def update_outpatient_task_status(
        self,
        patient_id: str,
        task_id: str,
        payload: OutpatientTaskStatusUpdateRequest,
    ) -> None:
        self._execute(
            """
            UPDATE outpatient_tasks
            SET status = :status,
                updated_by = :updated_by,
                updated_at = CURRENT_TIMESTAMP
            WHERE patient_id = :patient_id
              AND task_id = :task_id
            """,
            patient_id=patient_id,
            task_id=task_id,
            status=payload.status,
            updated_by=_actor_display_name(payload.actorUsername, payload.actorName),
        )
        self._execute(
            """
            INSERT INTO outpatient_task_logs (
              log_id, task_id, patient_id, action, actor_username, actor_name, note
            ) VALUES (
              :log_id, :task_id, :patient_id, :action, :actor_username, :actor_name, :note
            )
            """,
            log_id="log-{0}".format(uuid4().hex[:12]),
            task_id=task_id,
            patient_id=patient_id,
            action="completed" if payload.status == "已完成" else "closed",
            actor_username=payload.actorUsername,
            actor_name=payload.actorName,
            note="状态更新为 {0}".format(payload.status),
        )

    def list_contact_logs(self, patient_id: str) -> List[dict]:
        if not self._has_columns(
            "patient_contact_logs",
            "contact_time",
            "contact_type",
            "contact_target",
            "contact_result",
            "operator_username",
            "operator_name",
            "next_contact_date",
        ):
            return []
        return self._fetch_all(
            """
            SELECT log_id AS logId,
                   DATE_FORMAT(contact_time, '%Y-%m-%dT%H:%i:%s') AS contactTime,
                   contact_type AS contactType,
                   contact_target AS contactTarget,
                   contact_result AS contactResult,
                   operator_username AS operatorUsername,
                   operator_name AS operatorName,
                   COALESCE(note, '') AS note,
                   DATE_FORMAT(next_contact_date, '%Y-%m-%d') AS nextContactDate
            FROM patient_contact_logs
            WHERE patient_id = :patient_id
            ORDER BY contact_time DESC, created_at DESC
            """,
            patient_id=patient_id,
        )

    def add_contact_log(self, patient_id: str, payload: ContactLogCreateRequest) -> str:
        log_id = "clog-{0}".format(uuid4().hex[:12])
        self._execute(
            """
            INSERT INTO patient_contact_logs (
              log_id, patient_id, contact_time, contact_type, contact_target, contact_result,
              operator_username, operator_name, note, next_contact_date
            ) VALUES (
              :log_id, :patient_id, :contact_time, :contact_type, :contact_target, :contact_result,
              :operator_username, :operator_name, :note, :next_contact_date
            )
            """,
            log_id=log_id,
            patient_id=patient_id,
            contact_time=payload.contactTime,
            contact_type=payload.contactType,
            contact_target=payload.contactTarget,
            contact_result=payload.contactResult,
            operator_username=payload.actorUsername,
            operator_name=payload.actorName,
            note=payload.note,
            next_contact_date=payload.nextContactDate,
        )
        return log_id


def _current_store() -> Optional[MySQLStore]:
    global STORE
    if STORE is not None:
        return STORE
    if not DB_URL:
        return None
    try:
        STORE = MySQLStore(DB_URL)
        return STORE
    except Exception:
        return None


def _issue_token(username: str) -> str:
    token = "ctpath-{0}-{1}".format(username, datetime.now(timezone.utc).timestamp())
    TOKENS[token] = username
    return token


def _relation_label(relation: str) -> str:
    return RELATION_LABELS.get(relation, relation)


def _relation_type(relation: str) -> str:
    return demo_store.relation_type(relation)


def _format_date(value: Any) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d")
    return str(value)[:10]


def _format_datetime(value: Any) -> str:
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%dT%H:%M:%S")
    return str(value).replace(" ", "T")


def _actor_display_name(username: Optional[str], name: Optional[str]) -> Optional[str]:
    if name:
        return name
    if username:
        return username
    return None


def _default_encounter_status(patient: Dict[str, Any]) -> str:
    if patient.get("dataSupport") == "low":
        return "pending_review"
    return "waiting"


def _encounter_status_label(status: str) -> str:
    if status == "in_progress":
        return "接诊中"
    if status == "pending_review":
        return "待复核"
    if status == "completed":
        return "已完成"
    return "候诊"


def _encounter_next_action(status: str, outpatient_tasks: List[OutpatientTask], fallback: str) -> str:
    pending_tasks = [item for item in outpatient_tasks if item.status not in {"已完成", "已关闭"}]
    if pending_tasks:
        first = pending_tasks[0]
        return "{0}：{1}".format("检查申请" if first.category == "exam" else "复查计划", first.title)
    if status == "in_progress":
        return "继续完成本次接诊记录与预测复核"
    if status == "pending_review":
        return "优先补录结构化事件并完成复核"
    if status == "completed":
        return "等待下次复诊或随访触发"
    return fallback


def _build_outpatient_tasks(rows: List[Dict[str, Any]]) -> List[OutpatientTask]:
    return [
        OutpatientTask(
            taskId=str(item["taskId"]),
            category=str(item["category"]),
            title=str(item["title"]),
            owner=str(item["owner"]),
            dueDate=str(item["dueDate"]),
            priority=str(item["priority"]),
            status=str(item["status"]),
            note=str(item.get("note") or ""),
            source=str(item.get("source") or "ehr"),
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
        for item in rows
    ]


def _build_contact_logs(rows: List[Dict[str, Any]]) -> List[ContactLog]:
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
        for item in rows
    ]


def _build_timeline(events: List[Dict[str, Any]]) -> List[TimelineEvent]:
    return [
        TimelineEvent(
            date=_format_date(item["event_time"]),
            type=_relation_type(item["relation"]),
            title="{0}: {1}".format(_relation_label(item["relation"]), item["object_value"]),
            detail=item.get("note") or "{0} -> {1}".format(item["relation"], item["object_value"]),
        )
        for item in events
    ]


def _build_stats(events: List[Dict[str, Any]]) -> List[dict]:
    latest: Dict[str, Dict[str, Any]] = {}
    for item in events:
        latest[item["relation"]] = item

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
        if relation not in latest:
            continue
        stats.append(
            {
                "label": label,
                "value": str(latest[relation]["object_value"]),
                "trend": "来自最近一次结构化事件",
            }
        )
    return stats[:4]


def _build_followups(patient: Dict[str, Any]) -> List[dict]:
    due_date = str(patient["lastVisit"])
    if patient["riskLevel"] == "高风险":
        return [
            {"title": "7 天内完成重点复诊复核", "owner": "慢病门诊", "dueDate": due_date, "priority": "high"},
            {"title": "核对结构化事件完整性", "owner": "病案管理", "dueDate": due_date, "priority": "high"},
            {"title": "补充照护与用药执行记录", "owner": "随访护士", "dueDate": due_date, "priority": "medium"},
        ]
    return [
        {"title": "14 天内完成常规复诊", "owner": "慢病门诊", "dueDate": due_date, "priority": "medium"},
        {"title": "更新近期随访记录", "owner": "病案管理", "dueDate": due_date, "priority": "medium"},
        {"title": "继续生活方式管理提醒", "owner": "随访护士", "dueDate": due_date, "priority": "low"},
    ]


def _build_similar_cases(patient: Dict[str, Any]) -> List[dict]:
    return [
        {
            "caseId": "SIM-{0}".format(patient["patientId"]),
            "disease": patient["primaryDisease"],
            "matchScore": 0.84 if patient["dataSupport"] != "low" else 0.78,
            "summary": "相似病例来自同病种轨迹，用于辅助解释当前病程和风险变化。",
            "suggestion": "建议将相似病例路径与当前患者最近事件同时展示，供医生复核。",
        }
    ]


def _build_path_explanation(timeline: List[TimelineEvent]) -> List[str]:
    return ["{0} -> {1}".format(item.date, item.title) for item in timeline[-4:]]


def _build_default_predictions(patient: Dict[str, Any]) -> List[dict]:
    disease = patient["primaryDisease"]
    risk = patient["riskLevel"]
    stage = patient["currentStage"]
    base = 0.74 if risk == "高风险" else 0.61
    if disease == "Diabetes":
        return [
            {"label": "血糖控制波动上升", "score": base, "reason": "糖尿病阶段、依从性和监测轨迹提示需要继续加强管理。"},
            {"label": "复诊延迟风险增加", "score": base - 0.1, "reason": "建议结合门诊计划继续跟进随访节奏。"},
            {"label": "并发症筛查优先级提升", "score": base - 0.17, "reason": "中期患者更需要连续的检查提醒。"},
        ]
    if disease == "Alzheimer's":
        return [
            {"label": "认知功能继续下降", "score": base + 0.03, "reason": "病程阶段和睡眠/支持系统线索共同提示需要重点监测。"},
            {"label": "夜间行为问题风险增加", "score": base - 0.09, "reason": "建议结合照护者反馈完善病程记录。"},
            {"label": "照护压力持续上升", "score": base - 0.16, "reason": "照护路径需要同步评估。"},
        ]
    return [
        {"label": "步态波动与跌倒风险升高", "score": base + (0.04 if stage == "Late" else 0.0), "reason": "帕金森病病程推进后要优先评估运动症状。"},
        {"label": "药效穿透期缩短", "score": base - 0.08, "reason": "建议结合复诊记录和依从性进一步评估。"},
        {"label": "居家照护强度增加", "score": base - 0.16, "reason": "阶段进展会提高后续照护强度。"},
    ]


def _build_default_advice(patient: Dict[str, Any]) -> List[str]:
    disease = patient["primaryDisease"]
    support = patient["dataSupport"]
    advice = ["先核对最近一次就诊后的关键事件，确保阶段、依从性和支持系统信息完整。"]
    if disease == "Diabetes":
        advice.append("建议优先查看血糖、血压和并发症筛查是否按计划完成。")
    elif disease == "Alzheimer's":
        advice.append("建议同步关注照护者负担、夜间睡眠和安全风险。")
    else:
        advice.append("建议重点核查步态变化、跌倒风险和用药调整记录。")
    if support == "low":
        advice.append("当前样本支持较弱，优先补录 2 到 3 个结构化事件后再运行模型推理。")
    else:
        advice.append("可以结合 T+1 预测结果和相似病例进行辅助决策。")
    return advice


def _build_prediction_advice(patient: PatientCase, strategy: str, predictions: List[dict], evidence: Dict[str, Any]) -> List[str]:
    score = predictions[0]["score"] if predictions else 0.52
    suggestions = SUGGESTION_SERVICE.generate_suggestions(
        [{"entity": patient.primaryDisease, "confidence": score}]
    ) or SUGGESTION_SERVICE.get_generic_suggestions()

    advice: List[str] = []
    if strategy == "direct-model":
        advice.append("当前已直接使用训练图谱中的患者轨迹进行时序推理，建议优先复核 Top-1 预测与最近事件是否一致。")
    elif strategy == "proxy-model":
        advice.append("当前样本量有限，系统已切换为相似训练患者代理推理，建议重点核查被匹配到的关键关系。")
    elif strategy == "rules":
        advice.append("当前先采用规则与相似病例辅助建议，建议补录更多结构化事件后再触发模型推理。")
    else:
        advice.append("当前数据不足以支撑可靠模型推理，建议先完善关键病程事件。")

    if evidence["supportLevel"] == "minimal":
        advice.append("至少补录阶段、依从性、支持系统中的两个字段，以提高后续预测可信度。")

    for item in suggestions[:3]:
        advice.append(item.content)
    for item in patient.careAdvice:
        if item not in advice:
            advice.append(item)
    return advice[:6]


def _prediction_support_summary(strategy: str, evidence: Dict[str, Any]) -> str:
    if strategy == "direct-model":
        return "已基于现有患者实体直接推理，当前共有 {0} 条事件、{1} 个时间点。".format(
            evidence["eventCount"],
            evidence["timepointCount"],
        )
    if strategy == "proxy-model":
        return "当前采用相似训练患者代理推理，适用于小样本但已有部分结构化线索的场景。"
    if strategy == "rules":
        return "当前事件量仍偏少，系统先返回规则和相似病例辅助建议。"
    return "当前结构化事件不足，建议先补录关键关系后再执行模型推理。"


def _patient_case_from_db(store: MySQLStore, patient_id: str) -> Optional[PatientCase]:
    patient = store.get_patient_row(patient_id)
    if not patient:
        return None
    events = store.get_events(patient_id)
    timeline = _build_timeline(events)
    recommendation_mode = "similar-case" if patient["dataSupport"] == "low" or len(events) < 3 else "model"
    encounter_status = store.get_encounter_status(patient_id) or _default_encounter_status(patient)
    outpatient_tasks = _build_outpatient_tasks(store.list_outpatient_tasks(patient_id))
    contact_logs = _build_contact_logs(store.list_contact_logs(patient_id))
    audit_logs = [PatientAuditLog(**item) for item in store.list_patient_audit_logs(patient_id)]
    return PatientCase(
        **patient,
        encounterStatus=encounter_status,
        stats=_build_stats(events),
        timeline=timeline,
        predictions=_build_default_predictions(patient),
        pathExplanation=_build_path_explanation(timeline),
        followUps=_build_followups(patient),
        outpatientTasks=outpatient_tasks,
        contactLogs=contact_logs,
        auditLogs=audit_logs,
        recommendationMode=recommendation_mode,
        careAdvice=_build_default_advice(patient),
        similarCases=_build_similar_cases(patient),
    )


def authenticate(username: str, password: str) -> Optional[DoctorPublic]:
    store = _current_store()
    if store:
        doctor = store.authenticate(username, password)
        if doctor:
            return doctor
    return demo_store.authenticate(username, password)


def register_doctor(payload: RegisterRequest) -> Optional[DoctorPublic]:
    store = _current_store()
    if store:
        doctor = store.register_doctor(payload)
        if doctor:
            return doctor
        return None
    return demo_store.register_doctor(payload)


def get_doctor(username: str) -> Optional[DoctorPublic]:
    store = _current_store()
    if store:
        doctor = store.get_doctor(username)
        if doctor:
            return doctor
    return demo_store.get_doctor(username)


def issue_token(username: str) -> str:
    return _issue_token(username)


def is_token_valid(token: Optional[str]) -> bool:
    return bool(token and token in TOKENS)


def get_doctor_by_token(token: Optional[str]) -> Optional[DoctorPublic]:
    if not token:
        return None
    username = TOKENS.get(token)
    if not username:
        return None
    return get_doctor(username)


def list_patients() -> List[dict]:
    store = _current_store()
    if store:
        return store.list_patients()
    return demo_store.list_patients()


def get_timeline(patient_id: str) -> Optional[List[TimelineEvent]]:
    store = _current_store()
    if store:
        patient = store.get_patient_row(patient_id)
        if not patient:
            return None
        return _build_timeline(store.get_events(patient_id))
    return demo_store.get_timeline(patient_id)


def get_patient_quadruples(patient_id: str) -> Optional[List[PatientQuadruple]]:
    store = _current_store()
    if store:
        patient = store.get_patient_row(patient_id)
        if not patient:
            return None
        return [
            PatientQuadruple(
                subject=patient_id,
                relation=item["relation"],
                relationLabel=_relation_label(item["relation"]),
                objectValue=str(item["object_value"]),
                timestamp=_format_datetime(item["event_time"]),
                source=str(item.get("source") or "ehr"),
            )
            for item in store.get_events(patient_id)
        ]

    if not demo_store.get_patient(patient_id):
        return None
    return [
        PatientQuadruple(
            subject=patient_id,
            relation=item["relation"],
            relationLabel=_relation_label(item["relation"]),
            objectValue=str(item["object_value"]),
            timestamp=str(item["event_time"]).replace(" ", "T"),
            source=str(item.get("source") or "demo"),
        )
        for item in reversed(demo_store.list_event_rows(patient_id))
    ]


def get_patient(patient_id: str) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        return _patient_case_from_db(store, patient_id)
    return demo_store.get_patient(patient_id)


def save_patient(payload: PatientUpsertRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        store.save_patient(payload)
        return _patient_case_from_db(store, payload.patientId)
    return demo_store.save_patient(payload)


def add_patient_event(patient_id: str, payload: PatientEventCreateRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.add_event(patient_id, payload)
        return _patient_case_from_db(store, patient_id)
    return demo_store.add_event(patient_id, payload)


def add_patient_contact_log(patient_id: str, payload: ContactLogCreateRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.add_contact_log(patient_id, payload)
        return _patient_case_from_db(store, patient_id)
    return demo_store.add_contact_log(patient_id, payload)


def update_encounter_status(patient_id: str, payload: EncounterStatusUpdateRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.set_encounter_status(patient_id, payload.status)
        return _patient_case_from_db(store, patient_id)
    return demo_store.update_encounter_status(patient_id, payload)


def create_outpatient_task(patient_id: str, payload: OutpatientTaskCreateRequest) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.add_outpatient_task(patient_id, payload)
        return _patient_case_from_db(store, patient_id)
    return demo_store.add_outpatient_task(patient_id, payload)


def update_outpatient_task_status(
    patient_id: str,
    task_id: str,
    payload: OutpatientTaskStatusUpdateRequest,
) -> Optional[PatientCase]:
    store = _current_store()
    if store:
        if not store.get_patient_row(patient_id):
            return None
        store.update_outpatient_task_status(patient_id, task_id, payload)
        patient = _patient_case_from_db(store, patient_id)
        if patient is None:
            return None
        pending = [item for item in patient.outpatientTasks if item.status not in {"已完成", "已关闭"}]
        if not pending and patient.encounterStatus in {"in_progress", "pending_review"}:
            store.set_encounter_status(patient_id, "completed")
            patient = _patient_case_from_db(store, patient_id)
        return patient
    return demo_store.update_outpatient_task_status(patient_id, task_id, payload)


def predict_for_patient(patient_id: str, topk: int, as_of_time: Optional[str] = None) -> Optional[dict]:
    patient = get_patient(patient_id)
    if patient is None:
        return None

    timestamp = as_of_time or patient.lastVisit
    store = _current_store()
    event_payloads: List[Dict[str, Any]] = []

    if store:
        for item in store.get_events(patient_id):
            event_payloads.append(
                {
                    "event_time": _format_date(item["event_time"]),
                    "relation": item["relation"],
                    "object_value": item["object_value"],
                    "note": item.get("note") or "",
                }
            )
    else:
        for item in demo_store.list_event_rows(patient_id):
            event_payloads.append(
                {
                    "event_time": item["event_time"][:10],
                    "relation": item["relation"],
                    "object_value": item["object_value"],
                    "note": item.get("note") or "",
                }
            )

    if event_payloads:
        model_bundle = MODEL_SERVICE.predict_with_events(
            patient_id=patient.patientId,
            primary_disease=patient.primaryDisease,
            timestamp=timestamp,
            events=event_payloads,
            topk=topk,
        )
        strategy = model_bundle["strategy"]
        predictions = model_bundle["predictions"]
        evidence = model_bundle["evidence"]
        similar_cases = list(patient.similarCases)
        proxy_patient_id = model_bundle.get("proxyPatientId")
        if proxy_patient_id:
            similar_cases.insert(
                0,
                {
                    "caseId": "PROXY-{0}".format(proxy_patient_id),
                    "disease": patient.primaryDisease,
                    "matchScore": 0.82,
                    "summary": "该代理病例来自训练集中与当前事件组合最接近的患者轨迹。",
                    "suggestion": "建议结合代理路径与当前患者时间线共同复核。"},
            )

        if not predictions:
            predictions = [
                {
                    "label": _build_default_predictions(patient.model_dump())[0]["label"],
                    "score": 0.56 if strategy == "rules" else 0.48,
                    "reason": _prediction_support_summary(strategy, evidence),
                }
            ]

        return {
            "patientId": patient.patientId,
            "mode": model_bundle["mode"],
            "strategy": strategy,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "supportSummary": model_bundle["supportSummary"],
            "evidence": evidence,
            "topk": predictions[:topk],
            "advice": _build_prediction_advice(patient, strategy, predictions, evidence),
            "pathExplanation": model_bundle["pathExplanation"] or patient.pathExplanation,
            "similarCases": similar_cases,
        }

    fallback = demo_store.predict_for_patient(patient_id, topk)
    evidence = {
        "eventCount": len(patient.timeline),
        "timepointCount": len(set(item.date for item in patient.timeline)),
        "relationCount": min(len(patient.timeline), 4),
        "supportLevel": "strong" if patient.dataSupport == "high" else "limited",
    }
    if fallback:
        fallback["strategy"] = "direct-model" if fallback["mode"] == "model" else "similar-case"
        fallback["supportSummary"] = _prediction_support_summary(fallback["strategy"], evidence)
        fallback["evidence"] = evidence
        fallback["advice"] = _build_prediction_advice(patient, fallback["strategy"], fallback["topk"], evidence)
        return fallback

    fallback_predictions = _build_default_predictions(patient.model_dump())[:topk]
    return {
        "patientId": patient.patientId,
        "mode": "similar-case",
        "strategy": "similar-case",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "supportSummary": _prediction_support_summary("similar-case", evidence),
        "evidence": evidence,
        "topk": fallback_predictions,
        "advice": _build_prediction_advice(patient, "similar-case", fallback_predictions, evidence),
        "pathExplanation": patient.pathExplanation,
        "similarCases": patient.similarCases,
    }


def _reference_date(patients: List[dict]) -> Optional[datetime]:
    dates = []
    for item in patients:
        try:
            dates.append(datetime.strptime(item["lastVisit"], "%Y-%m-%d"))
        except Exception:
            continue
    return max(dates) if dates else None


def get_maintenance_overview() -> MaintenanceOverviewResponse:
    store = _current_store()
    if not store:
        overview = demo_store.maintenance_overview()
        overview.modelAvailable = MODEL_SERVICE.available
        overview.modelError = MODEL_SERVICE.error
        return overview

    patients = store.list_patients()
    event_rows = store.list_recent_events(limit=10)
    all_events: List[dict] = []
    for patient in patients:
        for item in store.get_events(patient["patientId"]):
            all_events.append(item)

    reference_date = _reference_date(patients)
    high_risk_count = sum(1 for item in patients if item["riskLevel"] == "高风险")
    low_support_count = sum(1 for item in patients if item["dataSupport"] == "low")
    overdue_count = 0
    if reference_date:
        for item in patients:
            try:
                last_visit = datetime.strptime(item["lastVisit"], "%Y-%m-%d")
            except Exception:
                continue
            if (reference_date - last_visit).days >= 14:
                overdue_count += 1

    disease_counter: Dict[str, int] = {}
    relation_counter: Dict[str, int] = {}
    for item in patients:
        disease_counter[item["primaryDisease"]] = disease_counter.get(item["primaryDisease"], 0) + 1
    for item in all_events:
        relation = item["relation"]
        relation_counter[relation] = relation_counter.get(relation, 0) + 1

    return MaintenanceOverviewResponse(
        mode="mysql",
        modelAvailable=MODEL_SERVICE.available,
        modelError=MODEL_SERVICE.error,
        patientCount=len(patients),
        eventCount=len(all_events),
        highRiskCount=high_risk_count,
        lowSupportCount=low_support_count,
        overdueFollowupCount=overdue_count,
        topDiseases=[
            MaintenanceCountItem(label=label, value=value)
            for label, value in sorted(disease_counter.items(), key=lambda item: (-item[1], item[0]))[:5]
        ],
        relationStats=[
            MaintenanceRelationStat(relation=relation, label=_relation_label(relation), count=count)
            for relation, count in sorted(relation_counter.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        recentPatients=[MaintenancePatientRow(**item) for item in patients[:6]],
        recentEvents=[
            MaintenanceEventRow(
                patientId=item["patientId"],
                patientName=item["patientName"],
                eventTime=item["eventTime"],
                relation=item["relation"],
                relationLabel=_relation_label(item["relation"]),
                objectValue=item["objectValue"],
                source=item["source"] or "ehr",
            )
            for item in event_rows
        ],
    )


def _task_type_from_title(title: str) -> str:
    lowered = title.lower()
    if "补录" in title:
        return "补录任务"
    if "复诊" in title or "随访" in title:
        return "随访任务"
    if "复核" in title:
        return "医生复核"
    return "管理任务"


def _followup_status(last_visit: str, due_date: str, risk_level: str, data_support: str) -> str:
    if data_support == "low":
        return "待补录"
    if risk_level == "高风险":
        return "优先随访"
    if due_date <= last_visit:
        return "已到期"
    return "待执行"


def _flow_status(patient: dict) -> tuple[str, str]:
    if patient["dataSupport"] == "low":
        return ("待补录", "补录关键结构化事件")
    if patient["riskLevel"] == "高风险":
        return ("待医生复核", "进入 N+1 预测并复核建议")
    if patient["dataSupport"] == "medium":
        return ("待随访", "安排近期复诊与随访")
    return ("已稳定", "保持常规随访")


def _encounter_status_rank(status: str) -> int:
    return {
        "in_progress": 0,
        "pending_review": 1,
        "waiting": 2,
        "completed": 3,
    }.get(status, 9)


def _legacy_get_followup_worklist_v1() -> FollowupWorklistResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    patients = list_patients()
    items: List[FollowupTaskRow] = []

    for patient in patients:
        patient_case = get_patient(patient["patientId"])
        if not patient_case:
            continue
        for task in patient_case.followUps:
            items.append(
                FollowupTaskRow(
                    taskId=None,
                    patientId=patient_case.patientId,
                    patientName=patient_case.name,
                    primaryDisease=patient_case.primaryDisease,
                    riskLevel=patient_case.riskLevel,
                    dataSupport=patient_case.dataSupport,
                    dueDate=task.dueDate,
                    owner=task.owner,
                    priority=task.priority,
                    taskType=_task_type_from_title(task.title),
                    status=_followup_status(patient_case.lastVisit, task.dueDate, patient_case.riskLevel, patient_case.dataSupport),
                )
            )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: (priority_order.get(item.priority, 9), item.dueDate, item.patientId))
    return FollowupWorklistResponse(mode=mode, items=items)


def _legacy_get_flow_board_v1() -> FlowBoardResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    rows: List[FlowBoardRow] = []

    for patient in list_patients():
        flow_status, next_action = _flow_status(patient)
        rows.append(
            FlowBoardRow(
                patientId=patient["patientId"],
                patientName=patient["name"],
                primaryDisease=patient["primaryDisease"],
                currentStage=patient["currentStage"],
                riskLevel=patient["riskLevel"],
                dataSupport=patient["dataSupport"],
                lastVisit=patient["lastVisit"],
                flowStatus=flow_status,
                nextAction=next_action,
            )
        )

    status_order = {"待医生复核": 0, "待补录": 1, "待随访": 2, "已稳定": 3}
    rows.sort(key=lambda item: (status_order.get(item.flowStatus, 9), item.lastVisit), reverse=False)
    return FlowBoardResponse(mode=mode, items=rows)


def _legacy_get_followup_worklist_v2() -> FollowupWorklistResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    patients = list_patients()
    items: List[FollowupTaskRow] = []

    for patient in patients:
        patient_case = get_patient(patient["patientId"])
        if not patient_case:
            continue
        for task in patient_case.followUps:
            items.append(
                FollowupTaskRow(
                    patientId=patient_case.patientId,
                    patientName=patient_case.name,
                    primaryDisease=patient_case.primaryDisease,
                    riskLevel=patient_case.riskLevel,
                    dataSupport=patient_case.dataSupport,
                    dueDate=task.dueDate,
                    owner=task.owner,
                    priority=task.priority,
                    taskType=_task_type_from_title(task.title),
                    status=_followup_status(patient_case.lastVisit, task.dueDate, patient_case.riskLevel, patient_case.dataSupport),
                    source="followup",
                )
            )
        for task in patient_case.outpatientTasks:
            items.append(
                FollowupTaskRow(
                    taskId=task.taskId,
                    patientId=patient_case.patientId,
                    patientName=patient_case.name,
                    primaryDisease=patient_case.primaryDisease,
                    riskLevel=patient_case.riskLevel,
                    dataSupport=patient_case.dataSupport,
                    dueDate=task.dueDate,
                    owner=task.owner,
                    priority=task.priority,
                    taskType="检查申请" if task.category == "exam" else "复查计划",
                    status=task.status,
                    source="outpatient-task",
                    lastActionBy=task.updatedBy,
                    lastActionAt=task.updatedAt,
                )
            )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: (priority_order.get(item.priority, 9), item.dueDate, item.patientId))
    return FollowupWorklistResponse(mode=mode, items=items)


def _legacy_get_flow_board_v2() -> FlowBoardResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    rows: List[FlowBoardRow] = []

    for patient in list_patients():
        _, fallback_next_action = _flow_status(patient)
        patient_case = get_patient(patient["patientId"])
        encounter_status = patient_case.encounterStatus if patient_case else _default_encounter_status(patient)
        outpatient_tasks = patient_case.outpatientTasks if patient_case else []
        rows.append(
            FlowBoardRow(
                patientId=patient["patientId"],
                patientName=patient["name"],
                primaryDisease=patient["primaryDisease"],
                currentStage=patient["currentStage"],
                riskLevel=patient["riskLevel"],
                dataSupport=patient["dataSupport"],
                lastVisit=patient["lastVisit"],
                flowStatus=_encounter_status_label(encounter_status),
                nextAction=_encounter_next_action(encounter_status, outpatient_tasks, fallback_next_action),
            )
        )

    status_order = {"接诊中": 0, "待复核": 1, "候诊": 2, "已完成": 3}
    rows.sort(key=lambda item: (status_order.get(item.flowStatus, 9), item.lastVisit), reverse=False)
    return FlowBoardResponse(mode=mode, items=rows)


def get_followup_worklist() -> FollowupWorklistResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    patients = list_patients()
    items: List[FollowupTaskRow] = []

    for patient in patients:
        patient_case = get_patient(patient["patientId"])
        if not patient_case:
            continue
        for task in patient_case.followUps:
            items.append(
                FollowupTaskRow(
                    taskId=None,
                    patientId=patient_case.patientId,
                    patientName=patient_case.name,
                    primaryDisease=patient_case.primaryDisease,
                    riskLevel=patient_case.riskLevel,
                    dataSupport=patient_case.dataSupport,
                    dueDate=task.dueDate,
                    owner=task.owner,
                    priority=task.priority,
                    taskType=_task_type_from_title(task.title),
                    status=_followup_status(patient_case.lastVisit, task.dueDate, patient_case.riskLevel, patient_case.dataSupport),
                    source="followup",
                )
            )
        for task in patient_case.outpatientTasks:
            items.append(
                FollowupTaskRow(
                    taskId=task.taskId,
                    patientId=patient_case.patientId,
                    patientName=patient_case.name,
                    primaryDisease=patient_case.primaryDisease,
                    riskLevel=patient_case.riskLevel,
                    dataSupport=patient_case.dataSupport,
                    dueDate=task.dueDate,
                    owner=task.owner,
                    priority=task.priority,
                    taskType="检查申请" if task.category == "exam" else "复查计划",
                    status=task.status,
                    source="outpatient-task",
                    lastActionBy=task.updatedBy,
                    lastActionAt=task.updatedAt,
                )
            )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    items.sort(key=lambda item: (priority_order.get(item.priority, 9), item.dueDate, item.patientId))
    return FollowupWorklistResponse(mode=mode, items=items)


def get_flow_board() -> FlowBoardResponse:
    store = _current_store()
    mode = "mysql" if store else "demo"
    rows: List[tuple[int, FlowBoardRow]] = []

    for patient in list_patients():
        _, fallback_next_action = _flow_status(patient)
        patient_case = get_patient(patient["patientId"])
        encounter_status = patient_case.encounterStatus if patient_case else _default_encounter_status(patient)
        outpatient_tasks = patient_case.outpatientTasks if patient_case else []
        rows.append(
            (
                _encounter_status_rank(encounter_status),
                FlowBoardRow(
                    patientId=patient["patientId"],
                    patientName=patient["name"],
                    primaryDisease=patient["primaryDisease"],
                    currentStage=patient["currentStage"],
                    riskLevel=patient["riskLevel"],
                    dataSupport=patient["dataSupport"],
                    lastVisit=patient["lastVisit"],
                    flowStatus=_encounter_status_label(encounter_status),
                    nextAction=_encounter_next_action(encounter_status, outpatient_tasks, fallback_next_action),
                ),
            )
        )

    rows.sort(key=lambda item: (item[0], item[1].lastVisit, item[1].patientId))
    return FlowBoardResponse(mode=mode, items=[row for _, row in rows])


def get_model_metrics() -> ModelMetricsResponse:
    return ModelMetricsResponse(
        dataset="CHRONIC",
        currentModel=ExperimentMetric(
            model="TKGR-GPRSCL / CTpath",
            status="done",
            mrr=0.3441,
            hits1=0.2294,
            hits3=0.4489,
            hits10=0.5163,
            note="当前展示的是 CHRONIC 上的已跑通结果，可用于系统联调与答辩展示。",
        ),
        comparisons=[
            ExperimentMetric(
                model="ICEWS14 标准对比实验",
                status="todo",
                note="建议补做标准公开数据集实验，用于支撑论文中的公平对比。",
            ),
            ExperimentMetric(
                model="静态基线对比",
                status="todo",
                note="建议补充 TransE、RotatE 等静态知识图谱基线。",
            ),
            ExperimentMetric(
                model="消融实验",
                status="todo",
                note="建议至少拆分时序模块与路径模块，形成两组消融结果。",
            ),
        ],
    )


def _build_master_index_summary(
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
                    detail="患者主索引尚未补齐病案号，建议先完成病案号维护。",
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
                    detail="档案已建立，但知情同意状态仍待补齐。",
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


def get_maintenance_overview() -> MaintenanceOverviewResponse:
    store = _current_store()
    if not store:
        overview = demo_store.maintenance_overview()
        overview.modelAvailable = MODEL_SERVICE.available
        overview.modelError = MODEL_SERVICE.error
        return overview

    patients = store.list_patients()
    event_rows = store.list_recent_events(limit=10)
    all_events: List[dict] = []
    for patient in patients:
        for item in store.get_events(patient["patientId"]):
            all_events.append(item)

    reference_date = _reference_date(patients)
    high_risk_count = sum(
        1 for item in patients if "高" in item["riskLevel"] or "high" in item["riskLevel"].lower()
    )
    low_support_count = sum(1 for item in patients if item["dataSupport"] == "low")
    overdue_count = 0
    if reference_date:
        for item in patients:
            try:
                last_visit = datetime.strptime(item["lastVisit"], "%Y-%m-%d")
            except Exception:
                continue
            if (reference_date - last_visit).days >= 14:
                overdue_count += 1

    (
        missing_mrn_count,
        pending_consent_count,
        duplicate_risk_count,
        source_counter,
        master_index_alerts,
    ) = _build_master_index_summary(patients)

    disease_counter: Dict[str, int] = {}
    relation_counter: Dict[str, int] = {}
    for item in patients:
        disease_counter[item["primaryDisease"]] = disease_counter.get(item["primaryDisease"], 0) + 1
    for item in all_events:
        relation = item["relation"]
        relation_counter[relation] = relation_counter.get(relation, 0) + 1

    return MaintenanceOverviewResponse(
        mode="mysql",
        modelAvailable=MODEL_SERVICE.available,
        modelError=MODEL_SERVICE.error,
        patientCount=len(patients),
        eventCount=len(all_events),
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
            MaintenanceRelationStat(relation=relation, label=_relation_label(relation), count=count)
            for relation, count in sorted(relation_counter.items(), key=lambda item: (-item[1], item[0]))[:8]
        ],
        recentPatients=[MaintenancePatientRow(**item) for item in patients[:6]],
        masterIndexAlerts=master_index_alerts,
        recentEvents=[
            MaintenanceEventRow(
                patientId=item["patientId"],
                patientName=item["patientName"],
                eventTime=item["eventTime"],
                relation=item["relation"],
                relationLabel=_relation_label(item["relation"]),
                objectValue=item["objectValue"],
                source=item["source"] or "ehr",
            )
            for item in event_rows
        ],
    )
