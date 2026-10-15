# Data Dictionary

This document describes the main tables and metrics used in the retail sales lakehouse. Confirm the exact column types and complete schemas in Databricks before treating this as a generated schema reference.

## Table overview

| Table | Layer | Grain | Main use |
|---|---|---|---|
| `retail_lakehouse.retail.bronze_retail_transactions` | Bronze | Source transaction row | Source landing and profiling |
| `retail_lakehouse.retail.silver_retail_transactions` | Silver | Source transaction row after standardization | Cleaned, classified transaction analysis |
| `retail_lakehouse.gold.gold_kpis` | Gold | One row per invoice date | Daily KPI reporting |
| `retail_lakehouse.gold.gold_product_performance` | Gold | One row per stock code and description | Product performance |
| `retail_lakehouse.gold.gold_customer_analysis` | Gold | One row per known customer ID | Customer purchase analysis |
| `retail_lakehouse.gold.gold_country_performance` | Gold | One row per country | Geographic sales analysis |

## Bronze table

**Table:** `retail_lakehouse.retail.bronze_retail_transactions`

The Bronze table contains the ingested source fields. The original source columns included:

| Source column | Meaning |
|---|---|
| `Invoice` | Invoice identifier |
| `StockCode` | Product or stock identifier |
| `Description` | Product description |
| `Quantity` | Quantity on the transaction line |
| `InvoiceDate` | Source transaction timestamp |
| `Price` | Unit price in the source dataset |
| `CustomerID` | Customer identifier, where supplied |
| `Country` | Country associated with the transaction |

The Bronze schema may include ingestion metadata or pipeline-managed fields depending on its implementation.

## Silver table

**Table:** `retail_lakehouse.retail.silver_retail_transactions`

| Column | Meaning |
|---|---|
| `invoice_id` | Trimmed invoice identifier |
| `stock_code` | Trimmed stock/product identifier |
| `description` | Trimmed description; blank values are normalized to null |
| `quantity` | Transaction-line quantity; negative values are retained for classification and review |
| `invoice_timestamp` | Source invoice timestamp |
| `unit_price` | Unit price cast to decimal |
| `customer_id` | Customer identifier normalized to a string; missing values remain null |
| `country` | Trimmed country value |
| `invoice_date` | Date derived from `invoice_timestamp`, without time of day |
| `line_amount` | `quantity * unit_price`, cast to decimal |
| `transaction_type` | Classification assigned by the current Silver rules |

The precise data types of all fields should be checked in the actual table schema. Additional source or metadata fields may be present.

### `transaction_type` values

| Value | Meaning under current rules |
|---|---|
| `SALE` | Does not match an earlier special-case rule |
| `CANCELLATION` | Invoice ID begins with `C` |
| `ADJUSTMENT` | Invoice ID begins with `A` |
| `NON_SALE` | Zero unit price and missing customer ID |
| `ZERO_PRICE_REVIEW` | Zero unit price and a known customer ID |
| `OTHER_NEGATIVE_QUANTITY` | Negative quantity not already classified by a preceding rule |

These meanings reflect the current rule order; they are not a substitute for source-specific business definitions.

## Gold KPI table

**Table:** `retail_lakehouse.gold.gold_kpis`

**Grain:** one row per `invoice_date`.

| Column | Meaning |
|---|---|
| `invoice_date` | Date of the transaction rows used for the daily aggregate |
| `gross_sales` | Sum of `line_amount` for rows classified as `SALE` |
| `cancellation_value` | Sum of absolute `line_amount` for rows classified as `CANCELLATION` |
| `net_sales` | `gross_sales - cancellation_value` for that date |
| `sale_invoices` | Distinct invoice IDs among `SALE` rows on that date |
| `units_sold` | Sum of quantity for `SALE` rows on that date |
| `average_order_value` | `gross_sales / sale_invoices` when the denominator is nonzero |

**Interpretation note:** this is a date-based KPI view. A cancellation may be recorded on a different date from its original sale, so daily net sales is not necessarily a restatement of original sale-day revenue.

## Gold product performance table

**Table:** `retail_lakehouse.gold.gold_product_performance`

**Grain:** one row per grouped `stock_code` and `description`, filtered to `SALE` rows.

| Column | Meaning |
|---|---|
| `stock_code` | Product/stock identifier |
| `description` | Product description |
| `total_revenue` | Sum of sale `line_amount` for the group |
| `unit_sold` | Sum of sale quantity for the group |
| `invoice_count` | Distinct sale invoice count for the group |
| `avg_selling_price` | Simple average of line-level `unit_price` values for the group |

`avg_selling_price` is not weighted by quantity. The actual table may use the exact output column names shown by the SQL query.

## Gold customer analysis table

**Table:** `retail_lakehouse.gold.gold_customer_analysis`

**Grain:** one row per known customer ID, filtered to `SALE` rows.

| Metric | Meaning |
|---|---|
| Customer identifier | Known customer associated with the group |
| Revenue | Sum of sale line amounts |
| Units sold | Sum of sale quantities |
| Invoice count | Distinct sale invoices |
| Average order value | Revenue divided by distinct invoice count |
| First observed date | Earliest qualifying invoice date |
| Last observed date | Latest qualifying invoice date |

The exact output column names depend on the SQL used to create the table. Confirm them in Databricks and update this section if they differ.

## Gold country performance table

**Table:** `retail_lakehouse.gold.gold_country_performance`

**Grain:** one row per country, filtered to `SALE` rows.

| Metric | Meaning |
|---|---|
| `country` | Country value associated with the transaction |
| Revenue | Sum of sale line amounts |
| Units sold | Sum of sale quantities |
| Invoice count | Distinct sale invoice count |
| Customer count | Distinct non-null customer IDs |

Rows with missing customer IDs can still contribute to revenue, units, and invoice counts. Null customer IDs are ignored by distinct-customer counting.

## Metric conventions

- Monetary values use the source dataset's price units. Confirm the currency before labelling values as GBP or another currency in reports.
- Revenue figures are sums of `line_amount` after the table's transaction filter.
- Invoice counts use distinct invoice identifiers, not transaction-row counts.
- Missing customer IDs are null, not a synthetic customer.
- Always compare metrics using the same transaction filter, date grain, and cancellation treatment.
