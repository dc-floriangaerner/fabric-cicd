# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# CELL ********************

# Gold Modeling Notebook
# Purpose: Create aggregated and business-ready analytics tables from Silver layer
# Layer: Silver → Gold (Business Logic and Aggregations)

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum, avg, min, max, 
    year, month, dayofmonth, current_timestamp,
    dense_rank, row_number
)
from pyspark.sql.window import Window

print("Starting Gold modeling process...")

# CELL ********************

# Configuration
# Note: Lakehouse references will be automatically transformed during deployment
# Dev lakehouse IDs are replaced with environment-specific IDs via parameter.yml

silver_lakehouse = "lakehouse_silver"
gold_lakehouse = "lakehouse_gold"
source_table = "cleaned_customers"
target_table = "customer_analytics"

print(f"Source: {silver_lakehouse}.{source_table}")
print(f"Target: {gold_lakehouse}.{target_table}")

# CELL ********************

# Read cleaned data from Silver lakehouse
df_silver = spark.read.format("delta").table(f"{silver_lakehouse}.{source_table}")

print(f"Records read from Silver: {df_silver.count()}")

# CELL ********************

# Create aggregated analytics table
# Group customers by country and registration month

df_gold = df_silver \
    .withColumn("registration_year", year(col("registration_date"))) \
    .withColumn("registration_month", month(col("registration_date"))) \
    .groupBy("country", "registration_year", "registration_month", "status") \
    .agg(
        count("customer_id").alias("customer_count"),
        count(col("email")).alias("customers_with_email")
    ) \
    .withColumn("email_completion_rate", 
                col("customers_with_email") / col("customer_count")) \
    .withColumn("model_timestamp", current_timestamp()) \
    .orderBy("country", "registration_year", "registration_month")

print(f"Aggregated records created: {df_gold.count()}")

# CELL ********************

# Preview aggregated data
print("Sample of Gold layer analytics:")
df_gold.show(20, truncate=False)

# CELL ********************

# Calculate customer rankings by country
window_spec = Window.partitionBy("country").orderBy(col("customer_count").desc())

df_country_ranks = df_silver \
    .groupBy("country") \
    .agg(
        count("customer_id").alias("total_customers"),
        count(col("email").isNotNull()).alias("customers_with_email"),
        count(col("status") == "active").alias("active_customers")
    ) \
    .withColumn("country_rank", dense_rank().over(Window.orderBy(col("total_customers").desc()))) \
    .withColumn("model_timestamp", current_timestamp())

print("Customer rankings by country:")
df_country_ranks.show(10, truncate=False)

# CELL ********************

# Write aggregated analytics to Gold lakehouse
df_gold.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(f"{gold_lakehouse}.{target_table}")

# Write country rankings
df_country_ranks.write \
    .format("delta") \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .saveAsTable(f"{gold_lakehouse}.customer_country_rankings")

print(f"Successfully wrote analytics to Gold lakehouse:")
print(f"  - {target_table}: {df_gold.count()} records")
print(f"  - customer_country_rankings: {df_country_ranks.count()} records")
print("Gold modeling complete!")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
