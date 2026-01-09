"""
5.render_landuse_from_kg_1210.py

- result/1.parcels/{id}_parcels.json 에서
  - site 정보(width/height)와 각 parcel의 polygon 좌표를 읽고
- Neo4j에서 해당 site의 Parcel 노드 land_use_kg 값을 조회하여
  - id 매칭 후 land_use_kg 기반으로 색을 칠해 PNG로 렌더링

출력:
- result/3.2landuse_kg_flat/{id}_landuse_kg_with_roads.png
"""

from pathlib import Path
import os
import json

import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from neo4j import GraphDatabase

# -----------------------------
# 경로 설정
# -----------------------------
ROOT_DIR = Path(__file__).resolve().parent

PARCELS_DIR = ROOT_DIR / "result" / "1.parcels"
OUT_DIR     = ROOT_DIR / "result" / "3.2landuse_kg_flat_2"
ROADS_DIR   = ROOT_DIR / "input" / "roads"
MASKS_DIR   = ROOT_DIR / "input" / "masks"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# roads_to_parcels / render_landuse_from_json 과 동일
SITE_WIDTH  = 1000.0
SITE_HEIGHT = 1000.0
TARGET_SIZE = (1024, 1024)

# land_use 색상
COLORS = {
    "Residential": "#fff59d",  # 연노랑
    "Commercial":  "#ef5350",  # 빨강
    "Public":      "#42a5f5",  # 파랑
    "Green":       "#66bb6a",  # 초록
}

# -----------------------------
# Neo4j 드라이버
# -----------------------------
def get_driver():
    uri  = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd  = os.getenv("NEO4J_PASSWORD")

    if not uri or not user or not pwd:
        raise RuntimeError("NEO4J_URI / NEO4J_USER / NEO4J_PASSWORD 환경변수가 설정되어야 합니다.")

    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    return driver


def _fetch_landuse_kg(tx, site_id: str):
    """
    주어진 site_id(예: '004')에 대해
    Block-{id:site_id}가 CONTAINS 하는 Parcel들의 land_use_kg를 가져옴.
    """
    query = """
    MATCH (b:Block {id: $site_id})-[:CONTAINS]->(p:Parcel)
    RETURN p.id AS pid, p.land_use_kg AS land_use_kg
    """
    result = tx.run(query, site_id=site_id)
    mapping = {}
    for row in result:
        mapping[row["pid"]] = row["land_use_kg"]
    return mapping


# -----------------------------
# 도로 polygon 추출 (기존 스크립트에서 복사)
# -----------------------------
def _extract_road_polygons(id_str: str):
    """
    roads_to_parcels.py / render_landuse_from_json.py 와 동일한 로직으로
    도로 영역을 contour → polygon 으로 변환
    """
    cond_path = ROADS_DIR / f"{id_str}_condition.png"
    mask_path = MASKS_DIR / f"{id_str}_mask.png"
    if not cond_path.exists() or not mask_path.exists():
        print(f"⚠ road/mask not found for {id_str}, skip road drawing.")
        return []

    cond = Image.open(cond_path).convert("RGB").resize(TARGET_SIZE)
    mask = Image.open(mask_path).convert("L").resize(TARGET_SIZE)

    cond_gray = np.array(cond.convert("L"))
    mask_np   = np.array(mask)

    h, w = cond_gray.shape

    # 1) 확장된 마스크 (외곽 도로 살리기)
    kernel_expand = np.ones((30, 30), np.uint8)
    mask_expanded = cv2.dilate((mask_np >= 128).astype(np.uint8),
                               kernel_expand, iterations=1)

    # 2) 어두운 픽셀 = 도로 후보
    road_binary = cond_gray < 220
    # 대상지 확장 마스크 밖은 제외
    road_binary[mask_expanded == 0] = False

    # 3) 도로 두껍게
    kernel = np.ones((3, 3), np.uint8)
    road_dilated = cv2.dilate(road_binary.astype(np.uint8),
                              kernel, iterations=4)

    # 4) 확장 마스크 내부 도로만 유지
    road_inside = ((mask_expanded == 1) & (road_dilated == 1)).astype(np.uint8) * 255

    # 5) contour → polygon
    contours, _ = cv2.findContours(
        road_inside,
        mode=cv2.RETR_EXTERNAL,
        method=cv2.CHAIN_APPROX_SIMPLE,
    )

    road_polys = []
    MIN_ROAD_AREA = 500

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_ROAD_AREA:
            continue

        epsilon = 2.0
        approx = cv2.approxPolyDP(cnt, epsilon=epsilon, closed=True)
        approx = approx.reshape(-1, 2)

        poly_xy = [
            [
                float(x / w * SITE_WIDTH),
                float((h - y) / h * SITE_HEIGHT),
            ]
            for (x, y) in approx
        ]
        road_polys.append(poly_xy)

    print(f"   → road polygons: {len(road_polys)}")
    return road_polys


# -----------------------------
# 한 사이트 렌더링
# -----------------------------
def render_site(driver, site_id: str):
    """
    site_id 예: '000', '004' …
    1) parcels JSON 읽기
    2) Neo4j에서 land_use_kg 가져오기
    3) 도로 + 필지 렌더링
    """
    parcels_path = PARCELS_DIR / f"{site_id}_parcels.json"
    if not parcels_path.exists():
        print(f"⚠ parcels JSON not found for {site_id}, skip.")
        return

    with open(parcels_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    site    = data["site"]
    parcels = data["parcels"]

    width  = site.get("width_m", SITE_WIDTH)
    height = site.get("height_m", SITE_HEIGHT)

    # Neo4j에서 land_use_kg 매핑 조회
    with driver.session(database="neo4j") as session:
        lu_map = session.execute_read(_fetch_landuse_kg, site_id)

    print(f"\n=== Rendering site {site_id} ===")
    print(f"   parcels in JSON : {len(parcels)}")
    print(f"   parcels in Neo4j: {len(lu_map)}")

    fig, ax = plt.subplots(figsize=(6, 6))

    # 1) 도로 먼저
    road_polys = _extract_road_polygons(site_id)
    for poly in road_polys:
        patch_road = Polygon(
            poly,
            closed=True,
            facecolor="#dddddd",
            edgecolor="black",
            linewidth=0.4,
            zorder=1,
        )
        ax.add_patch(patch_road)

    # 2) parcel polygon을 land_use_kg 색으로
    for p in parcels:
        pid = p["id"]
        land = lu_map.get(pid)

        # land_use_kg가 없으면 일단 Residential로 기본 처리
        if land is None:
            land = "Residential"

        color = COLORS.get(land, "#eeeeee")
        poly = p["polygon"]

        patch = Polygon(
            [(x, y) for x, y in poly],
            closed=True,
            facecolor=color,
            edgecolor="black",
            linewidth=0.3,
            zorder=2,
        )
        ax.add_patch(patch)

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    plt.axis("off")

    out_path = OUT_DIR / f"{site_id}_landuse_kg_with_roads.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Saved KG-based land-use PNG: {out_path}")


def main():
    driver = get_driver()

    # result/1.parcels 안에 있는 모든 id 순회
    ids = sorted(p.stem.replace("_parcels", "") for p in PARCELS_DIR.glob("*_parcels.json"))

    for site_id in ids:
        render_site(driver, site_id)

    driver.close()


if __name__ == "__main__":
    main()
