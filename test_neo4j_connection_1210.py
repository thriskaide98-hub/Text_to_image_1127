from neo4j import GraphDatabase

URI = "neo4j+s://4a80fd07.databases.neo4j.io"
AUTH = ("neo4j", "9NFpy2I1fyMBJkPlZm1RHiXJrZvGdGEE7i9qlYinwjA")

print("🔹 드라이버 생성 중...")

driver = GraphDatabase.driver(URI, auth=AUTH)

print("🔹 네트워크 연결 확인 중...")

driver.verify_connectivity()

print("✅ Neo4j 연결 성공!")

driver.close()

