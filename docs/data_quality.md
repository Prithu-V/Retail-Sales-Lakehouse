# Data Quality and Cleaning Decisions

## Purpose

The purpose of the data-quality work is to understand the source data before using it for business reporting. The project profiles missing values, transaction types, numeric extremes, and aggregate totals. Cleaning decisions are recorded explicitly so that unusual records are not silently removed.

## Observed validation snapshot

The following values were observed during a project validation run. Re-run the notebooks if the source files or transformation logic change.

| Check | Observed result |
|---|---:|
| Silver rows | 1,067,371 |
| Distinct invoice IDs | 53,628 |
| Distinct stock codes | 5,304 |
| Rows with missing customer IDs | 243,007 |
| Rows with negative quantity | 22,950 |
| Rows with negative unit price | 5 |
| Rows with zero unit price | 6,220 |
| Minimum quantity | -80,995 |
| Minimum unit price | -53,594.36 |
| Minimum line amount | -168,469.60 |

The source date range was 1 December 2009 through 9 December 2011. The source timestamp may include a time component; `invoice_date` is derived as a date-only column for grouping.

## Missing values

### Customer ID

Missing customer IDs are retained as null in Silver. A missing ID means that the transaction cannot reliably be assigned to a known customer.

- Customer-level Gold analysis excludes rows without a customer ID.
- Country-level sales metrics include qualifying sales with missing customer IDs.
- Distinct customer counts ignore null IDs.

This avoids excluding otherwise valid sales from broader revenue analysis while avoiding treating null as a customer.

### Description

Blank or whitespace-only descriptions are normalized to null. A missing description should be investigated if product-level reporting depends on product names. Stock codes remain useful for grouping where present.

## Transaction classification

The current Silver logic assigns a `transaction_type` according to ordered rules.

| Category | Observed rows | Current interpretation |
|---|---:|---|
| `SALE` | 1,041,651 | Ordinary sales under the current rules |
| `CANCELLATION` | 19,494 | Invoice ID begins with `C` |
| `NON_SALE` | 6,131 | Zero price and missing customer ID |
| `ZERO_PRICE_REVIEW` | 89 | Zero price with a customer ID |
| `ADJUSTMENT` | 6 | Invoice ID begins with `A` |
| `OTHER_NEGATIVE_QUANTITY` | Not listed separately in the snapshot | Negative quantity not caught by earlier rules |

The classification is rule-based, not a manual audit of each row. Since rules are ordered, cancellation and adjustment prefixes take precedence over later tests.

## Negative quantities and cancellations

Negative quantities can represent returns, cancellations, or adjustments. The project does not automatically remove all negative-quantity rows because doing so could remove meaningful business events.

Cancellations are identified using invoice IDs beginning with `C`. The Gold KPI table reports cancellation value as an absolute amount and calculates net sales as gross sales minus cancellation value. The daily date used for the cancellation is the cancellation transaction date, which may differ from the original sale date.

Extreme negative quantities, including the minimum observed quantity of -80,995, should be inspected to establish whether they represent legitimate bulk corrections, source anomalies, or another business event.

## Negative and zero prices

Five rows with negative unit prices were observed. The adjustment category contains six rows, so these counts should not be assumed to match. Inspect the actual records and their invoice IDs, quantities, descriptions, and source files before deciding how they should affect revenue.

Zero-price rows are not all treated identically:

- Rows with no customer ID are classified as `NON_SALE`.
- Rows with a customer ID are classified as `ZERO_PRICE_REVIEW`.

These rows remain available for auditing but are excluded from Gold tables filtered to `SALE`.

## Duplicate-looking rows

Repeated invoice and stock-code combinations were observed in profiling. This does not prove that the records are duplicates: an invoice can contain multiple lines for a product, and identical-looking lines can occur in source data.

The current Silver approach does not automatically deduplicate records. Before deduplication is introduced, define a source-supported transaction-line key and compare repeated records against the source files.

## Reconciliation

The observed `SALE` line-amount total was **20,961,532.49**. Gold revenue tables were checked against the Silver `SALE` population and their totals matched during the validation run.

The sum of all classified line amounts was approximately **19,287,250.55**, compared with the Bronze total of approximately **19,287,250.57**. The small difference should be understood in the context of decimal casting and aggregation; verify the exact calculation if strict financial reconciliation is required.

## Recommended next checks

1. Inspect all five negative-price rows and all six adjustment rows.
2. Inspect extreme negative-quantity rows.
3. Confirm the source meaning of invoice IDs beginning with `C` and `A`.
4. Define a defensible duplicate policy using source semantics.
5. Add automated assertions for row counts, null rules, transaction categories, and revenue reconciliation.
6. Re-run checks after any change to Silver classification logic.

## Limitations

These checks document the observed state of the project; they do not certify that every anomalous row has been resolved. Keep the original source data available and preserve the reasoning behind any future exclusions or corrections.
