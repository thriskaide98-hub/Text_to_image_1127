"""
plan_from_parcels_llm.py

- result/parcels/{id}_parcels.json 을 읽어
- gpt-4.1-mini 에게 각 parcel의 land_use 를 할당하게 하고
- result/plans/{id}_landuse.json 으로 저장
"""

from pathlib import Path
import json

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parent
PARCELS_DIR = ROOT_DIR / "result" / "1.parcels"
OUT_DIR     = ROOT_DIR / "result" / "2.plans"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "gpt-4.1-mini"
client = OpenAI()


def assign_land_use_for_id(id_str: str):
    parcels_path = PARCELS_DIR / f"{id_str}_parcels.json"
    if not parcels_path.exists():
        raise FileNotFoundError(parcels_path)

    with open(parcels_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    site = data["site"]
    parcels = data["parcels"]

    prompt = f"""
You are an urban planner AI.

You are given a site and a list of land parcels. 
Each parcel has:
- id
- area_px: approximate size in pixels (relative size)
- centroid_norm: [x, y] in 0–1 range (x: left-to-right, y: bottom-to-top)
- polygon: coordinates in meters (0–1000 range in both x and y)

Assign one land_use category to each parcel, using only:
- "Residential"
- "Commercial"
- "Public"
- "Green"

Heuristic rules (not strict, but preferred):
- Larger parcels near the center or along major roads: more likely "Commercial".
- Parcels near the outer boundary or river/park edges: "Residential" or "Green".
- Some medium-sized parcels near intersections can be "Public" (schools, civic).
- Ensure there is a reasonable mix: mostly Residential, fewer Commercial, some Public, some Green.

Return ONLY valid JSON with the same structure, but each parcel object must have an extra key "land_use".
Do not include explanations or comments.
Here is the data:
{json.dumps(data, ensure_ascii=False)}
"""

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )

    content = resp.choices[0].message.content.strip()
    # 혹시 코드펜스로 감싸면 제거
    if content.startswith("```"):
        content = content.strip("`")
        lines = content.splitlines()
        if lines and lines[0].lower().startswith("json"):
            lines = lines[1:]
        content = "\n".join(lines)

    plan = json.loads(content)

    out_path = OUT_DIR / f"{id_str}_landuse.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved land-use JSON: {out_path}")


def main():
    ids = sorted(p.stem.replace("_parcels", "") for p in PARCELS_DIR.glob("*_parcels.json"))
    for id_str in ids:
        assign_land_use_for_id(id_str)


if __name__ == "__main__":
    main()
