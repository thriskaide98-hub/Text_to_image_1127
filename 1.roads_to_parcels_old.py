"""
roads_to_parcels.py

- input/roads/{id}_condition.png, input/masks/{id}_mask.png
- 도로를 기준으로 빈 공간(대지)을 찾고 parcel polygon 추출
- result/parcels/{id}_parcels.json 으로 저장
"""

from pathlib import Path
import json

import numpy as np
import cv2
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent
ROADS_DIR = ROOT_DIR / "input" / "roads"
MASKS_DIR = ROOT_DIR / "input" / "masks"
OUT_DIR   = ROOT_DIR / "result" / "parcels"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_parcels(id_str: str, target_size=(512, 512)):
    cond_path = ROADS_DIR / f"{id_str}_condition.png"
    mask_path = MASKS_DIR / f"{id_str}_mask.png"
    if not cond_path.exists() or not mask_path.exists():
        raise FileNotFoundError("missing cond/mask")

    cond = Image.open(cond_path).convert("RGB").resize(target_size)
    mask = Image.open(mask_path).convert("L").resize(target_size)

    cond_gray = np.array(cond.convert("L"))
    mask_np   = np.array(mask)

    # 1) 도로 추출 (밝은 도로/어두운 배경 상황에 따라 threshold 조절 필요)
    #   여기서는 "도로가 밝은 회색"이라고 가정 -> 도로 = 어두운 선이면 반대로 사용
    road_binary = cond_gray < 230  # True = road

    # 2) 대상지 밖은 전부 road로 취급해서 parcel에서 제외
    road_binary[mask_np < 128] = True

    # 3) road mask를 조금 두껍게 (폭 넓혀서 parcel 완전히 분리되도록)
    kernel = np.ones((3, 3), np.uint8)
    road_dilated = cv2.dilate(road_binary.astype(np.uint8), kernel, iterations=2)

    # 4) parcel 영역 = 대상지 내부 & road 아닌 부분
    parcel_mask = (mask_np >= 128) & (road_dilated == 0)

    # 5) connected components 로 parcel label 부여
    num_labels, labels = cv2.connectedComponents(parcel_mask.astype(np.uint8))
    print(f"[{id_str}] found parcels:", num_labels - 1)

    parcels = []
    h, w = labels.shape
    site_width = 1000.0
    site_height = 1000.0

    for label_id in range(1, num_labels):  # 0은 배경
        ys, xs = np.where(labels == label_id)
        if len(xs) < 50:  # 너무 작은 건 noise로 제외
            continue

        area_px = float(len(xs))
        # 중점 (0~1 정규화)
        cx = float(xs.mean() / w)
        cy = float(1.0 - ys.mean() / h)  # 위가 1.0이 되도록 뒤집기

        # 간단 polygon: convex hull
        pts = np.stack([xs, ys], axis=1).astype(np.int32)
        hull = cv2.convexHull(pts)
        hull = hull.squeeze(1)
        # 좌표를 0~1000 범위로 스케일
        poly = [
            [
                float(x / w * site_width),
                float((h - y) / h * site_height),
            ]
            for (x, y) in hull
        ]

        parcels.append(
            {
                "id": f"P{label_id:03d}",
                "area_px": area_px,
                "centroid_norm": [cx, cy],
                "polygon": poly,
            }
        )

    result = {
        "site": {"width_m": site_width, "height_m": site_height},
        "parcels": parcels,
    }

    out_path = OUT_DIR / f"{id_str}_parcels.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved parcels JSON: {out_path}")


def main():
    ids = sorted(p.stem.replace("_condition", "") for p in ROADS_DIR.glob("*_condition.png"))
    for id_str in ids:
        extract_parcels(id_str)


if __name__ == "__main__":
    main()
