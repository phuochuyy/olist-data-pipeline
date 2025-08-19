#!/bin/bash
# Fix for Spark shell ivy configuration issue

echo "🔧 Fixing Spark configuration..."

# Create ivy directory
mkdir -p /tmp/.ivy2/local

# Set environment variables
export HOME=/tmp
export IVY_CACHE_DIR=/tmp/.ivy2
export SPARK_HOME=/opt/bitnami/spark

# Start Python with PySpark in local mode
echo "🐍 Starting PySpark shell..."
python3 << 'EOF'
import os
os.environ['HOME'] = '/tmp'

from pyspark.sql import SparkSession

# Create Spark session in local mode (no cluster needed)
spark = SparkSession.builder \
    .appName("InteractivePySpark") \
    .master("local[*]") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.ui.port", "4041") \
    .getOrCreate()

print("✅ PySpark session created successfully!")
print("📊 Spark UI: http://localhost:4041")
print("🔧 Available objects: 'spark' (SparkSession)")
print("💡 Example: spark.range(10).show()")
print("💡 To read CSV: spark.read.csv('path/to/file.csv', header=True)")
print("💡 Exit with: exit() or Ctrl+D")
print()

# Start interactive shell
import code
code.interact(local=dict(globals(), **locals()))
EOF
