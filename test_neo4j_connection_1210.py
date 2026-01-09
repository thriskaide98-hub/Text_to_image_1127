from neo4j import GraphDatabase

URI = "neo4j+s://f6402eb8.databases.neo4j.io"
AUTH = ("neo4j", "AZoxdeEQgaHZZYtjc8sWsTu8TK_ou7gvgE55RoTIx18")

print("🔹 드라이버 생성 중...")

driver = GraphDatabase.driver(URI, auth=AUTH)

print("🔹 네트워크 연결 확인 중...")

driver.verify_connectivity()

print("✅ Neo4j 연결 성공!")

driver.close()
