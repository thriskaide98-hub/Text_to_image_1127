"""
6.create_grid_images_1210.py

- result/3.2landuse_kg_flat_2/ 폴더의 이미지들을
- 5x5 그리드(25개씩)로 묶어서 하나의 이미지로 생성
- result/3.3kg_grids/ 폴더에 저장

사용법:
  # 모든 이미지 처리
  python 6.create_grid_images_1210.py

  # 특정 ID 리스트 지정
  python 6.create_grid_images_1210.py --ids 000 001 002 004 005

  # 범위 지정
  python 6.create_grid_images_1210.py --range 000 025

  # 파일에서 ID 리스트 읽기
  python 6.create_grid_images_1210.py --file selected_ids.txt
"""

from pathlib import Path
from PIL import Image
import numpy as np
import argparse

ROOT_DIR = Path(__file__).resolve().parent
INPUT_DIR = ROOT_DIR / "result" / "3.2landuse_kg_flat_2"
OUTPUT_DIR = ROOT_DIR / "result" / "3.3kg_grids"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 그리드 설정
GRID_ROWS = 5
GRID_COLS = 5
IMAGES_PER_GRID = GRID_ROWS * GRID_COLS  # 25개

# 이미지 간 간격 (픽셀)
SPACING = 10

# 배경 색상 (흰색)
BACKGROUND_COLOR = (255, 255, 255)


def create_grid_image(image_paths, grid_index):
    """
    주어진 이미지 경로 리스트를 5x5 그리드로 합쳐서 하나의 이미지로 만듦
    
    Args:
        image_paths: 이미지 파일 경로 리스트 (최대 25개)
        grid_index: 그리드 인덱스 (파일명에 사용)
    
    Returns:
        PIL Image 객체
    """
    if not image_paths:
        return None
    
    # 첫 번째 이미지로 크기 확인
    first_img = Image.open(image_paths[0])
    img_width, img_height = first_img.size
    
    # 그리드 전체 크기 계산
    grid_width = GRID_COLS * img_width + (GRID_COLS - 1) * SPACING
    grid_height = GRID_ROWS * img_height + (GRID_ROWS - 1) * SPACING
    
    # 배경 이미지 생성
    grid_image = Image.new('RGB', (grid_width, grid_height), BACKGROUND_COLOR)
    
    # 각 이미지를 그리드에 배치
    for idx, img_path in enumerate(image_paths):
        if idx >= IMAGES_PER_GRID:
            break
        
        row = idx // GRID_COLS
        col = idx % GRID_COLS
        
        # 이미지 로드 및 크기 조정 (일관성 확보)
        try:
            img = Image.open(img_path)
            if img.size != (img_width, img_height):
                img = img.resize((img_width, img_height), Image.Resampling.LANCZOS)
            
            # RGB로 변환 (RGBA인 경우 처리)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 그리드 위치 계산
            x = col * (img_width + SPACING)
            y = row * (img_height + SPACING)
            
            # 이미지 붙이기
            grid_image.paste(img, (x, y))
        except Exception as e:
            print(f"⚠ Error loading {img_path.name}: {e}")
            continue
    
    return grid_image


