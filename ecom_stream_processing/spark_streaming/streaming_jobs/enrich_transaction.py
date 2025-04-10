import yaml
import os
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import col, from_json

# Load YAML config
with open("config/streaming_config.yaml", "r") as f:
    config = yaml.safe_load(f)



# Config values
app_name = config["app_name"]
brokers = config["kafka"]["brokers"]
transaction_topic = config["kafka"]["topics"]["transactions"]
user_topic = config["kafka"]["topics"]["users"]
starting_offsets = config["kafka"]["starting_offsets"]
output_mode = config["output"]["mode"]
truncate = config["output"]["truncate"]

print(f"🧪 Kafka brokers being used: {brokers}")

# Spark session
spark = SparkSession.builder.appName(app_name).getOrCreate()
spark.sparkContext.setLogLevel("WARN")

# Transaction schema
transaction_schema = StructType([
    StructField("transaction_id", StringType()),
    StructField("user_id", StringType()),
    StructField("item_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("timestamp", TimestampType())
])

# User schema
user_schema = StructType([
    StructField("user_id", StringType()),
    StructField("first_name", StringType()),
    StructField("last_name", StringType()),
    StructField("user_name", StringType()),
    StructField("user_type", StringType()),
    StructField("age_group", StringType()),
    StructField("gender", StringType()),
    StructField("address", StringType()),
    StructField("city", StringType()),
    StructField("state", StringType()),
    StructField("zipcode", StringType()),
    StructField("country", StringType()),
    StructField("account_creation_date", TimestampType()),
    StructField("last_login_time", TimestampType()),
    StructField("preferred_language", StringType()),
    StructField("persona", StringType())
])

# Read transaction stream
transactions_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", brokers) \
    .option("subscribe", transaction_topic) \
    .option("startingOffsets", starting_offsets) \
    .load()

transactions_parsed = transactions_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), transaction_schema).alias("data")) \
    .select("data.*")

# Read user stream
users_df = spark.readStream.format("kafka") \
    .option("kafka.bootstrap.servers", brokers) \
    .option("subscribe", user_topic) \
    .option("startingOffsets", starting_offsets) \
    .load()

users_parsed = users_df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), user_schema).alias("data")) \
    .select("data.*")

# Output both to console
transactions_query = transactions_parsed.writeStream \
    .format(output_mode) \
    .option("truncate", truncate) \
    .queryName("TransactionStream") \
    .start()

users_query = users_parsed.writeStream \
    .format(output_mode) \
    .option("truncate", truncate) \
    .queryName("UserStream") \
    .start()

transactions_query.awaitTermination()
users_query.awaitTermination()
