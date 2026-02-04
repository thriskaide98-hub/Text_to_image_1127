# import_parcels_to_neo4j.py
#
# result/1.parcels/{id}_parcels.json 을 읽어서
# - Block 노드
# - Parcel 노드
# - Block-Parcel CONTAINS 관계
# - Parcel-Context HAS_CONTEXT 관계
# 를 생성한다.

from pathlib import Path
import json
import numpy as np
from neo4j import GraphDatabase

# ----------------------------
# 1) Neo4j 접속 설정  (test_neo4j_connection.py 와 동일하게)
# ----------------------------
URI = "neo4j+s://4a80fd07.databases.neo4j.io"  # <- 네 URI
USER = "neo4j"
PWD  = "9NFpy2I1fyMBJkPlZm1RHiXJrZvGdGEE7i9qlYinwjA"                      # <- 네 비번

driver = GraphDatabase.driver(URI, auth=(USER, PWD))

ROOT_DIR    = Path(__file__).resolve().parent
PARCELS_DIR = ROOT_DIR / "result" / "1.parcels"


# ----------------------------
# 2) area_rank, position_tag, pos_group 계산
# ----------------------------
def compute_area_rank_and_position(parcels):
    areas = np.array([p["area_px"] for p in parcels], dtype=float)
    n = len(parcels)

    if n >= 5:
        q_small = float(np.quantile(areas, 0.2))
        q_large = float(np.quantile(areas, 0.8))
    else:
        q_small = float(np.min(areas))
        q_large = float(np.max(areas))

    stats = {}
    for p in parcels:
        pid  = p["id"]
        area = float(p["area_px"])
        cx, cy = p["centroid_norm"]  # 0~1, x: left→right, y: bottom→top

        # area_rank
        if area <= q_small:
            area_rank = "small"
        elif area >= q_large:
            area_rank = "large"
        else:
            area_rank = "medium"

        # 위치 태그
        hor = "left" if cx < 0.33 else ("right" if cx > 0.66 else "center")
        ver = "bottom" if cy < 0.33 else ("top" if cy > 0.66 else "middle")
        position_tag = f"{hor}_{ver}"

        # pos_group (Context 와 매칭용)
        if "center" in position_tag and "middle" in position_tag:
            pos_group = "center"
        else:
            pos_group = "edge"

        stats[pid] = {
            "area_px": area,
            "area_rank": area_rank,
            "position_tag": position_tag,
            "pos_group": pos_group,
        }

    return stats


# ----------------------------
# 3) Neo4j 에 쓰는 Cypher
# ----------------------------
CREATE_QUERY = """
MERGE (b:Block {id: $site_id})
MERGE (p:Parcel {id: $site_id + "_" + $pid})   
SET  p.local_id = $pid,
     p.site_id  = $site_id,
     p.area_px      = $area_px,
     p.area_rank    = $area_rank,
     p.position_tag = $position_tag,
     p.pos_group    = $pos_group
MERGE (b)-[:CONTAINS]->(p)
WITH p
MATCH (c:Context {area_rank: $area_rank, pos_group: $pos_group})
MERGE (p)-[:HAS_CONTEXT]->(c)
"""

def import_one_site(tx, site_id: str, parcels: list):
    stats = compute_area_rank_and_position(parcels)
    for p in parcels:
        pid = p["id"]
        s = stats[pid]
        tx.run(
            CREATE_QUERY,
            site_id      = site_id,
            pid          = pid,
            area_px      = s["area_px"],
            area_rank    = s["area_rank"],
            position_tag = s["position_tag"],
            pos_group    = s["pos_group"],
        )


def main():
    json_files = sorted(PARCELS_DIR.glob("*_parcels.json"))
    if not json_files:
        print("❌ result/1.parcels 에 *_parcels.json 이 없습니다.")
        return

    with driver.session() as session:
        for path in json_files:
            site_id = path.stem.replace("_parcels", "")
            print(f"\n=== Importing parcels for site: {site_id} ===")

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            parcels = data.get("parcels", [])
            if not parcels:
                print("  → parcels 없음, 건너뜀")
                continue

            session.execute_write(import_one_site, site_id, parcels)
            print(f"  → imported {len(parcels)} parcels")

    driver.close()
    print("\n✅ Done.")


if __name__ == "__main__":
    main()
