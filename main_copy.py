"""
main.py
- LLM(gpt-4.1-mini)을 사용하여 6x6 블록 개념 계획 생성
- PNG 시각화 + JSON 저장
- 결과물을 result/0.main/{모델명_년월일_시분}/ 폴더 안에 저장
"""

import os
import json
from datetime import datetime
from collections import Counter

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from openai import OpenAI

# 한글 폰트 설정
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 한글 폰트를 사용할 수 있는 경우 설정 (시스템에 따라 다름)
try:
    # Linux에서 한글 폰트 찾기
    font_list = [f.name for f in fm.fontManager.ttflist]
    korean_fonts = ['NanumGothic', 'NanumBarunGothic', 'Noto Sans CJK KR', 'Malgun Gothic', 'Nanum Gothic']
    for font_name in korean_fonts:
        if font_name in font_list:
            plt.rcParams['font.family'] = font_name
            print(f"✅ 한글 폰트 설정: {font_name}")
            break
    else:
        # 폰트 경로로 직접 찾기
        font_paths = [
            '/usr/share/fonts/truetype/nanum/NanumGothic.ttf',
            '/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf',
            '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        ]
        for font_path in font_paths:
            if os.path.exists(font_path):
                font_prop = fm.FontProperties(fname=font_path)
                plt.rcParams['font.family'] = font_prop.get_name()
                print(f"✅ 한글 폰트 설정 (경로): {font_path}")
                break
except Exception as e:
    print(f"⚠️ 한글 폰트 설정 실패: {e}")
    print("   기본 폰트를 사용합니다. 한글이 깨질 수 있습니다.")


# =========================
# 1. OpenAI 클라이언트 설정
# =========================

MODEL_NAME = "gpt-4.1"
client = OpenAI()


# =========================
# 2. LLM 프롬프트 정의
# =========================

PROMPT = """
You are an urban planner AI assistant.

Generate a simple 6x6 block concept plan for a 1000x1000 meter rectangular site.
Return ONLY valid JSON with this exact structure:

{
  "site": {"width_m": 1000, "height_m": 1000},
  "blocks": [
    {"id": "B00", "coords": [0, 833.33, 166.67, 1000], "land_use": "Residential"},
    ...
  ]
}

Rules:
- Divide the site into exactly 36 blocks arranged in a 6x6 grid.
- The site origin (0,0) is at the bottom-left corner.
- The full site extends to (1000, 1000).
- Each block must be exactly 166.67 x 166.67 meters (1000/6).
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
    "Residential": "#d9ffb3",
    "Commercial": "#ff9999",
    "Public": "#66b3ff",
    "Green": "#99ff99",
}

def plot_plan(plan: dict, filename: str, title: str) -> None:
    width = plan["site"]["width_m"]
    height = plan["site"]["height_m"]
    blocks = plan["blocks"]

    # 범례를 위한 공간을 확보하기 위해 figsize 조정
    fig = plt.figure(figsize=(8, 7.5))
    gs = fig.add_gridspec(2, 1, height_ratios=[10, 1.2], hspace=0.2)
    ax = fig.add_subplot(gs[0])
    ax_legend = fig.add_subplot(gs[1])

    # 그리드 그리기
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
    ax.set_title(title, fontsize=12, pad=10)
    ax.axis("off")

    # 범례 생성
    ax_legend.axis("off")
    legend_elements = []
    labels_en = {
        "Residential": "Residential",
        "Commercial": "Commercial",
        "Public": "Public",
        "Green": "Green"
    }
    
    for land_use, color in COLORS.items():
        legend_elements.append(
            plt.Rectangle((0, 0), 1, 1, facecolor=color, edgecolor="black", linewidth=0.5)
        )
    
    # 범례를 2줄로 배치 (각 줄에 2개씩)
    legend_labels = [f"{lu[0]} = {labels_en.get(lu, lu)}" for lu in COLORS.keys()]
    ax_legend.legend(
        legend_elements,
        legend_labels,
        loc="center",
        ncol=2,  # 2열로 배치하여 2줄 생성
        frameon=False,
        fontsize=11,
        handlelength=1.5,
        handletextpad=0.5,
        columnspacing=1.5
    )

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
    plot_plan(plan, filename=img_path, title="AI Urban Concept Plan (6x6 Grid)")

    # 🔸 6) 평가 출력
    evaluate_plan(plan)

    print("\n🎉 All results saved to:", output_dir)


if __name__ == "__main__":
    main()
