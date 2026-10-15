# Architecture

## Overview

This project uses a Bronze–Silver–Gold architecture in Databricks. Each layer has a separate purpose: retain ingested source data, standardize and classify records, and provide tables for business analysis.

```text
Source CSV files
      |
      v
Bronze table
retail_lakehouse.retail.bronze_retail_transactions
      |
      v
Silver table
retail_lakehouse.retail.silver_retail_transactions
      |
      +--------------------+--------------------+--------------------+
      |                    |                    |                    |
      v                    v                    v                    v
gold_kpis       gold_product_performance  gold_customer_analysis  gold_country_performance
```

## Source and ingestion

The project uses the UCI Online Retail II dataset, supplied as retail transaction files. The Databricks volume configured for incoming files is:

`/Volumes/retail_lakehouse/retail/retail_files/incoming/`

The Bronze ingestion notebook/pipeline uses Databricks Auto Loader to discover and ingest source files. Auto Loader tracks file ingestion state through its configured streaming/checkpoint mechanism; exact settings depend on the current pipeline configuration.

## Bronze layer

**Table:** `retail_lakehouse.retail.bronze_retail_transactions`

Purpose:

- Provide a landing table for source transactions.
- Preserve the source fields for traceability and downstream transformations.
- Support profiling and data-quality investigation before cleaning.

Bronze is not intended to be the primary reporting layer. Analysts should use Silver or Gold tables for the documented analytical use cases.

## Silver layer

**Table:** `retail_lakehouse.retail.silver_retail_transactions`

Purpose:

- Standardize column names.
- Trim text values.
- Normalize missing customer identifiers to null and remove a trailing `.0` from string-form identifiers.
- Derive `invoice_date` from the invoice timestamp.
- Cast unit price to a decimal type.
- Calculate `line_amount` as quantity multiplied by unit price.
- Classify transaction rows using the project’s current rules.

The Silver table keeps unusual records available for review. It does not simply discard all cancellations, negative quantities, or zero-price rows.

### Transaction classification order

The current logic applies the following conditions in order:

1. Invoice IDs beginning with `C` are classified as `CANCELLATION`.
2. Invoice IDs beginning with `A` are classified as `ADJUSTMENT`.
3. A zero-price row with no customer ID is classified as `NON_SALE`.
4. A zero-price row with a customer ID is classified as `ZERO_PRICE_REVIEW`.
5. Other rows with negative quantity are classified as `OTHER_NEGATIVE_QUANTITY`.
6. Remaining rows are classified as `SALE`.

Because conditions are evaluated in order, the first matching condition determines the category. These are working business rules and should be revised if further investigation shows the source data requires different treatment.

## Gold layer

Gold tables are designed for specific reporting questions rather than general-purpose cleaning.

### `retail_lakehouse.gold.gold_kpis`

Grain: one row per `invoice_date`.

Contains:

- `gross_sales`: sum of `line_amount` for `SALE` rows on that date.
- `cancellation_value`: sum of absolute `line_amount` for `CANCELLATION` rows on that date.
- `net_sales`: `gross_sales - cancellation_value`.
- `sale_invoices`: distinct invoice IDs among `SALE` rows on that date.
- `units_sold`: sum of quantity for `SALE` rows on that date.
- `average_order_value`: daily gross sales divided by daily distinct sale invoices, where the denominator is nonzero.

Caveat: cancellation dates may not be the same as the original sale dates. Therefore, subtracting cancellation value on the cancellation date is a daily operational view, not necessarily a restatement of the original sale date.

### `retail_lakehouse.gold.gold_product_performance`

Grain: one row per grouped `stock_code` and `description`.

Contains total sale line revenue, units sold, distinct invoice count, and average line-level selling price. The average selling price is a simple average of unit prices across qualifying rows; it is not quantity-weighted.

### `retail_lakehouse.gold.gold_customer_analysis`

Grain: one row per known `customer_id`.

Contains sales revenue, units sold, distinct invoice count, average revenue per distinct invoice, and first/last observed invoice dates, using the current `SALE` filter. Rows without a customer identifier are excluded because they cannot be attributed to a specific customer.

### `retail_lakehouse.gold.gold_country_performance`

Grain: one row per country.

Contains sale revenue, units sold, distinct invoice count, and distinct non-null customer count. Revenue includes qualifying sales even when the customer ID is missing; the distinct-customer count ignores null customer IDs.

## Design choices

- Separate layers make transformation logic easier to review.
- Silver retains records needing review instead of dropping them automatically.
- Gold tables use explicit business filters to make the meaning of each metric clearer.
- Revenue and quantity metrics should be reconciled to the same Silver filters before they are compared.
- The tables are materialized using the project’s current Databricks pipeline and SQL setup. Refresh behavior should be verified in the workspace before describing it as fully automated or incremental.

## Operational considerations

A fresh workspace needs the relevant catalog, schemas, volume, permissions, compute, source files, and pipeline configuration. Databricks Free Edition may have compute or usage limits that affect pipeline runs. This documentation does not imply that all resources are created automatically.
