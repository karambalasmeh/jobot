import os
from google.cloud import aiplatform
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.getenv("GCP_PROJECT_ID")
LOCATION = os.getenv("GCP_LOCATION", "us-central1")

aiplatform.init(project=PROJECT_ID, location=LOCATION)

print("Starting Index Creation... (This takes about 30-45 minutes)")

# 1. إنشاء الـ Index مع تمرير إعدادات الخوارزمية يدوياً لتجاوز خطأ مكتبة جوجل
my_index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="jobot_rag_index",
    dimensions=768,
    approximate_neighbors_count=150,
    distance_measure_type="DOT_PRODUCT_DISTANCE",
    index_update_method="STREAM_UPDATE",
    leaf_node_embedding_count=500,     # <--- هذا السطر يحل المشكلة
    leaf_nodes_to_search_percent=7,    # <--- وهذا السطر يكمل الحل
)
print(f"Index created! ID: {my_index.name}")

print("Starting Endpoint Creation...")

# 2. إنشاء الـ Endpoint
my_index_endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="jobot_rag_endpoint",
    public_endpoint_enabled=True,
)
print(f"Endpoint created! ID: {my_index_endpoint.name}")

print("Deploying Index to Endpoint... (This also takes about 20-30 minutes)")

# 3. ربط الـ Index بالـ Endpoint
my_index_endpoint.deploy_index(
    index=my_index, deployed_index_id="jobot_deployed_index"
)
print("Deployment Complete!")
print("=========================================")
print(f"Please copy these to your .env file:")
print(f"VERTEX_INDEX_ID={my_index.name}")
print(f"VERTEX_ENDPOINT_ID={my_index_endpoint.name}")
print("=========================================")