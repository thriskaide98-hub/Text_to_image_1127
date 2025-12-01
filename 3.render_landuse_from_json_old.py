"""
render_landuse_from_json.py

- result/plans/{id}_landuse.json 을 읽어
- 토지이용 색상으로 polygon 렌더링
- result/landuse_flat/{id}_landuse_flat.png 저장
"""

from pathlib import Path
import json

import matplotlib.pyplot as plt
from matplotlib.patches import Polygon

ROOT_DIR = Path(__file__).resolve().parent
PLANS_DIR = ROOT_DIR / "result" / "plans"
OUT_DIR   = ROOT_DIR / "result" / "landuse_flat"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COLORS = {
    "Residential": "#fff59d",  # 연노랑
    "Commercial":  "#ef5350",  # 빨강
    "Public":      "#42a5f5",  # 파랑
    "Green":       "#66bb6a",  # 초록
}


def render_for_id(id_str: str):
    plan_path = PLANS_DIR / f"{id_str}_landuse.json"
    if not plan_path.exists():
        raise FileNotFoundError(plan_path)

    with open(plan_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    site = data["site"]
    parcels = data["parcels"]

    w = site["width_m"]
    h = site["height_m"]

    fig, ax = plt.subplots(figsize=(6, 6))

    for p in parcels:
        land = p.get("land_use", "Residential")
        color = COLORS.get(land, "#eeeeee")
        poly = p["polygon"]
        poly_xy = [(x, y) for x, y in poly]

        patch = Polygon(poly_xy, closed=True, facecolor=color, edgecolor="black", linewidth=0.3)
        ax.add_patch(patch)

    ax.set_xlim(0, w)
    ax.set_ylim(0, h)
    ax.set_aspect("equal")
    plt.axis("off")

    out_path = OUT_DIR / f"{id_str}_landuse_flat.png"
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"✅ Saved flat land-use PNG: {out_path}")


def main():
    ids = sorted(p.stem.replace("_landuse", "") for p in PLANS_DIR.glob("*_landuse.json"))
    for id_str in ids:
        render_for_id(id_str)


if __name__ == "__main__":
    main()
