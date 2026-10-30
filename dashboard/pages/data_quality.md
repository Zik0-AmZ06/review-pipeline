---
title: Data Quality Issues
description: Documented data issues found during pipeline development
---

# 🔍 Data Quality Issues Log

## Stage 1: Raw Data Issues

| Issue | Severity | Evidence | Mitigation |
|-------|----------|----------|------------|
| Currency mixing (USD, EUR, GBP, CAD, AUD) | High | Revenue sums without conversion | FX normalization in Python loader |
| Text columns for dates/numbers | Medium | All raw columns are TEXT | Staging models cast to proper types |
| No foreign key enforcement | Medium | `customer_id` in orders not validated | dbt relationship tests |
| Cancelled/pending orders in raw data | Low | Status values: completed, cancelled, pending | Filtered to `completed` in fact |
| Price drift (same product, different prices) | Medium | "Wireless Headphones" at 150, 140 | dim_product takes latest price |
| All customers have orders | Low | 0 customers with 0 orders | Documented, not necessarily wrong |

## Stage 2: Modeling Decisions

| Decision | Rationale |
|----------|-----------|
| dim_product uses latest price (ROW_NUMBER) | Simple SCD Type 1 for demo |
| fact_order_items only includes `completed` | Revenue should reflect finalized orders |
| dim_date spans full order date range | Enables time-series analysis |
| Region mapping from country | Enables geographic slicing |

## Stage 3: Ingestion Validation

- Idempotent upserts via `ON CONFLICT` (staging) and dbt `unique_key` (fact)
- FX rates fetched per order date from Frankfurter API
- Comprehensive logging to `ingest/logs/ingest.log`

## Stage 4: Testing

- 30 dbt tests passing (unique, not_null, relationships)
- Incremental fact table verified idempotent (2nd run = 0 rows)
- Revenue reconciliation: fact (4423.50) = raw (4423.50)

## Remaining Gaps

1. No incremental loading for staging tables (full refresh each run)
2. No quarantine table for invalid rows
3. No scheduled orchestration (Airflow/cron)
4. No CI/CD pipeline
