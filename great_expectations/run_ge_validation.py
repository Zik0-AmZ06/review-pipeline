#!/usr/bin/env python3
"""Run Great Expectations validation for ingestion."""
import sys
from pathlib import Path
import great_expectations as ge
from great_expectations.checkpoint import Checkpoint

# Try multiple import paths for modern GE versions
try:
    from great_expectations import DataContext
except Exception:
    try:
        from great_expectations.data_context import DataContext
    except Exception:
        try:
            from great_expectations.data_context.data_context import DataContext
        except Exception:
            from great_expectations.data_context import FileDataContext as DataContext

def main():
    ge_root = Path(__file__).parent
    context = DataContext(str(ge_root))

    # Run the checkpoint
    checkpoint = Checkpoint(
        name="ingestion_checkpoint",
        data_context=context,
        config_version=1.0,
        class_name="Checkpoint",
        run_name_template="%Y%m%d-%H%M%S-ingestion-validation",
        action_list=[
            {"name": "store_validation_result", "action": {"class_name": "StoreValidationResultAction"}},
            {"name": "store_evaluation_params", "action": {"class_name": "StoreEvaluationParametersAction"}},
            {"name": "update_data_docs", "action": {"class_name": "UpdateDataDocsAction", "site_names": ["local_site"]}},
        ],
        batches=[
            {
                "batch_kwargs": {
                    "path": str(ge_root.parent / "data" / "customers.csv"),
                    "datasource": "review_pipeline",
                    "data_connector": "customers",
                    "data_asset_name": "customers",
                },
                "expectation_suite_names": ["customers_suite"],
            },
            {
                "batch_kwargs": {
                    "path": str(ge_root.parent / "data" / "orders.csv"),
                    "datasource": "review_pipeline",
                    "data_connector": "orders",
                    "data_asset_name": "orders",
                },
                "expectation_suite_names": ["orders_suite"],
            },
            {
                "batch_kwargs": {
                    "path": str(ge_root.parent / "data" / "order_items.csv"),
                    "datasource": "review_pipeline",
                    "data_connector": "order_items",
                    "data_asset_name": "order_items",
                },
                "expectation_suite_names": ["order_items_suite"],
            },
        ],
    )

    results = checkpoint.run()

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
        print("\n❌ Validation FAILED")
        sys.exit(1)

    print("\n✅ All validations PASSED")
    print(f"\nData Docs available at: {ge_root}/data_docs/index.html")

if __name__ == "__main__":
    main()
