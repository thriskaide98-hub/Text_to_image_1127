"""
main.py
- LLM(gpt-4.1-mini)을 사용하여 5x5 블록 개념 계획 생성
- PNG 시각화 + JSON 저장
- 결과물을 result/{모델명_년월일_시분}/ 폴더 안에 저장
- (추가) SD + ControlNet을 사용한 land-use 이미지(sd_landuse.png)도 생성
"""

import os
import json
from datetime import datetime
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
from openai import OpenAI

# 🔹 SD 파이프라인 모듈 불러오기
from sd_landuse_from_roads import (
    get_sd_pipe,
    generate_from_condition,
    PROMPT_BASE,
    NEGATIVE_PROMPT,
)

from PIL import Image, ImageDraw

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

    if content.startswith("```"):
        lines = content.strip("`").splitlines()
        if lines and lines[0].lower().startswith("json"):
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
# 4. matplotlib 시각화 함수
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
# 6. (추가) JSON 계획 → SD 조건 이미지 생성 함수
# =========================

def build_condition_image_from_plan(plan: dict, size: int = 768) -> Image.Image:
    """
    LLM이 만든 5x5 블록 JSON을 이용해 '도로 스케치' 이미지를 만든다.
    - 단순화: 블록 경계선을 모두 도로로 가정
    """
    w = h = size
    img = Image.new("RGB", (w, h), "white")
    draw = ImageDraw.Draw(img)

    site_w = plan["site"]["width_m"]
    site_h = plan["site"]["height_m"]
    sx = w / site_w
    sy = h / site_h

    blocks = plan["blocks"]

    # 블록 경계 좌표(격자선) 추출
    xs = set()
    ys = set()
    for b in blocks:
        x1, y1, x2, y2 = b["coords"]
        xs.add(x1)
        xs.add(x2)
        ys.add(y1)
        ys.add(y2)

    xs = sorted(xs)
    ys = sorted(ys)

    road_color = (0, 0, 0)
    road_width = 4

    # 수직선(도로)
    for x in xs:
        x_px = int(x * sx)
        draw.line([(x_px, 0), (x_px, h)], fill=road_color, width=road_width)

    # 수평선(도로)
    for y in ys:
        y_px = int(h - y * sy)  # y축 뒤집기(간단한 탑뷰 보정)
        draw.line([(0, y_px), (w, y_px)], fill=road_color, width=road_width)

    return img


# =========================
# 7. 메인 실행부
# =========================

def main():
    # 1) 결과 폴더 준비
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    folder_name = f"0.{MODEL_NAME}_{timestamp}"
    output_dir = Path("result/0.main") / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "plan.json"
    img_path = output_dir / "landuse.png"
    sd_img_path = output_dir / "sd_landuse.png"

    # 2) LLM 호출
    plan = call_llm_for_plan()

    print("✅ JSON parsed successfully!")
    print(f"Site: {plan['site']['width_m']} x {plan['site']['height_m']} m")
    print(f"Block count: {len(plan['blocks'])}")

    # 3) JSON 저장
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON saved: {json_path}")

    # 4) matplotlib landuse 이미지 저장
    plot_plan(plan, filename=str(img_path), title="AI Urban Concept Plan (5x5 Grid)")

    # 5) 간단 평가
    evaluate_plan(plan)

    # 6) (추가) JSON 기반 SD land-use 이미지 생성
    print("\n🔹 Building SD condition image from JSON plan...")
    cond_img = build_condition_image_from_plan(plan, size=768)
    mask_img = None  # 전체 영역을 사용 (원하면 마스크도 만들 수 있음)

    print("🔹 Loading SD + ControlNet pipeline...")
    pipe = get_sd_pipe()  # GPU 있으면 cuda로 자동

    generate_from_condition(
        pipe=pipe,
        cond_img=cond_img,
        mask_img=mask_img,
        out_path=sd_img_path,
        prompt=PROMPT_BASE,
        negative_prompt=NEGATIVE_PROMPT,
        seed=1234,
    )

    print("\n🎉 All results saved to:", output_dir)


if __name__ == "__main__":
    main()
