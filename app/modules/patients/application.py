import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from ...schemas import (
    ContactLogCreateRequest,
    EncounterStatusUpdateRequest,
    MedicationPlanGenerateRequest,
    MedicationPlanResponse,
    OutpatientTaskCreateRequest,
    OutpatientTaskStatusUpdateRequest,
    PatientCase,
    PatientEventCreateRequest,
    PatientSummary,
    PatientUpsertRequest,
    QuadrupleResponse,
    TimelineResponse,
)
from ...services.llm_advice_service import LLM_ADVICE_SERVICE
from ...store import (
    add_patient_contact_log,
    add_patient_event,
    create_outpatient_task,
    get_patient,
    get_patient_quadruples,
    get_timeline,
    list_patients as store_list_patients,
    save_patient,
    update_encounter_status,
    update_outpatient_task_status,
)


@dataclass
class PatientPaginationResult:
    items: List[PatientSummary]
    total: int
    page: int
    page_size: int
    total_pages: int

    def to_legacy_payload(self) -> dict:
        return {
            "patients": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
        }

    def to_v2_payload(self) -> dict:
        return {
            "items": self.items,
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "total_pages": self.total_pages,
        }


class PatientApplicationService:
    """OpenHIS-style application service for the patient module."""

    _SORT_FIELD_MAP = {
        "patientId": "patientId",
        "patient_id": "patientId",
        "name": "name",
        "age": "age",
        "primaryDisease": "primaryDisease",
        "currentStage": "currentStage",
        "riskLevel": "riskLevel",
        "risk_level": "riskLevel",
        "dataSupport": "dataSupport",
        "lastVisit": "lastVisit",
        "created_at": "lastVisit",
    }

    def list_patients(self) -> List[PatientSummary]:
        return [PatientSummary(**item) for item in store_list_patients()]

    def paginate_patients(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        risk_level: Optional[str] = None,
        disease: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> PatientPaginationResult:
        filtered = self._filter_patients(
            self.list_patients(),
            search=search,
            risk_level=risk_level,
            disease=disease,
        )
        sorted_items = self._sort_patients(filtered, sort_by=sort_by, sort_order=sort_order)

        total = len(sorted_items)
        total_pages = math.ceil(total / page_size) if total > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        return PatientPaginationResult(
            items=sorted_items[start_idx:end_idx],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_patient_case(self, patient_id: str) -> Optional[PatientCase]:
        return get_patient(patient_id)

    def create_patient(self, payload: PatientUpsertRequest) -> Optional[PatientCase]:
        return save_patient(payload)

    def update_patient(self, patient_id: str, payload: PatientUpsertRequest) -> Optional[PatientCase]:
        return save_patient(payload.model_copy(update={"patientId": patient_id}))

    def create_patient_event(
        self,
        patient_id: str,
        payload: PatientEventCreateRequest,
    ) -> Optional[PatientCase]:
        return add_patient_event(patient_id, payload)

    def create_contact_log(
        self,
        patient_id: str,
        payload: ContactLogCreateRequest,
    ) -> Optional[PatientCase]:
        return add_patient_contact_log(patient_id, payload)

    def update_encounter_status(
        self,
        patient_id: str,
        payload: EncounterStatusUpdateRequest,
    ) -> Optional[PatientCase]:
        return update_encounter_status(patient_id, payload)

    def create_outpatient_task(
        self,
        patient_id: str,
        payload: OutpatientTaskCreateRequest,
    ) -> Optional[PatientCase]:
        return create_outpatient_task(patient_id, payload)

    def update_outpatient_task_status(
        self,
        patient_id: str,
        task_id: str,
        payload: OutpatientTaskStatusUpdateRequest,
    ) -> Optional[PatientCase]:
        return update_outpatient_task_status(patient_id, task_id, payload)

    def get_timeline(self, patient_id: str) -> Optional[TimelineResponse]:
        items = get_timeline(patient_id)
        if items is None:
            return None
        return TimelineResponse(patientId=patient_id, items=items)

    def get_quadruples(self, patient_id: str) -> Optional[QuadrupleResponse]:
        items = get_patient_quadruples(patient_id)
        if items is None:
            return None
        return QuadrupleResponse(patientId=patient_id, items=items)

    def generate_medication_plan(
        self,
        patient_id: str,
        payload: MedicationPlanGenerateRequest,
    ) -> Optional[MedicationPlanResponse]:
        patient = self.get_patient_case(patient_id)
        if patient is None:
            return None

        current_medications = self._normalize_list(payload.currentMedications)
        if not current_medications:
            current_medications = self._infer_current_medications(patient)

        allergies = self._split_text_values(patient.allergyHistory)
        care_goals = self._normalize_list(payload.careGoals)

        return LLM_ADVICE_SERVICE.generate_medication_plan(
            patient=self._to_upsert_patient(patient),
            current_medications=current_medications,
            allergies=allergies,
            care_goals=care_goals,
            clinical_notes=payload.clinicalNotes.strip(),
        )

    def get_stats_overview(self) -> dict:
        patients = self.list_patients()
        by_risk: Dict[str, int] = {}
        by_age: Dict[str, int] = {}

        for patient in patients:
            by_risk[patient.riskLevel] = by_risk.get(patient.riskLevel, 0) + 1
            age_bucket = self._age_bucket(patient.age)
            by_age[age_bucket] = by_age.get(age_bucket, 0) + 1

        return {
            "total": len(patients),
            "by_risk": by_risk,
            "by_age": by_age,
        }

    def _filter_patients(
        self,
        patients: List[PatientSummary],
        *,
        search: Optional[str],
        risk_level: Optional[str],
        disease: Optional[str],
    ) -> List[PatientSummary]:
        filtered = patients

        if search:
            keyword = search.strip().lower()
            filtered = [
                patient
                for patient in filtered
                if keyword in patient.name.lower()
                or keyword in patient.patientId.lower()
                or keyword in patient.primaryDisease.lower()
            ]

        if risk_level and risk_level not in {"全部风险", "all"}:
            keyword = risk_level.strip().lower()
            filtered = [patient for patient in filtered if keyword in patient.riskLevel.lower()]

        if disease:
            keyword = disease.strip().lower()
            filtered = [patient for patient in filtered if keyword in patient.primaryDisease.lower()]

        return filtered

    def _sort_patients(
        self,
        patients: List[PatientSummary],
        *,
        sort_by: Optional[str],
        sort_order: str,
    ) -> List[PatientSummary]:
        sort_field = self._SORT_FIELD_MAP.get(sort_by or "", "lastVisit")
        reverse = sort_order.lower() != "asc"

        def sort_key(patient: PatientSummary):
            value = getattr(patient, sort_field)
            if isinstance(value, str):
                return value.lower()
            return value

        return sorted(patients, key=sort_key, reverse=reverse)

    @staticmethod
    def _age_bucket(age: int) -> str:
        if age < 50:
            return "<50"
        if age < 60:
            return "50-59"
        if age < 70:
            return "60-69"
        if age < 80:
            return "70-79"
        return "80+"

    @staticmethod
    def _normalize_list(values: List[str]) -> List[str]:
        result: List[str] = []
        for item in values:
            text = str(item).strip()
            if not text:
                continue
            if text in result:
                continue
            result.append(text)
        return result

    @staticmethod
    def _split_text_values(raw_text: str) -> List[str]:
        if not raw_text:
            return []
        normalized = (
            raw_text.replace("；", ",")
            .replace("，", ",")
            .replace("、", ",")
            .replace(";", ",")
            .replace("/", ",")
            .replace("|", ",")
            .replace("\n", ",")
        )
        values = [item.strip() for item in normalized.split(",") if item.strip()]
        return PatientApplicationService._normalize_list(values)

    @staticmethod
    def _infer_current_medications(patient: PatientCase) -> List[str]:
        items: List[str] = []
        for event in patient.timeline:
            title = event.title.lower()
            detail = event.detail.strip()
            if not detail:
                continue
            if event.type == "medication" or "用药" in event.title or "med" in title:
                items.append(detail)
        return PatientApplicationService._normalize_list(items)

    @staticmethod
    def _to_upsert_patient(patient: PatientCase) -> PatientUpsertRequest:
        return PatientUpsertRequest(
            patientId=patient.patientId,
            name=patient.name,
            age=patient.age,
            gender=patient.gender,
            avatarUrl=patient.avatarUrl,
            phone=patient.phone,
            emergencyContactName=patient.emergencyContactName,
            emergencyContactRelation=patient.emergencyContactRelation,
            emergencyContactPhone=patient.emergencyContactPhone,
            identityMasked=patient.identityMasked,
            insuranceType=patient.insuranceType,
            department=patient.department,
            primaryDoctor=patient.primaryDoctor,
            caseManager=patient.caseManager,
            medicalRecordNumber=patient.medicalRecordNumber,
            archiveSource=patient.archiveSource,
            archiveStatus=patient.archiveStatus,
            consentStatus=patient.consentStatus,
            allergyHistory=patient.allergyHistory,
            familyHistory=patient.familyHistory,
            primaryDisease=patient.primaryDisease,
            currentStage=patient.currentStage,
            riskLevel=patient.riskLevel,
            lastVisit=patient.lastVisit,
            summary=patient.summary,
            dataSupport=patient.dataSupport,
        )


PATIENT_APPLICATION_SERVICE = PatientApplicationService()
