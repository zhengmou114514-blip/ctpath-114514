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


class ChronicModelService:
    def __init__(self) -> None:
        self.available = False
        self.error = None  # type: Optional[str]
        self.device = os.getenv("CTPATH_MODEL_DEVICE", "cpu")
        self.checkpoint_path = Path(os.getenv("CTPATH_MODEL_CHECKPOINT", str(DEFAULT_CHECKPOINT)))
        self.rank = int(os.getenv("CTPATH_MODEL_RANK", "800"))
        self.n_hidden = int(os.getenv("CTPATH_MODEL_N_HIDDEN", "160"))
        self.num_walks = int(os.getenv("CTPATH_MODEL_NUM_WALKS", "1"))
        self.walk_len = int(os.getenv("CTPATH_MODEL_WALK_LEN", "8"))
        self._torch = None
        self._model = None
        self._args = None
        self._entity_to_id = {}  # type: Dict[str, int]
        self._id_to_entity = {}  # type: Dict[int, str]
        self._relation_to_id = {}  # type: Dict[str, int]
        self._timestamp_to_id = {}  # type: Dict[str, int]
        self._sorted_timestamps = []  # type: List[str]
        self._relation_candidates = {}  # type: Dict[str, List[int]]
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
            stat = pickle.load(open(DATA_DIR / "stat", "rb"))
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
            self.available = True
        except Exception as exc:  # pragma: no cover
            self.error = str(exc)
            self.available = False

    def _read_mapping_file(self, path: Path) -> Dict[str, int]:
        mapping = {}  # type: Dict[str, int]
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
        walks = []  # type: List[List[int]]
        timestamps = []  # type: List[List[int]]
        weights = []  # type: List[List[float]]
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
        relation_to_objects = {}  # type: Dict[str, Set[int]]
        for split in ["train", "valid", "test"]:
            with open(DATA_DIR / split, "r", encoding="utf-8") as file:
                for line in file:
                    _lhs, relation, rhs, _timestamp = line.rstrip("\n").split("\t")
                    relation_to_objects.setdefault(relation, set()).add(self._entity_to_id[rhs])
        self._relation_candidates = dict((key, sorted(value)) for key, value in relation_to_objects.items())

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
            return ["stage", "med_adherence", "support_system"]
        if "肾" in primary_disease:
            return ["stage", "mood_bin", "support_system"]
        if "阿尔茨海默" in primary_disease:
            return ["stage", "support_system", "sleep_hours_bin"]
        return ["stage", "med_adherence", "support_system"]

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

        predictions = []  # type: List[ModelPrediction]
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

    def predict_patient(self, patient_id: str, primary_disease: str, timestamp: str, topk: int = 3) -> List[dict]:
        if not self.available:
            return []
        entity_name = self._patient_entity(patient_id)
        subject_id = self._entity_to_id.get(entity_name)
        if subject_id is None:
            return []
        timestamp_id = self._timestamp_id(timestamp)
        relation_names = self._select_relations(primary_disease)
        results = []  # type: List[dict]
        for relation_name in relation_names:
            predictions = self._score_relation(subject_id, relation_name, timestamp_id, topk=1)
            if not predictions:
                continue
            prediction = predictions[0]
            normalized_score = 1 / (1 + math.exp(-prediction.score / 25))
            results.append(
                {
                    "label": "{0} -> {1}".format(relation_name, prediction.label),
                    "score": normalized_score,
                    "reason": "CTpath 在关系 {0} 上对候选 {1} 的打分最高。".format(relation_name, prediction.label),
                }
            )
        return results[:topk]


MODEL_SERVICE = ChronicModelService()
