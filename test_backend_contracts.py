from __future__ import annotations

from test_closure_contract import (
    test_business_health_contract,
    test_middleware_trace_and_auth_contract,
    test_model_metrics_requires_admin,
    test_predict_api_contract,
)
from test_model_api_contract import test_model_auth_and_training_contract, test_model_health_contract


def main() -> None:
    test_predict_api_contract()
    test_middleware_trace_and_auth_contract()
    test_business_health_contract()
    test_model_metrics_requires_admin()
    test_model_health_contract()
    test_model_auth_and_training_contract()
    print("backend-contracts-ok")


if __name__ == "__main__":
    main()