def parse_arguments():
    """명령줄 인자 파싱"""
    parser = argparse.ArgumentParser(
        description="KG 기반 토지이용 이미지를 5x5 그리드로 묶기",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  # 모든 이미지 처리
  python 6.create_grid_images_1210.py

  # 특정 ID 리스트 지정
  python 6.create_grid_images_1210.py --ids 000 001 002 004 005

  # 범위 지정 (000부터 024까지)
  python 6.create_grid_images_1210.py --range 000 024

  # 파일에서 ID 리스트 읽기 (한 줄에 하나씩)
  python 6.create_grid_images_1210.py --file selected_ids.txt
        """
    )
    
    parser.add_argument(
        '--ids',
        nargs='+',
        help='처리할 이미지 ID 리스트 (예: --ids 000 001 002)'
    )
    
    parser.add_argument(
        '--range',
        nargs=2,
        metavar=('START', 'END'),
        help='처리할 이미지 ID 범위 (예: --range 000 024)'
    )
    
    parser.add_argument(
        '--file',
        type=str,
        help='ID 리스트가 담긴 파일 경로 (한 줄에 하나씩)'
    )
    
    return parser.parse_args()


def get_selected_image_ids(args):
    """
    명령줄 인자에 따라 선택된 이미지 ID 리스트 반환
    
    Returns:
        list: 선택된 이미지 ID 리스트 (문자열, 예: ['000', '001', '002'])
        None: 모든 이미지 사용
    """
    if args.ids:
        # 직접 ID 리스트 지정
        return [id_str.strip() for id_str in args.ids]
    
    elif args.range:
        # 범위 지정
        start_id = args.range[0].strip()
        end_id = args.range[1].strip()
        
        try:
            start_num = int(start_id)
            end_num = int(end_id)
            
            # 000 형식으로 포맷팅
            selected_ids = []
            for num in range(start_num, end_num + 1):
                selected_ids.append(f"{num:03d}")
            return selected_ids
        except ValueError:
            print(f"⚠ 범위는 숫자여야 합니다: {start_id}, {end_id}")
            return None
    
    elif args.file:
        # 파일에서 읽기
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ids = [line.strip() for line in f if line.strip()]
            return ids
        except Exception as e:
            print(f"❌ 파일 읽기 오류: {e}")
            return None
    
    else:
        # 인자가 없으면 None 반환 (모든 이미지 사용)
        return None


def filter_images_by_ids(image_files, selected_ids):
    """
    선택된 ID에 해당하는 이미지 파일만 필터링
    
    Args:
        image_files: 모든 이미지 파일 리스트
        selected_ids: 선택된 ID 리스트
    
    Returns:
        필터링된 이미지 파일 리스트
    """
    if selected_ids is None:
        return image_files
    
    # ID를 정규화 (앞뒤 공백 제거, 0 패딩)
    normalized_ids = set()
    for id_str in selected_ids:
        id_str = id_str.strip()
        # 숫자로 변환 가능하면 3자리로 포맷팅
        try:
            num = int(id_str)
            normalized_ids.add(f"{num:03d}")
        except ValueError:
            normalized_ids.add(id_str)
    
    filtered = []
    for img_file in image_files:
        # 파일명에서 ID 추출 (예: "000_landuse_kg_with_roads.png" -> "000")
        file_id = img_file.stem.replace("_landuse_kg_with_roads", "")
        
        # 정규화된 ID와 비교
        try:
            file_num = int(file_id)
            normalized_file_id = f"{file_num:03d}"
        except ValueError:
            normalized_file_id = file_id
        
        if normalized_file_id in normalized_ids:
            filtered.append(img_file)
    
    return sorted(filtered)


def main():
    # 명령줄 인자 파싱
    args = parse_arguments()
    
    # 선택된 이미지 ID 가져오기
    selected_ids = get_selected_image_ids(args)
    
    # 입력 폴더에서 모든 PNG 이미지 가져오기
    all_image_files = sorted(INPUT_DIR.glob("*_landuse_kg_with_roads.png"))
    
    if not all_image_files:
        print(f"❌ {INPUT_DIR}에 이미지 파일이 없습니다.")
        return
    
    # 선택된 ID에 따라 필터링
    if selected_ids:
        image_files = filter_images_by_ids(all_image_files, selected_ids)
        print(f"📋 선택된 이미지 ID: {', '.join(selected_ids[:10])}{'...' if len(selected_ids) > 10 else ''}")
        print(f"📁 총 {len(image_files)}개의 이미지 파일 선택됨 (전체 {len(all_image_files)}개 중)")
        
        if not image_files:
            print("❌ 선택된 ID에 해당하는 이미지 파일이 없습니다.")
            return
    else:
        image_files = all_image_files
        print(f"📁 총 {len(image_files)}개의 이미지 파일 발견 (모두 처리)")
    
    # 25개씩 묶어서 처리
    num_grids = (len(image_files) + IMAGES_PER_GRID - 1) // IMAGES_PER_GRID
    print(f"📊 {num_grids}개의 그리드 이미지 생성 예정 (각 {IMAGES_PER_GRID}개씩)")
    
    for grid_idx in range(num_grids):
        start_idx = grid_idx * IMAGES_PER_GRID
        end_idx = min(start_idx + IMAGES_PER_GRID, len(image_files))
        batch = image_files[start_idx:end_idx]
        
        print(f"\n=== Creating grid {grid_idx + 1}/{num_grids} ===")
        print(f"   Images: {start_idx + 1} ~ {end_idx} ({len(batch)}개)")
        
        # 그리드 이미지 생성
        grid_image = create_grid_image(batch, grid_idx)
        
        if grid_image:
            # 파일명 생성
            first_id = batch[0].stem.replace("_landuse_kg_with_roads", "")
            last_id = batch[-1].stem.replace("_landuse_kg_with_roads", "")
            output_filename = f"grid_{grid_idx:03d}_{first_id}_to_{last_id}.png"
            output_path = OUTPUT_DIR / output_filename
            
            # 저장
            grid_image.save(output_path, "PNG", dpi=(300, 300))
            print(f"✅ Saved: {output_path.name}")
            print(f"   Size: {grid_image.size[0]}x{grid_image.size[1]} pixels")
        else:
            print(f"⚠ Grid {grid_idx + 1} 생성 실패")
    
    print(f"\n✅ 완료! 총 {num_grids}개의 그리드 이미지 생성됨")
    print(f"   저장 위치: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

