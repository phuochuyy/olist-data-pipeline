.PHONY: help spark-test spark-bash pyspark spark-shell

help:
	@echo "🚀 Olist Data Pipeline Commands:"
	@echo "  spark-test    - Test Spark installation"
	@echo "  spark-bash    - Open Spark container shell"
	@echo "  pyspark       - PySpark shell instructions"

spark-test:
	@echo "🧪 Testing Spark installation..."
	docker compose exec spark-master python3 -c "import pyspark; print('✅ PySpark version:', pyspark.__version__)"

spark-bash:
	@echo "💻 Opening Spark container bash..."
	@echo "💡 Inside container you can run:"
	@echo "   python3"
	@echo "   from pyspark.sql import SparkSession"
	@echo "   spark = SparkSession.builder.master('local[*]').getOrCreate()"
	docker compose exec spark-master bash

pyspark:
	@echo "🐍 PySpark Shell Setup:"
	@echo ""
	@echo "Due to Bitnami Spark ivy configuration, use manual setup:"
	@echo "1. Run: make spark-bash"
	@echo "2. Inside container run: python3"
	@echo "3. Setup PySpark:"
	@echo "   from pyspark.sql import SparkSession"
	@echo "   spark = SparkSession.builder.appName('Interactive').master('local[*]').getOrCreate()"
	@echo "   spark.range(5).show()  # Test"
	@echo ""
	@make spark-bash

spark-shell: pyspark