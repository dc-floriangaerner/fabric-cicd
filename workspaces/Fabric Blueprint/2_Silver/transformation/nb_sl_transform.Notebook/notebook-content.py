# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

# Silver Transformation Notebook
# Purpose: Read raw data from Bronze lakehouse, clean and transform, write to Silver lakehouse
# Layer: Bronze → Silver (Data Cleansing and Standardization)

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, trim, upper, to_date, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DateType

print("Starting Silver transformation process...")

# CELL ********************

# Configuration
# Note: Lakehouse references will be automatically transformed during deployment
# Dev lakehouse IDs are replaced with environment-specific IDs via parameter.yml

bronze_lakehouse = "lakehouse_bronze"
silver_lakehouse = "lakehouse_silver"
source_table = "raw_customers"
target_table = "cleaned_customers"

print(f"Source: {bronze_lakehouse}.{source_table}")
print(f"Target: {silver_lakehouse}.{target_table}")

# CELL ********************

# Read raw data from Bronze lakehouse
# Using Delta Lake format for ACID transactions and time travel
df_bronze = spark.read.format("delta").table(f"{bronze_lakehouse}.{source_table}")

print(f"Records read from Bronze: {df_bronze.count()}")
df_bronze.printSchema()

# CELL ********************

# Data Cleansing and Transformation
# Apply business rules and data quality improvements

df_silver = df_bronze \
    .dropDuplicates(["customer_id"]) \
    .filter(col("customer_id").isNotNull()) \
    .withColumn("customer_name", trim(upper(col("customer_name")))) \
    .withColumn("email", trim(col("email"))) \
    .withColumn("registration_date", to_date(col("registration_date"), "yyyy-MM-dd")) \
    .withColumn("processed_timestamp", current_timestamp()) \
    .select(
        "customer_id",
        "customer_name",
        "email",
        "registration_date",
        "country",
        "status",
        "processed_timestamp"
    )

print(f"Records after transformation: {df_silver.count()}")

# CELL ********************

# Data Quality Checks
null_counts = df_silver.select([
    col(c).isNull().cast("int").alias(c) 
    for c in df_silver.columns
]).groupBy().sum()

print("Null value counts by column:")
null_counts.show()

# CELL ********************

# Write cleaned data to Silver lakehouse
# Using MERGE operation for incremental updates (upsert pattern)

df_silver.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(f"{silver_lakehouse}.{target_table}")

print(f"Successfully wrote {df_silver.count()} records to Silver lakehouse")
print("Silver transformation complete!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
