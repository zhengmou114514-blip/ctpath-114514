from __future__ import annotations

import importlib
import math
import os
import pickle
import sys
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Optional, Set

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
DATA_DIR = ROOT / "data" / "CHRONIC"
PATH_DIR = ROOT / "path_data" / "CHRONIC"
DEFAULT_CHECKPOINT = ROOT / "models" / "results" / "CHRONIC_Supercomplex_800_0.1_160_1_8_1772601693" / "best.pth"


@dataclass
class ModelPrediction:
    label: str
    score: float
    relation: str


@dataclass
class ProxyMatch:
    entity_name: str
    patient_id: str
    score: float
    matched_relations: List[str]
    disease_match: Optional[str]


class ChronicModelService:
    def __init__(self) -> None:
        self.available = False
        self.error: Optional[str] = None
        self.device = os.getenv("CTPATH_MODEL_DEVICE", "cpu")
        self.checkpoint_path = Path(os.getenv("CTPATH_MODEL_CHECKPOINT", str(DEFAULT_CHECKPOINT)))
        self.rank = int(os.getenv("CTPATH_MODEL_RANK", "800"))
        self.n_hidden = int(os.getenv("CTPATH_MODEL_N_HIDDEN", "160"))
        self.num_walks = int(os.getenv("CTPATH_MODEL_NUM_WALKS", "1"))
        self.walk_len = int(os.getenv("CTPATH_MODEL_WALK_LEN", "8"))
        self._torch = None
        self._model = None
        self._args = None
        self._entity_to_id: Dict[str, int] = {}
        self._id_to_entity: Dict[int, str] = {}
        self._relation_to_id: Dict[str, int] = {}
        self._timestamp_to_id: Dict[str, int] = {}
        self._sorted_timestamps: List[str] = []
        self._relation_candidates: Dict[str, List[int]] = {}
        self._patient_profiles: Dict[str, dict] = {}
        self._neis_all = None
        self._neis_timestamps = None
        self._path_weight = None
        self._load()

    def _load(self) -> None:
        try:
            import torch  # type: ignore
        except Exception as exc:  # pragma: no cover
            self.error = "torch unavailable: {0}".format(exc)
            return

        self._torch = torch
        try:
            if str(MODELS_DIR) not in sys.path:
                sys.path.insert(0, str(MODELS_DIR))
            ct_models = importlib.import_module("models")
            with open(DATA_DIR / "stat", "rb") as file:
                stat = pickle.load(file)
            sizes = (int(stat[0]), int(stat[1]) * 2, int(stat[0]), int(stat[2]))
            self._args = SimpleNamespace(
                cuda=self.device,
                num_walks=self.num_walks,
                walk_len=self.walk_len,
                n_hidden=self.n_hidden,
                dropout_pathnet=0.2,
            )
            self._model = ct_models.Supercomplex(self._args, sizes, self.rank, is_cuda=self.device != "cpu")
            checkpoint = torch.load(self.checkpoint_path, map_location=self.device)
            self._model.load_state_dict(checkpoint["param"], strict=True)
            self._model.eval()
            self._read_mappings()
            self._load_paths()
            self._build_relation_candidates()
            self._build_patient_profiles()
            self.available = True
        except Exception as exc:  # pragma: no cover
            self.error = str(exc)
            self.available = False

    def _read_mapping_file(self, path: Path) -> Dict[str, int]:
        mapping: Dict[str, int] = {}
        with open(path, "r", encoding="utf-8") as file:
            for line in file:
                left, right = line.rstrip("\n").split("\t")
                mapping[left] = int(right)
        return mapping

    def _read_mappings(self) -> None:
        self._entity_to_id = self._read_mapping_file(DATA_DIR / "ent2id.txt")
        self._id_to_entity = dict((value, key) for key, value in self._entity_to_id.items())
        self._relation_to_id = self._read_mapping_file(DATA_DIR / "rel2id.txt")
        self._timestamp_to_id = self._read_mapping_file(DATA_DIR / "ts2id.txt")
        self._sorted_timestamps = sorted(self._timestamp_to_id.keys())

    def _load_paths(self) -> None:
        torch = self._torch
        walks: List[List[int]] = []
        timestamps: List[List[int]] = []
        weights: List[List[float]] = []
        path_file = PATH_DIR / "CHRONIC_{0}_{1}_merw.txt".format(self.num_walks, self.walk_len)
        with open(path_file, "r", encoding="utf-8") as file:
            for line in file:
                info = list(map(float, line[1:-2].split(",")))
                walks.append(list(map(int, info[: self.walk_len])))
                timestamps.append(list(map(int, info[self.walk_len : 2 * self.walk_len])))
                weights.append(info[2 * self.walk_len :])
        node_num = int(torch.from_numpy(np.load(PATH_DIR / "y.npy")).to(torch.long))
        self._neis_all = torch.tensor(walks, dtype=torch.long).view(node_num, -1).to(self.device)
        self._neis_timestamps = torch.tensor(timestamps, dtype=torch.long).view(node_num, -1).to(self.device)
        self._path_weight = torch.tensor(weights).view(node_num, -1).to(self.device)

    def _build_relation_candidates(self) -> None:
        relation_to_objects: Dict[str, Set[int]] = {}
        for split in ["train", "valid", "test"]:
            with open(DATA_DIR / split, "r", encoding="utf-8") as file:
                for line in file:
                    _lhs, relation, rhs, _timestamp = line.rstrip("\n").split("\t")
                    relation_to_objects.setdefault(relation, set()).add(self._entity_to_id[rhs])
        self._relation_candidates = dict((key, sorted(value)) for key, value in relation_to_objects.items())

    def _build_patient_profiles(self) -> None:
        profiles: Dict[str, dict] = {}
        for split in ["train", "valid", "test"]:
            with open(DATA_DIR / split, "r", encoding="utf-8") as file:
                for line in file:
                    lhs, relation, rhs, timestamp = line.rstrip("\n").split("\t")
                    profile = profiles.setdefault(
                        lhs,
                        {
                            "patient_id": lhs.replace("p_", "", 1),
                            "latest_relations": {},
                            "relation_times": {},
                            "diseases": set(),
                            "event_count": 0,
                            "timepoints": set(),
                        },
                    )
                    profile["event_count"] += 1
                    profile["timepoints"].add(timestamp)
                    previous_time = profile["relation_times"].get(relation)
                    if previous_time is None or timestamp >= previous_time:
                        profile["relation_times"][relation] = timestamp
                        profile["latest_relations"][relation] = rhs
                    if relation == "has_disease":
                        profile["diseases"].add(rhs)
                    if relation == "medical_history":
                        profile["diseases"].add(rhs)
        self._patient_profiles = profiles

    def _timestamp_id(self, timestamp: str) -> int:
        if timestamp in self._timestamp_to_id:
            return self._timestamp_to_id[timestamp]
        earlier = [item for item in self._sorted_timestamps if item <= timestamp]
        if earlier:
            return self._timestamp_to_id[earlier[-1]]
        return 0

    def _patient_entity(self, patient_id: str) -> str:
        return patient_id if patient_id.startswith("p_") else "p_{0}".format(patient_id)

    def supports_patient(self, patient_id: str) -> bool:
        if not self.available:
            return False
        entity_name = self._patient_entity(patient_id)
        return entity_name in self._entity_to_id

    def _select_relations(self, primary_disease: str) -> List[str]:
        if "糖尿病" in primary_disease:
            return ["stage", "med_adherence", "bmi_bin", "bp_sys_bin", "support_system"]
        if "肾" in primary_disease:
            return ["stage", "bp_sys_bin", "mood_bin", "sleep_hours_bin", "support_system"]
        if "阿尔茨海默" in primary_disease:
            return ["stage", "support_system", "sleep_hours_bin", "mood_bin", "has_caregiver"]
        if "高血压" in primary_disease:
            return ["bp_sys_bin", "bp_dia_bin", "med_adherence", "support_system", "stage"]
        return ["stage", "med_adherence", "support_system", "mood_bin"]

    def _choose_relations(self, primary_disease: str, latest_relations: Dict[str, str]) -> List[str]:
        relation_order = [
            "stage",
            "has_disease",
            "med_adherence",
            "support_system",
            "bp_sys_bin",
            "bp_dia_bin",
            "sleep_hours_bin",
            "mood_bin",
            "bmi_bin",
            "cholesterol_bin",
            "has_caregiver",
        ]
        observed = [relation for relation in relation_order if relation in latest_relations]
        merged = observed + self._select_relations(primary_disease)
        deduped: List[str] = []
        for relation in merged:
            if relation not in deduped:
                deduped.append(relation)
        return deduped[: max(3, len(self._select_relations(primary_disease)))]

    def _score_relation(self, subject_id: int, relation_name: str, timestamp_id: int, topk: int) -> List[ModelPrediction]:
        if relation_name not in self._relation_to_id:
            return []

        relation_id = self._relation_to_id[relation_name]
        candidate_ids = self._relation_candidates.get(relation_name, [])
        if not candidate_ids:
            return []

        torch = self._torch
        x = torch.tensor([[subject_id, relation_id, 0, timestamp_id]], dtype=torch.long).to(self.device)
        lhs = self._model.embeddings[0](x[:, 0])
        rel = self._model.embeddings[1](x[:, 1])
        time_ent = self._model.embeddings[2](x[:, 3])
        time_rel = self._model.embeddings[3](x[:, 3])
        comp_time = self._model.embeddings[4](x[:, 3])
        rel_ = self._model.complex_mul(rel, comp_time)
        rel_ = rel + rel_
        neis_embd = self._model.forward_PathNet(
            self._model.pathNet_encoder,
            self._model.embeddings[0].weight,
            self._model.embeddings[2].weight,
            self._args.num_walks,
            self._args.walk_len,
            self._neis_all,
            self._neis_timestamps,
            self._path_weight,
            x[:, 0],
            x[:, 3],
        )
        lhs_rel = self._model.quaternion_mul(
            torch.cat([lhs, lhs, time_ent, time_ent], dim=1),
            torch.cat([rel_, rel_, time_rel, time_rel], dim=1),
        )
        a, b, c, d = torch.chunk(lhs_rel, chunks=4, dim=1)
        all_entities = self._model.embeddings[0].weight.transpose(0, 1)
        scores = a @ all_entities + b @ all_entities
        scores = scores + torch.sum(c * neis_embd, dim=1).unsqueeze(1)
        scores = scores + torch.sum(d * time_ent, dim=1).unsqueeze(1)
        scores = scores + torch.sum(d * neis_embd, dim=1).unsqueeze(1)
        scores = scores + torch.sum(c * time_ent, dim=1).unsqueeze(1)

        candidate_tensor = torch.tensor(candidate_ids, dtype=torch.long).to(self.device)
        candidate_scores = scores[0, candidate_tensor]
        values, indices = torch.topk(candidate_scores, k=min(topk, len(candidate_ids)))

        predictions: List[ModelPrediction] = []
        for score, index in zip(values.tolist(), indices.tolist()):
            entity_id = candidate_ids[index]
            predictions.append(
                ModelPrediction(
                    label=self._id_to_entity[entity_id],
                    score=float(score),
                    relation=relation_name,
                )
            )
        return predictions

    def _build_event_profile(self, events: List[dict], primary_disease: str, as_of_time: Optional[str]) -> dict:
        cutoff = (as_of_time or "").strip()
        filtered: List[dict] = []
        for item in events:
            event_time = str(item.get("event_time", "") or item.get("date", ""))[:10]
            if cutoff and event_time and event_time > cutoff[:10]:
                continue
            filtered.append(
                {
                    "event_time": event_time,
                    "relation": item.get("relation", ""),
                    "object_value": item.get("object_value", ""),
                    "note": item.get("note", ""),
                }
            )

        filtered.sort(key=lambda item: (item["event_time"], item["relation"], item["object_value"]))
        latest_relations: Dict[str, str] = {}
        relation_times: Dict[str, str] = {}
        diseases: Set[str] = set()
        path_steps: List[str] = []
        for item in filtered:
            relation = item["relation"]
            if not relation:
                continue
            event_time = item["event_time"]
            object_value = item["object_value"]
            previous_time = relation_times.get(relation)
            if previous_time is None or event_time >= previous_time:
                relation_times[relation] = event_time
                latest_relations[relation] = object_value
            if relation in {"has_disease", "medical_history"} and object_value:
                diseases.add(object_value)
            if object_value:
                path_steps.append("{0} -> {1}: {2}".format(event_time or "unknown", relation, object_value))

        if primary_disease:
            diseases.add(primary_disease)

        timepoints = sorted(set(item["event_time"] for item in filtered if item["event_time"]))
        relation_count = len(latest_relations)
        event_count = len(filtered)
        if event_count >= 6 and len(timepoints) >= 3 and relation_count >= 4:
            support_level = "strong"
        elif event_count >= 3 and len(timepoints) >= 2 and relation_count >= 2:
            support_level = "limited"
        else:
            support_level = "minimal"

        return {
            "latest_relations": latest_relations,
            "diseases": diseases,
            "event_count": event_count,
            "timepoint_count": len(timepoints),
            "relation_count": relation_count,
            "support_level": support_level,
            "path_steps": path_steps[-4:],
        }

    def _match_proxy_patient(self, profile: dict, exclude_entity_name: Optional[str]) -> Optional[ProxyMatch]:
        best_match: Optional[ProxyMatch] = None
        latest_relations: Dict[str, str] = profile["latest_relations"]
        diseases: Set[str] = profile["diseases"]

        for entity_name, candidate in self._patient_profiles.items():
            if exclude_entity_name and entity_name == exclude_entity_name:
                continue

            score = 0.0
            matched_relations: List[str] = []
            disease_match: Optional[str] = None

            for disease in diseases:
                for candidate_disease in candidate["diseases"]:
                    if disease == candidate_disease:
                        score += 4.0
                        disease_match = disease
                        break
                    if disease and candidate_disease and (disease in candidate_disease or candidate_disease in disease):
                        score += 2.5
                        disease_match = candidate_disease
                        break
                if disease_match:
                    break

            for relation, object_value in latest_relations.items():
                candidate_value = candidate["latest_relations"].get(relation)
                if candidate_value is None:
                    continue
                matched_relations.append(relation)
                score += 1.0
                if candidate_value == object_value:
                    score += 2.0

            normalizer = 4.0 + max(1, len(latest_relations)) * 3.0
            normalized = min(score / normalizer, 1.0)
            if normalized <= 0:
                continue

            candidate_match = ProxyMatch(
                entity_name=entity_name,
                patient_id=candidate["patient_id"],
                score=normalized,
                matched_relations=matched_relations,
                disease_match=disease_match,
            )
            if best_match is None or candidate_match.score > best_match.score:
                best_match = candidate_match

        return best_match

    def _predict_subject(
        self,
        entity_name: str,
        primary_disease: str,
        timestamp: str,
        topk: int,
        latest_relations: Dict[str, str],
        proxy_match: Optional[ProxyMatch] = None,
    ) -> List[dict]:
        subject_id = self._entity_to_id.get(entity_name)
        if subject_id is None:
            return []

        timestamp_id = self._timestamp_id(timestamp)
        relation_names = self._choose_relations(primary_disease, latest_relations)
        results: List[dict] = []
        for relation_name in relation_names:
            predictions = self._score_relation(subject_id, relation_name, timestamp_id, topk=1)
            if not predictions:
                continue
            prediction = predictions[0]
            normalized_score = 1 / (1 + math.exp(-prediction.score / 25))
            if proxy_match:
                reason = "参考训练患者 {0} 的相似轨迹，在关系 {1} 上最可能出现 {2}。".format(
                    proxy_match.patient_id,
                    relation_name,
                    prediction.label,
                )
            else:
                reason = "CTpath 在关系 {0} 上对候选 {1} 的打分最高。".format(relation_name, prediction.label)
            results.append(
                {
                    "label": "{0} -> {1}".format(relation_name, prediction.label),
                    "score": normalized_score,
                    "reason": reason,
                }
            )
        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:topk]

    def predict_patient(self, patient_id: str, primary_disease: str, timestamp: str, topk: int = 3) -> List[dict]:
        if not self.available:
            return []
        entity_name = self._patient_entity(patient_id)
        if entity_name not in self._entity_to_id:
            return []
        return self._predict_subject(entity_name, primary_disease, timestamp, topk, latest_relations={})

    def predict_with_events(
        self,
        patient_id: str,
        primary_disease: str,
        timestamp: str,
        events: List[dict],
        topk: int = 3,
    ) -> dict:
        profile = self._build_event_profile(events, primary_disease, timestamp)
        evidence = {
            "eventCount": profile["event_count"],
            "timepointCount": profile["timepoint_count"],
            "relationCount": profile["relation_count"],
            "supportLevel": profile["support_level"],
        }

        if not self.available:
            return {
                "predictions": [],
                "mode": "similar-case",
                "strategy": "similar-case",
                "supportSummary": "模型当前不可用，系统仅返回规则和相似病例辅助建议。",
                "evidence": evidence,
                "pathExplanation": profile["path_steps"],
                "proxyPatientId": None,
            }

        entity_name = self._patient_entity(patient_id)
        if entity_name in self._entity_to_id and profile["support_level"] != "minimal":
            predictions = self._predict_subject(
                entity_name=entity_name,
                primary_disease=primary_disease,
                timestamp=timestamp,
                topk=topk,
                latest_relations=profile["latest_relations"],
            )
            if predictions:
                return {
                    "predictions": predictions,
                    "mode": "model",
                    "strategy": "direct-model",
                    "supportSummary": "已使用训练图谱中的同名患者实体做直接时序推理。",
                    "evidence": evidence,
                    "pathExplanation": profile["path_steps"],
                    "proxyPatientId": None,
                }

        if profile["support_level"] != "minimal":
            proxy_match = self._match_proxy_patient(profile, exclude_entity_name=entity_name)
            if proxy_match and proxy_match.score >= 0.35:
                predictions = self._predict_subject(
                    entity_name=proxy_match.entity_name,
                    primary_disease=primary_disease,
                    timestamp=timestamp,
                    topk=topk,
                    latest_relations=profile["latest_relations"],
                    proxy_match=proxy_match,
                )
                if predictions:
                    matched = "、".join(proxy_match.matched_relations[:4]) or "病种相似"
                    return {
                        "predictions": predictions,
                        "mode": "model",
                        "strategy": "proxy-model",
                        "supportSummary": "已基于少量事件匹配到相似训练患者 {0}，参考关系包括 {1}。".format(
                            proxy_match.patient_id,
                            matched,
                        ),
                        "evidence": evidence,
                        "pathExplanation": profile["path_steps"],
                        "proxyPatientId": proxy_match.patient_id,
                    }

        if profile["event_count"] >= 2:
            return {
                "predictions": [],
                "mode": "similar-case",
                "strategy": "rules",
                "supportSummary": "当前事件数量有限，先采用规则与相似病例辅助建议，再等待更多连续事件。",
                "evidence": evidence,
                "pathExplanation": profile["path_steps"],
                "proxyPatientId": None,
            }

        return {
            "predictions": [],
            "mode": "similar-case",
            "strategy": "similar-case",
            "supportSummary": "当前结构化事件不足，建议先补录关键关系后再触发模型推理。",
            "evidence": evidence,
            "pathExplanation": profile["path_steps"],
            "proxyPatientId": None,
        }


MODEL_SERVICE = ChronicModelService()
