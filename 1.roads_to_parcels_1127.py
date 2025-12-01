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
OUT_DIR   = ROOT_DIR / "result" / "1.parcels"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def extract_parcels(id_str: str, target_size=(1024, 1024)):
    cond_path = ROADS_DIR / f"{id_str}_condition.png"
    mask_path = MASKS_DIR / f"{id_str}_mask.png"
    if not cond_path.exists() or not mask_path.exists():
        raise FileNotFoundError("missing cond/mask")

    # 해상도 통일
    cond = Image.open(cond_path).convert("RGB").resize(target_size)
    mask = Image.open(mask_path).convert("L").resize(target_size)

    cond_gray = np.array(cond.convert("L"))
    mask_np   = np.array(mask)

    h, w = cond_gray.shape

    # --------------------------------------------------
    # 1) 도로 바이너리 마스크 만들기
    #    - cond_gray가 어두운 부분 = 도로라고 가정
    # --------------------------------------------------
    # 값은 데이터 보고 200~240 사이로 조절해봐
    road_binary = cond_gray < 220        # True = road
    # 대상지 바깥은 전부 road 취급 (잘라내기)
    road_binary[mask_np < 128] = True

    # 도로를 살짝 두껍게 → 필지 사이 간격 확보
    kernel = np.ones((3, 3), np.uint8)
    road_dilated = cv2.dilate(road_binary.astype(np.uint8), kernel, iterations=2)

    # --------------------------------------------------
    # 2) 필지 후보 = 대상지 내부 & 도로가 아닌 부분
    # --------------------------------------------------
    parcel_mask = (mask_np >= 128) & (road_dilated == 0)

    # 도로 폭을 조금 더 확보하고 싶으면 필지 쪽을 한 번 더 erode
    parcel_mask = cv2.erode(parcel_mask.astype(np.uint8), kernel, iterations=1)

    # --------------------------------------------------
    # 3) Connected Components → 서로 안 겹치는 라벨들
    # --------------------------------------------------
    num_labels, labels = cv2.connectedComponents(parcel_mask.astype(np.uint8))
    print(f"[{id_str}] found raw parcels:", num_labels - 1)

    parcels = []
    site_width = 1000.0
    site_height = 1000.0

    MIN_PX = 1500   # 너무 작은 노이즈 제거 (필지 최소 면적 픽셀)
    for label_id in range(1, num_labels):  # 0 = 배경
        label_mask = (labels == label_id).astype(np.uint8)
        area_px = int(label_mask.sum())
        if area_px < MIN_PX:
            continue

        ys, xs = np.where(label_mask == 1)

        # --- (A) 경계에 붙은(테두리와 접한) 라벨은 외곽이라 버리기 ---
        if xs.min() == 0 or ys.min() == 0 or xs.max() == w - 1 or ys.max() == h - 1:
            continue

        # --------------------------------------------------
        # 4) 이 라벨에 대한 contour → approxPolyDP
        #    ※ 여기서는 convexHull 안 씀! (겹침의 주범이었음)
        # --------------------------------------------------
        # 255/0 바이너리 이미지로 변환
        contour_img = (label_mask * 255).astype(np.uint8)

        contours, _ = cv2.findContours(
            contour_img,
            mode=cv2.RETR_EXTERNAL,       # 가장 바깥 외곽만
            method=cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            continue

        # 여러 contour가 있어도 가장 큰 것만 사용
        contour = max(contours, key=cv2.contourArea)

        # 너무 요철이 심하면 epsilon 조금 키우고, 너무 각지면 줄여보기
        epsilon = 2.0
        approx = cv2.approxPolyDP(contour, epsilon=epsilon, closed=True)
        approx = approx.reshape(-1, 2)

        # centroid (정규화, 0~1)
        cx = xs.mean() / w
        cy = 1.0 - (ys.mean() / h)

        # 픽셀 → 사이트 좌표 (0~1000m 가정)
        poly = [
            [
                float(x / w * site_width),
                float((h - y) / h * site_height),
            ]
            for (x, y) in approx
        ]

        parcels.append(
            {
                "id": f"P{label_id:03d}",
                "area_px": float(area_px),
                "centroid_norm": [float(cx), float(cy)],
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
    print(f"   → final parcels count: {len(parcels)}")



def main():
    ids = sorted(p.stem.replace("_condition", "") for p in ROADS_DIR.glob("*_condition.png"))
    for id_str in ids:
        extract_parcels(id_str)


if __name__ == "__main__":
    main()
