#!/usr/bin/env python3
"""Run Great Expectations validation for ingestion (GE 0.18+ compatible)."""
import sys
from pathlib import Path
import great_expectations as ge
from great_expectations.checkpoint import Checkpoint
from great_expectations.core.batch import BatchRequest

def main():
    ge_root = Path(__file__).parent

    # Create DataContext - GE 0.18+ automatically finds great_expectations.yml
    context = ge.get_context(context_root_dir=str(ge_root))

    # Define batch requests using the new v3 API
    batch_requests = [
        BatchRequest(
            datasource_name="review_pipeline",
            data_connector_name="customers",
            data_asset_name="customers",
            batch_spec_passthrough={"path": str(ge_root.parent / "data" / "customers.csv")},
        ),
        BatchRequest(
            datasource_name="review_pipeline",
            data_connector_name="orders",
            data_asset_name="orders",
            batch_spec_passthrough={"path": str(ge_root.parent / "data" / "orders.csv")},
        ),
        BatchRequest(
            datasource_name="review_pipeline",
            data_connector_name="order_items",
            data_asset_name="order_items",
            batch_spec_passthrough={"path": str(ge_root.parent / "data" / "order_items.csv")},
        ),
    ]

    # Create checkpoint using new API
    checkpoint = Checkpoint(
        name="ingestion_checkpoint",
        data_context=context,
        run_name_template="%Y%m%d-%H%M%S-ingestion-validation",
        action_list=[
            {"name": "store_validation_result", "action": {"class_name": "StoreValidationResultAction"}},
            {"name": "store_evaluation_params", "action": {"class_name": "StoreEvaluationParametersAction"}},
            {"name": "update_data_docs", "action": {"class_name": "UpdateDataDocsAction", "site_names": ["local_site"]}},
        ],
    )

    # Run checkpoint with batch requests
    results = checkpoint.run(
        batch_request=batch_requests,
        expectation_suite_names=["customers_suite", "orders_suite", "order_items_suite"],
    )

    # Print summary
    print(f"\n{'='*60}")
    print(f"Great Expectations Validation Results")
    print(f"{'='*60}")
    for result in results["run_results"].values():
        vr = result["validation_result"]
        print(f"\nSuite: {vr['expectation_suite_name']}")
        print(f"  Success: {vr['success']}")
        print(f"  Expectations: {vr['statistics']['evaluated_expectations']}")
        print(f"  Passed: {vr['statistics']['successful_expectations']}")
        print(f"  Failed: {vr['statistics']['unsuccessful_expectations']}")

    if not results["success"]:
        print("\n✗ Validation FAILED")
        sys.exit(1)

    print("\n✓ All validations PASSED")
    print(f"\nData Docs available at: {ge_root}/data_docs/index.html")

if __name__ == "__main__":
    main()