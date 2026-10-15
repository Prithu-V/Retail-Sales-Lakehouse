from pyspark import pipelines as dp

from pyspark.sql.functions import (
    col, trim, when, lit, to_date, regexp_replace
)

@dp.table(
    name = "silver_retail_transactions"
)

def silver_retail_transactions():
    df = spark.readStream.table(
    "retail_lakehouse.retail.bronze_retail_transactions"
)

    df = (
        df
        .withColumnRenamed("Invoice", "invoice_id")
        .withColumnRenamed("StockCode", "stock_code")
        .withColumnRenamed("Description", "description")
        .withColumnRenamed("Quantity", "quantity")
        .withColumnRenamed("InvoiceDate", "invoice_timestamp")
        .withColumnRenamed("Price", "unit_price")
        .withColumnRenamed("CustomerID", "customer_id")
        .withColumnRenamed("Country", "country")
    )

    df = (
        df
        .withColumn("invoice_id", trim(col('invoice_id')))
        .withColumn("stock_code", trim(col('stock_code')))
        .withColumn("description", trim(col('description')))
        .withColumn(
            "description",
            when(
                col("description").isNull()
                | (col("description") == ""),
                lit(None).cast("string")
            ).otherwise(col("description"))
        )
        .withColumn("country", trim(col("country")))
    )

    df = df.withColumn(
        "customer_id",
        when(
            col("customer_id").isNull()
            | (trim(col("customer_id")) == ""),
            lit(None).cast("string")
        ).otherwise(
            regexp_replace(trim(col("customer_id")), r"\.0$", "")
        )
    )

    df = df.withColumn(
        "invoice_date",
        to_date(col('invoice_timestamp'))
    )

    df = df.withColumn(
        "unit_price",
        col("unit_price").cast("decimal(12,2)")
    )

    df = df.withColumn(
        "line_amount",
        (col("quantity").cast("decimal(12,2)") * col("unit_price")).cast("decimal(12,2)")
    )

    df = df.withColumn(
        "transaction_type",
        when(
            col("invoice_id").startswith("C"),
            "CANCELLATION"
        )
        .when(
            col("invoice_id").startswith("A"),
            "ADJUSTMENT"
        )
        .when(
            (col("unit_price") == 0) & col('customer_id').isNull(),
            "NON_SALE"
        )
        .when(
            col("unit_price")==0,
            "ZERO_PRICE_REVIEW" 
        )
        .when(
            col("quantity") < 0,
            "OTHER_NEGATIVE_QUANTITY" 
        )
        .otherwise("SALE")
    )

    return df



