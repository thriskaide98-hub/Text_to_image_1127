"""
render_landuse_from_json.py

- result/plans/{id}_landuse.json 을 읽어
- 토지이용 색상으로 parcel polygon 렌더링
- 같은 id의 도로/마스크 이미지를 이용해 road polygon도 생성하여 검정/회색으로 표시
- result/landuse_flat/{id}_landuse_flat_with_roads.png 저장
"""

from pathlib import Path
import json

import numpy as np
import cv2
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image

ROOT_DIR   = Path(__file__).resolve().parent
PLANS_DIR  = ROOT_DIR / "result" / "2.1plans"
OUT_DIR    = ROOT_DIR / "result" / "3.1landuse_flat"
ROADS_DIR  = ROOT_DIR / "input" / "roads"
MASKS_DIR  = ROOT_DIR / "input" / "masks"

OUT_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    "Residential": "#fff59d",  # 연노랑
    "Commercial":  "#ef5350",  # 빨강
    "Public":      "#42a5f5",  # 파랑
    "Green":       "#66bb6a",  # 초록
}

SITE_WIDTH  = 1000.0
SITE_HEIGHT = 1000.0
TARGET_SIZE = (1024, 1024)  # roads_to_parcels 와 동일하게 사용


def _extract_road_polygons(id_str: str):
    """
    roads_to_parcels.py 에서 사용했던 로직을 그대로 써서
    '도로 영역'을 바이너리 마스크로 만들고,
    그걸 contour → polygon 으로 변환.
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

    
    # ------------------------------------------------------
    # 1) 렌더링용 확장 마스크 생성 (외곽 도로 살리기)
    # ------------------------------------------------------
    kernel_expand = np.ones((30, 30), np.uint8)
    mask_expanded = cv2.dilate((mask_np >= 128).astype(np.uint8), kernel_expand, iterations=1)

    # ------------------------------------------------------
    # 2) 도로 바이너리 생성 (어두운 픽셀 = 도로)
    # ------------------------------------------------------
    road_binary = cond_gray < 220   # threshold는 필요시 조정 가능

    # mask_expanded 밖은 도로에서 제외
    road_binary[mask_expanded == 0] = False

    # ------------------------------------------------------
    # 3) 도로 두껍게 만들기 (도로 폭 안정화)
    # ------------------------------------------------------
    kernel = np.ones((3, 3), np.uint8)
    road_dilated = cv2.dilate(road_binary.astype(np.uint8), kernel, iterations=4)

    # ------------------------------------------------------
    # 4) 확장된 마스크 내부에 남아있는 도로만 유지
    # ------------------------------------------------------
    road_inside = ((mask_expanded == 1) & (road_dilated == 1)).astype(np.uint8) * 255

    # ------------------------------------------------------
    # 5) 도로 contour → polygon 변환
    # ------------------------------------------------------
    contours, _ = cv2.findContours(
        road_inside,
        mode=cv2.RETR_EXTERNAL,
        method=cv2.CHAIN_APPROX_SIMPLE,
    )

    road_polys = []
    MIN_ROAD_AREA = 500  # 너무 작은 조각은 무시

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


def render_for_id(id_str: str):
    plan_path = PLANS_DIR / f"{id_str}_landuse.json"
    if not plan_path.exists():
        raise FileNotFoundError(plan_path)

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    site    = data["site"]
    parcels = data["parcels"]

    w = site.get("width_m", SITE_WIDTH)
    h = site.get("height_m", SITE_HEIGHT)

    fig, ax = plt.subplots(figsize=(6, 6))

    # 1) 도로 polygon 먼저 그리기 (회색 면 + 테두리 약간)
    road_polys = _extract_road_polygons(id_str)
    for poly in road_polys:
        patch_road = Polygon(
            poly,
            closed=True,
            facecolor="#dddddd",   # 도로 면 색 (밝은 회색)
            edgecolor="black",     # 도로 경계선
            linewidth=0.4,
            zorder=1,
        )
        ax.add_patch(patch_road)

    # 2) 그 위에 parcel polygon을 land-use 색으로 렌더링
    for p in parcels:
        land = p.get("land_use", "Residential")
        color = COLORS.get(land, "#eeeeee")
        poly  = p["polygon"]
        poly_xy = [(x, y) for x, y in poly]

        patch = Polygon(
            poly_xy,
            closed=True,
            facecolor=color,
            edgecolor="black",
            linewidth=0.3,
            zorder=2,   # 도로보다 위
        )
        ax.add_patch(patch)

    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    plt.axis("off")

    out_path = OUT_DIR / f"{id_str}_landuse_flat_with_roads.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved flat land-use PNG with roads: {out_path}")


def main():
    ids = sorted(p.stem.replace("_landuse", "") for p in PLANS_DIR.glob("*_landuse.json"))
    for id_str in ids:
        print(f"\n=== Rendering {id_str} ===")
        render_for_id(id_str)


if __name__ == "__main__":
    main()
