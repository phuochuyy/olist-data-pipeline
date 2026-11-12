"""Great Expectations (0.18, fluent API) checks on the bronze tables in PostgreSQL.

Run inside the Airflow container (task `great_expectations_validation`) or by hand:
    python great_expectations/data_quality.py
Exit code 1 if any expectation fails. A JSON summary is written to
great_expectations/uncommitted/ (git-ignored).

The context is ephemeral (in memory), so no connection string is written to disk.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import great_expectations as gx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("data_quality")

CONNECTION = os.environ.get(
    "OLIST_DW_CONN", "postgresql+psycopg2://postgres:postgres@postgres:5432/olist_dw"
)
OUT_DIR = Path(__file__).resolve().parent / "uncommitted"

ORDER_STATUSES = ["delivered", "shipped", "canceled", "unavailable", "invoiced",
                  "processing", "created", "approved"]

# table in schema raw -> list of (expectation, kwargs)
SUITES = {
    "customers": [
        ("expect_column_to_exist", {"column": "customer_id"}),
        ("expect_column_values_to_not_be_null", {"column": "customer_id"}),
        ("expect_column_values_to_be_unique", {"column": "customer_id"}),
        ("expect_column_values_to_match_regex", {"column": "customer_state", "regex": r"^[A-Z]{2}$"}),
    ],
    "orders": [
        ("expect_column_values_to_not_be_null", {"column": "order_id"}),
        ("expect_column_values_to_be_unique", {"column": "order_id"}),
        ("expect_column_values_to_be_in_set", {"column": "order_status", "value_set": ORDER_STATUSES}),
        ("expect_column_values_to_not_be_null", {"column": "order_purchase_timestamp"}),
    ],
    "order_items": [
        ("expect_column_values_to_not_be_null", {"column": "order_id"}),
        ("expect_column_values_to_be_between", {"column": "price", "min_value": 0, "max_value": 10000}),
        ("expect_column_values_to_be_between", {"column": "freight_value", "min_value": 0, "max_value": 1000}),
    ],
    "products": [
        ("expect_column_values_to_not_be_null", {"column": "product_id"}),
        ("expect_column_values_to_be_unique", {"column": "product_id"}),
    ],
    "sellers": [
        ("expect_column_values_to_be_unique", {"column": "seller_id"}),
        ("expect_column_values_to_match_regex", {"column": "seller_state", "regex": r"^[A-Z]{2}$"}),
    ],
}


def run() -> dict:
    context = gx.get_context(mode="ephemeral")
    datasource = context.sources.add_postgres(name="olist_dw", connection_string=CONNECTION)

    summary = {"run_at": datetime.now(timezone.utc).isoformat(), "tables": {}, "success": True}
    for table, expectations in SUITES.items():
        asset = datasource.add_table_asset(name=table, table_name=table, schema_name="raw")
        suite_name = f"raw_{table}"
        context.add_or_update_expectation_suite(expectation_suite_name=suite_name)
        validator = context.get_validator(batch_request=asset.build_batch_request(),
                                          expectation_suite_name=suite_name)
        for expectation, kwargs in expectations:
            getattr(validator, expectation)(**kwargs)
        result = validator.validate()

        checks = []
        for r in result.results:
            cfg = r.expectation_config
            checks.append({
                "expectation": cfg.expectation_type,
                "column": cfg.kwargs.get("column"),
                "success": r.success,
                "unexpected_count": r.result.get("unexpected_count"),
            })
        summary["tables"][table] = {"success": result.success, "checks": checks}
        summary["success"] &= result.success
        log.info("raw.%s: %s (%d/%d expectations passed)", table,
                 "PASS" if result.success else "FAIL",
                 sum(c["success"] for c in checks), len(checks))
        for c in checks:
            if not c["success"]:
                log.warning("  failed %s on %s: %s unexpected rows",
                            c["expectation"], c["column"], c["unexpected_count"])
    return summary


def main() -> int:
    summary = run()
    OUT_DIR.mkdir(exist_ok=True)
    out = OUT_DIR / f"validation_{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.json"
    out.write_text(json.dumps(summary, indent=2))
    log.info("summary written to %s", out)
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
