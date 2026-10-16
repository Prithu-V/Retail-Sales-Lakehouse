# Retail Sales Lakehouse

A Databricks lakehouse project that transforms raw retail transaction files into cleaned, validated, and analysis-ready tables for business reporting.

## Project objective

Retail transaction data can contain missing customer identifiers, cancellations, negative quantities, zero-price rows, and unusual values. This project organizes the data into Bronze, Silver, and Gold layers so that data preparation and business reporting are easier to inspect and maintain.

The project demonstrates a practical analytics workflow using Databricks, PySpark, SQL, Delta tables, and data-quality checks.

## Architecture

```text
Online Retail II source files
          |
          v
Bronze: retail_lakehouse.retail.bronze_retail_transactions
          |
          v
Silver: retail_lakehouse.retail.silver_retail_transactions
          |
          +-------------------+--------------------+-------------------+
          |                   |                    |                   |
          v                   v                    v                   v
Gold: gold_kpis   gold_product_performance   gold_customer_analysis   gold_country_performance
```

See [`docs/Architecture.md`](docs/Architecture.md) for the layer-by-layer design.

## Technology

- **Databricks** — data engineering and analytics environment
- **PySpark** — transformations and ingestion logic
- **Lakeflow Declarative Pipelines** — pipeline-based table creation where configured
- **Auto Loader** — file ingestion for the Bronze layer
- **Delta tables** — managed analytical storage
- **SQL** — Gold-layer aggregation and validation
- **Git / GitHub** — source control and project documentation

## Data flow

### Bronze

The Bronze table stores the source transactions ingested from the input files. It provides the raw-data foundation for subsequent transformations.

### Silver

The Silver table standardizes column names, trims text fields, normalizes missing customer identifiers, creates a date-only field, casts prices to a decimal type, calculates line amounts, and classifies transaction rows.

The current transaction classifications are:

- `SALE`
- `CANCELLATION`
- `ADJUSTMENT`
- `NON_SALE`
- `ZERO_PRICE_REVIEW`
- `OTHER_NEGATIVE_QUANTITY`

These labels are rules for analytical use, not a claim that every unusual record has been manually verified.

### Gold

The Gold layer contains four analytical tables:

| Table | Purpose |
|---|---|
| `retail_lakehouse.gold.gold_kpis` | Daily sales, cancellation value, net sales, sale invoice count, units sold, and average order value |
| `retail_lakehouse.gold.gold_product_performance` | Revenue and unit metrics by product |
| `retail_lakehouse.gold.gold_customer_analysis` | Purchase metrics for rows with a known customer identifier |
| `retail_lakehouse.gold.gold_country_performance` | Revenue, units, invoice counts, and identified-customer counts by country |

See [`docs/data_dictionary.md`](docs/data_dictionary.md) for the intended meaning of the tables and metrics.

## Validation and reconciliation

During validation, the Silver table contained **1,067,371 rows** and **53,628 distinct invoice identifiers**. The source data covered **1 December 2009 through 9 December 2011**.

The Silver checks found **243,007 rows with missing customer identifiers**. Missing customer identifiers are retained in Silver rather than silently discarded. Customer-level analysis excludes unidentified customers, while country-level revenue analysis includes their sales and counts distinct non-null customers.

The transaction-category revenue totals observed during validation were:

| Category | Rows | Line amount total |
|---|---:|---:|
| `SALE` | 1,041,651 | 20,961,532.49 |
| `CANCELLATION` | 19,494 | -1,526,667.86 |
| `NON_SALE` | 6,131 | 0.00 |
| `ZERO_PRICE_REVIEW` | 89 | 0.00 |
| `ADJUSTMENT` | 6 | -147,614.08 |

Amounts are shown in the dataset's original currency units; confirm the currency convention before presenting these figures as a specific currency. Gold sales-revenue aggregations were reconciled against Silver `SALE` rows.

The validation figures above are a snapshot from a project run. Re-run the validation notebooks if the source files or pipeline logic change.

## Business rules and caveats

- Rows classified as `SALE` are used for the main product, customer, country, and daily gross-sales metrics.
- Cancellation value in `gold_kpis` is calculated using the absolute value of cancellation line amounts; daily net sales is defined as gross sales minus cancellation value.
- Missing customer IDs are not treated as a real customer.
- Zero-price, adjustment, and other negative-quantity rows are classified separately for review rather than being automatically counted as ordinary sales.
- Repeated-looking transaction rows are not automatically deduplicated. Repeated lines may be legitimate, so a deduplication rule should be based on source semantics and investigation.
- The current project includes data-quality checks, but not every anomalous value has been resolved or explained.
- `average_order_value` is daily gross sales divided by the number of distinct sale invoices for that date. Verify invoice/date assumptions before interpreting this as a fully reconciled order-level metric.

## Repository contents

```text
retail_lakehouse/
├── README.md
├── docs/
│   ├── Architecture.md
│   ├── data_dictionary.md
│   └── data_quality.md
├── bronze_data_quality_check
├── silver_data_quality_check.dbquery.ipynb
├── gold_kpis
├── gold_product_performance.dbquery.ipynb
├── gold_customer_analysis.dbquery.ipynb
├── gold_country_performance.dbquery.ipynb
├── setup
└── Online Retail Excel Explorer
```

Actual file extensions and names may vary based on how Databricks exports or stores each notebook.

## How to reproduce

1. Obtain the Online Retail II dataset from its original publisher and review its licence and usage terms.
2. Place the source files in the configured Databricks volume location. The current project was configured to read from:

   `/Volumes/retail_lakehouse/retail/retail_files/incoming/`

3. Confirm the catalog, schemas, volume permissions, and compute availability in your Databricks workspace.
4. Run the setup notebook and configure the Bronze ingestion pipeline according to the workspace configuration.
5. Run the Silver transformation pipeline.
6. Run the Bronze and Silver data-quality checks.
7. Create or refresh the four Gold tables using the corresponding SQL notebooks.
8. Run the validation queries and compare the outputs with the documented results.

The exact execution order and pipeline settings depend on the Databricks workspace. Do not run the steps blindly in a different environment without checking catalog and volume configuration.

## Project status

This is a portfolio and learning project. It demonstrates a layered data workflow and business-oriented analytical tables. It should not be described as production-ready without further operational, security, testing, and incremental-refresh work.
