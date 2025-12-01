"""
3.0coloring.py
- result/1.parcels 폴더의 JSON 파일들을 읽어서
- 각 파셀에 색을 입혀서 PNG 이미지로 저장
- 결과물을 result/3.0coloring/ 폴더에 저장
"""

import os
import json
import glob
from matplotlib.patches import Polygon
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

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
# 색상 생성 함수
# =========================

def generate_colors(n_parcels: int) -> list:
    """파셀 개수에 따라 색상 리스트 생성"""
    # 부드러운 파스텔 톤 색상 팔레트
    base_colors = [
        '#FFB3B3',  # 연한 빨강
        '#B7FBC2',  # 연한 연두/초록
        '#FFFFCC',  # 연한 노랑
        '#FFDAB3',  # 연한 주황
        '#B3C6FF',  # 연한 파랑
        '#C7ECFF',  # 연한 하늘색
    ]
    
    # 파셀 개수만큼 색상 반복/혼합
    colors = []
    for i in range(n_parcels):
        # 색상을 순환하면서 약간의 변형 추가
        base_idx = i % len(base_colors)
        color = base_colors[base_idx]
        colors.append(color)
    
    return colors


# =========================
# 시각화 함수
# =========================

def plot_parcels(parcels_data: dict, filename: str) -> None:
    """파셀 데이터를 시각화하여 이미지로 저장"""
    site = parcels_data["site"]
    parcels = parcels_data["parcels"]
    
    width = site["width_m"]
    height = site["height_m"]
    n_parcels = len(parcels)
    
    # 색상 생성
    colors = generate_colors(n_parcels)
    
    # 그림 생성
    fig, ax = plt.subplots(figsize=(8, 8))
    
    # 각 파셀 그리기
    for i, parcel in enumerate(parcels):
        polygon_coords = parcel["polygon"]
        
        # 좌표를 numpy 배열로 변환
        coords = np.array(polygon_coords)
        
        # Polygon 패치 생성
        polygon = Polygon(
            coords,
            facecolor=colors[i],
            edgecolor='black',
            linewidth=0.5,
            alpha=0.7
        )
        ax.add_patch(polygon)
    
    # 축 설정
    ax.set_xlim(0, width)
    ax.set_ylim(0, height)
    ax.set_aspect("equal")
    ax.axis("off")
    
    # 이미지 저장
    plt.savefig(filename, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"✅ Image saved: {filename} ({n_parcels} parcels)")


# =========================
# 메인 실행부
# =========================

def main():
    # 입력/출력 폴더 설정
    input_dir = "result/1.parcels"
    output_dir = "result/3.0coloring"
    os.makedirs(output_dir, exist_ok=True)
    
    # JSON 파일 목록 가져오기
    json_files = sorted(glob.glob(os.path.join(input_dir, "*_parcels.json")))
    
    if not json_files:
        print(f"❌ {input_dir} 폴더에 JSON 파일이 없습니다.")
        return
    
    print(f"📁 Found {len(json_files)} JSON files")
    print()
    
    # 각 JSON 파일 처리
    for json_file in json_files:
        # 파일명에서 인덱스 추출
        basename = os.path.basename(json_file)
        file_idx = basename.replace("_parcels.json", "")
        
        print(f"🔹 Processing: {basename}")
        
        # JSON 파일 읽기
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                parcels_data = json.load(f)
        except Exception as e:
            print(f"❌ Error reading {json_file}: {e}")
            continue
        
        # 출력 파일 경로
        output_file = os.path.join(output_dir, f"{file_idx}_parcels_colored.png")
        
        # 시각화 및 저장
        plot_parcels(
            parcels_data,
            filename=output_file
        )
    
    print()
    print(f"🎉 All results saved to: {output_dir}")


if __name__ == "__main__":
    main()

