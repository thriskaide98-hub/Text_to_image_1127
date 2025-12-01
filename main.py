"""
main.py
- LLM(gpt-4.1-mini)을 사용하여 5x5 블록 개념 계획 생성
- PNG 시각화 + JSON 저장
- 결과물을 result/0.main/{모델명_년월일_시분}/ 폴더 안에 저장
"""

import os
import json
from datetime import datetime
from collections import Counter

import matplotlib.pyplot as plt
from openai import OpenAI


# =========================
# 1. OpenAI 클라이언트 설정
# =========================

MODEL_NAME = "gpt-4.1-mini"
client = OpenAI()


# =========================
# 2. LLM 프롬프트 정의
# =========================

PROMPT = """
You are an urban planner AI assistant.

Generate a simple 5x5 block concept plan for a 1000x1000 meter rectangular site.
Return ONLY valid JSON with this exact structure:

{
  "site": {"width_m": 1000, "height_m": 1000},
  "blocks": [
    {"id": "B00", "coords": [0, 800, 200, 1000], "land_use": "Residential"},
    ...
  ]
}

Rules:
- Divide the site into exactly 25 blocks arranged in a 5x5 grid.
- The site origin (0,0) is at the bottom-left corner.
- The full site extends to (1000, 1000).
- Each block must be exactly 200 x 200 meters.
- Use only these land_use values: "Residential", "Commercial", "Public", "Green".
- Assign land uses in a realistic mixed-use pattern.
- Do NOT include any comments, explanations, markdown, or code fences.
- Respond with JSON only.
"""


# =========================
# 3. JSON 생성 함수
# =========================

def call_llm_for_plan() -> dict:
    print(f"🔹 Requesting AI-generated plan from OpenAI ({MODEL_NAME})...")

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": PROMPT}],
        temperature=0.2,
    )

    content = response.choices[0].message.content.strip()
    print("✅ Raw response (first 200 chars):")
    print(content[:200] + ("..." if len(content) > 200 else ""))
    print()

    # 코드펜스 제거
    if content.startswith("```"):
        lines = content.strip("`").splitlines()
        if lines[0].lower().startswith("json"):
            lines = lines[1:]
        content = "\n".join(lines)

    try:
        plan = json.loads(content)
    except json.JSONDecodeError as e:
        print("❌ JSON 파싱 실패:", e)
        print("\n응답 전체:\n", content)
        raise

    return plan


# =========================
# 4. 시각화 함수
# =========================

COLORS = {
    "Residential": "#ff9999",
    "Commercial": "#66b3ff",
    "Public": "#99ff99",
    "Green": "#d9ffb3",
}

def plot_plan(plan: dict, filename: str, title: str) -> None:
    width = plan["site"]["width_m"]
    height = plan["site"]["height_m"]
    blocks = plan["blocks"]

    fig, ax = plt.subplots(figsize=(6, 6))

    for b in blocks:
        x1, y1, x2, y2 = b["coords"]
        land = b["land_use"]

        ax.add_patch(
            plt.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                facecolor=COLORS.get(land, "#dddddd"),
                edgecolor="black",
                linewidth=0.5,
            )
        )

        ax.text(
            (x1 + x2) / 2,
            (y1 + y2) / 2,
            land[0],
            ha="center",
            va="center",
            fontsize=7,
        )

    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    plt.title(title)
    plt.axis("off")
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"✅ Image saved: {filename}")


# =========================
# 5. 평가 함수
# =========================

def evaluate_plan(plan: dict) -> None:
    blocks = plan["blocks"]
    total = len(blocks)
    counts = Counter(b["land_use"] for b in blocks)

    print("\n📊 Basic Evaluation")
    print(f"- Total blocks: {total}")
    print("- Land-use distribution:")
    for lu, cnt in counts.items():
        print(f"  • {lu}: {cnt} blocks ({cnt / total * 100:.1f}%)")


# =========================
# 6. 메인 실행부
# =========================

def main():

    # 🔸 1) 시간 스탬프 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    # 🔸 2) 하위 폴더 경로 생성
    folder_name = f"{MODEL_NAME}_{timestamp}"
    output_dir = os.path.join("result/0.main&sd/main", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # 파일 경로들
    json_path = os.path.join(output_dir, "plan.json")
    img_path = os.path.join(output_dir, "landuse.png")

    # 🔸 3) LLM 호출
    plan = call_llm_for_plan()

    print("✅ JSON parsed successfully!")
    print(f"Site: {plan['site']['width_m']} x {plan['site']['height_m']} m")
    print(f"Block count: {len(plan['blocks'])}")

    # 🔸 4) JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON saved: {json_path}")

    # 🔸 5) landuse 이미지 저장
    plot_plan(plan, filename=img_path, title="AI Urban Concept Plan (5x5 Grid)")

    # 🔸 6) 평가 출력
    evaluate_plan(plan)

    print("\n🎉 All results saved to:", output_dir)


if __name__ == "__main__":
    main()
