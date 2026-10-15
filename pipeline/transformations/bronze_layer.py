from pyspark import pipelines as dp

from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType,
    TimestampType
)

from pyspark.sql.functions import (
    current_timestamp,
    regexp_extract,
    col
)


@dp.table(
    name="bronze_retail_transactions"
)
def bronze_retail_transactions():

    # Schema of the incoming CSV files
    source_schema = StructType([
        StructField("Invoice", StringType(), True),
        StructField("StockCode", StringType(), True),
        StructField("Description", StringType(), True),
        StructField("Quantity", IntegerType(), True),
        StructField("InvoiceDate", TimestampType(), True),
        StructField("Price", DoubleType(), True),
        StructField("Customer ID", StringType(), True),
        StructField("Country", StringType(), True)
    ])

    # Read incoming files using Auto Loader
    df = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("header", "true")
        .schema(source_schema)
        .load(
            "/Volumes/retail_lakehouse/retail/retail_files/incoming/"
        )
    )

    # Rename problematic source column for Delta compatibility
    df = df.withColumnRenamed(
        "Customer ID",
        "CustomerID"
    )

    # Add ingestion metadata
    return (
        df
        .withColumn(
            "_ingestion_timestamp",
            current_timestamp()
        )
        .withColumn(
            "_source_file",
            col("_metadata.file_path")
        )
        .withColumn(
            "_batch_id",
            regexp_extract(
                col("_metadata.file_path"),
                r"retail_(\d{4}-\d{2})\.csv",
                1
            )
        )
    )