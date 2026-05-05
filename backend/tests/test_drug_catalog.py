from __future__ import annotations

import os
import shutil
from pathlib import Path

import app.main  # noqa: F401

from app.schemas import DrugCatalogUpsertRequest
from app.services.drug_catalog_service import create_drug_catalog_item, get_drug_catalog_item, list_drug_catalog, update_drug_catalog_item


def main() -> None:
    temp_dir = Path(__file__).resolve().parent / "app" / "runtime" / "drug_catalog_test_case"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["CTPATH_DRUG_CATALOG_DIR"] = str(temp_dir)

    try:
        baseline = list_drug_catalog()
        assert len(baseline) >= 3, "expected seeded drug catalog records"

        payload = DrugCatalogUpsertRequest(
            drug_id="drug-test-amoxicillin",
            generic_name="Amoxicillin",
            brand_name="",
            dosage_form="capsule",
            specification="0.25 g",
            unit="box",
            is_prescription=True,
            is_controlled=False,
            status="active",
            indication="Bacterial infection",
        )

        created = create_drug_catalog_item(payload, updated_by="tester")
        assert created.drug_id == payload.drug_id
        assert created.generic_name == payload.generic_name

        fetched = get_drug_catalog_item(payload.drug_id)
        assert fetched.drug_id == payload.drug_id

        updated = update_drug_catalog_item(
            payload.drug_id,
            DrugCatalogUpsertRequest(
                drug_id=payload.drug_id,
                generic_name="Amoxicillin",
                brand_name="Amoxil",
                dosage_form="capsule",
                specification="0.25 g",
                unit="box",
                is_prescription=True,
                is_controlled=False,
                status="inactive",
                indication="Bacterial infection",
            ),
            updated_by="tester2",
        )
        assert updated.brand_name == "Amoxil"
        assert updated.status == "inactive"

        inactive = list_drug_catalog(status="inactive")
        assert any(item.drug_id == payload.drug_id for item in inactive)

        print("drug-catalog-ok")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    main()
