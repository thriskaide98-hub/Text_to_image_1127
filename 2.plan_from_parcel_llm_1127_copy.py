"""
plan_from_parcels_llm_v2.py

- result/parcels/{id}_parcels.json 을 읽어
- 각 parcel의 요약정보(크기, 위치, area_rank 등)만 LLM에 전달
- LLM은 id별 land_use만 결정해서 반환
- 원본 parcel 데이터에 land_use를 merge하여
  result/plans/{id}_landuse.json 으로 저장
"""

from pathlib import Path
import json
import numpy as np

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent
PARCELS_DIR = ROOT_DIR / "result" / "1.parcels"
OUT_DIR     = ROOT_DIR / "result" / "2.1plans"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gpt-4.1-mini"
client = OpenAI()

# -----------------------------
# 1. 전역 설정: 목표 land-use 비율
# -----------------------------
TARGET_SHARE = {
    "Residential": 0.6,
    "Commercial":  0.2,
    "Public":      0.1,
    "Green":       0.1,
}

VALID_USES = list(TARGET_SHARE.keys())


def _make_parcel_summary(parcels):
    """
    polygon은 LLM에 보내지 않고,
    필지 요약 정보만 만들어서 반환.
    """
    areas = np.array([p["area_px"] for p in parcels], dtype=float)
    n = len(parcels)

    # area 기반 quantile로 크기 등급 나누기
    if n >= 5:
        q_small  = float(np.quantile(areas, 0.2))
        q_large  = float(np.quantile(areas, 0.8))
    else:
        # 필지 개수가 너무 적으면 그냥 median 기준으로
        q_small = float(np.min(areas))
        q_large = float(np.max(areas))

    summaries = []
    for p in parcels:
        area = float(p["area_px"])
        cx, cy = p["centroid_norm"]

        if area <= q_small:
            area_rank = "small"
        elif area >= q_large:
            area_rank = "large"
        else:
            area_rank = "medium"

        # 위치 태깅 (rough)
        hor = "left" if cx < 0.33 else ("right" if cx > 0.66 else "center")
        ver = "bottom" if cy < 0.33 else ("top" if cy > 0.66 else "middle")
        pos_tag = f"{hor}_{ver}"

        summaries.append(
            {
                "id": p["id"],
                "area_px": area,
                "area_rank": area_rank,
                "centroid": [cx, cy],
                "position_tag": pos_tag,
            }
        )

    return summaries


def assign_land_use_for_id(id_str: str):
    parcels_path = PARCELS_DIR / f"{id_str}_parcels.json"
    if not parcels_path.exists():
        raise FileNotFoundError(parcels_path)

    with open(parcels_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    site = data["site"]
    parcels = data["parcels"]

    if not parcels:
        print(f"[{id_str}] no parcels, skip.")
        return

    parcel_summaries = _make_parcel_summary(parcels)

    # 전체 면적 합 (비율 계산 참고용)
    total_area = float(sum(p["area_px"] for p in parcels))

    prompt_data = {
        "site": site,
        "target_share": TARGET_SHARE,
        "total_area_px": total_area,
        "parcels": parcel_summaries,
    }

    prompt = f"""
You are an expert urban planner AI.

You are given:
- A site description and the total sum of parcel areas (in pixels).
- A list of parcels with:
  - id
  - area_px (relative size)
  - area_rank: one of "small", "medium", "large"
  - centroid: [x, y] in 0–1 (x: left→right, y: bottom→top)
  - position_tag: a coarse location label such as "center_top", "left_middle", etc.

You must assign EXACTLY ONE land_use category to each parcel.
Allowed land_use values are ONLY:
{VALID_USES}

Target overall land-use share (by area, NOT by parcel count) is:
{json.dumps(TARGET_SHARE)}

Guiding heuristics:
- Large parcels near the center or along major corridors:
  - Prefer "Commercial" or sometimes "Public".
- Outer-edge parcels (position_tag including "left_bottom", "right_top", etc.):
  - Prefer "Residential" or "Green".
- Some medium parcels near the center-middle or key intersections:
  - Assign as "Public" (schools, civic facilities, etc.).
- Ensure the total area for each land_use is roughly close to the target_share.
  Exact matching is not required, but avoid extreme imbalance.

Return ONLY a valid JSON object of the form:

{{
  "parcels": [
    {{ "id": "P001", "land_use": "Residential" }},
    {{ "id": "P002", "land_use": "Commercial" }},
    ...
  ]
}}

- Use each parcel id exactly once.
- Do NOT include any comments, explanations, or extra keys.
Here is the input data:
{json.dumps(prompt_data, ensure_ascii=False)}
"""

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    content = resp.choices[0].message.content.strip()

    # ```json ... ``` 감싸져 있으면 제거
    if content.startswith("```"):
        content = content.strip("`")
        lines = content.splitlines()
        if lines and lines[0].lower().startswith("json"):
            lines = lines[1:]
        content = "\n".join(lines)

    result = json.loads(content)

    # id → land_use 매핑
    mapping = {p["id"]: p["land_use"] for p in result["parcels"]}

    # 원본 parcels에 land_use 병합
    for p in parcels:
        lu = mapping.get(p["id"], "Residential")  # 혹시 누락되면 기본 주거
        if lu not in VALID_USES:
            lu = "Residential"
        p["land_use"] = lu

    out_data = {
        "site": site,
        "parcels": parcels,
        "target_share": TARGET_SHARE,
    }

    out_path = OUT_DIR / f"{id_str}_landuse.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved land-use JSON (v2): {out_path}")


def main():
    ids = sorted(p.stem.replace("_parcels", "") for p in PARCELS_DIR.glob("*_parcels.json"))
    for id_str in ids:
        assign_land_use_for_id(id_str)


if __name__ == "__main__":
    main()
