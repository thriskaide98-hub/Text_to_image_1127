"""
sd_landuse_from_roads.py

- 실제 도로망 이미지를 ControlNet 조건으로 사용
- Stable Diffusion으로 토지이용계획(주거/상업/공공/녹지) 탑뷰 이미지 생성
- 결과는 result/sd_landuse/{id}_landuse.png 로 저장
"""

import os
from pathlib import Path

import torch
import numpy as np
from PIL import Image
import cv2

from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
)


# =========================
# 1. 기본 설정
# =========================

# 프로젝트 루트 기준 경로
ROOT_DIR = Path(__file__).resolve().parent
ROADS_DIR = ROOT_DIR / "input" / "roads"
MASKS_DIR = ROOT_DIR / "input" / "masks"
OUT_DIR   = ROOT_DIR / "result/0.main&sd/sd" / "sd_landuse"

OUT_DIR.mkdir(parents=True, exist_ok=True)

# 사용할 모델 이름 (원하면 네가 쓰는 모델로 변경)
SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
CONTROLNET_MODEL_ID = "lllyasviel/sd-controlnet-scribble"  # 라인/스케치용

# 프롬프트 템플릿 (계획도 스타일 강조)
PROMPT_BASE = (
    "flat top-down urban land-use planning map, schematic, vector map style, "
    "solid flat colors only, no textures, no shadows, no gradients, "
    "roads strictly follow the given line drawing, "
    "yellow residential blocks, red commercial corridors and centers, "
    "blue public and institutional facilities, "
    "green parks and open spaces, "
    "clean map, high contrast, minimalistic design, no labels, no text"
)

NEGATIVE_PROMPT = (
    "photo, realistic, satellite imagery, terrain, aerial photo, "
    "3d, perspective, buildings details, windows, cars, people, trees with texture, "
    "fog, shadow, reflection, noise, blur, sketch, hand-drawn text, labels, numbers, watermark"
)

# 생성 파라미터
NUM_STEPS = 40              # 디테일 확보
GUIDANCE = 11.0             # 프롬프트 영향 강하게
CONTROL_SCALE = 1.2         # 도로망을 더 강하게 유지


# =========================
# 2. 파이프라인 로드
# =========================

def load_pipeline(device: str = "cuda"):
    print("🔹 Loading ControlNet model...")
    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL_ID,
        torch_dtype=torch.float16
    )

    print("🔹 Loading Stable Diffusion + ControlNet pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        SD_MODEL_ID,
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)

    # xformers가 설치되어 있지 않은 서버에서는 이 옵션을 켜면 에러가 나므로 주석 처리
    # pipe.enable_xformers_memory_efficient_attention()

    # 이건 메모리 조금 덜 쓰게 해주는 옵션이라 유지해도 괜찮음
    pipe.enable_attention_slicing()

    return pipe


# =========================
# 3. 유틸 함수
# =========================

def load_pair_images(id_str: str, target_size=(768, 768)):
    """
    roads/000_condition.png + masks/000_mask.png 쌍을 로드하고
    SD 입력 크기에 맞게 리사이즈
    """
    cond_path = ROADS_DIR / f"{id_str}_condition.png"
    mask_path = MASKS_DIR / f"{id_str}_mask.png"

    if not cond_path.exists():
        raise FileNotFoundError(cond_path)
    if not mask_path.exists():
        raise FileNotFoundError(mask_path)

    cond = Image.open(cond_path).convert("RGB")
    mask = Image.open(mask_path).convert("L")

    cond = cond.resize(target_size, Image.BILINEAR)
    mask = mask.resize(target_size, Image.NEAREST)

    return cond, mask


def apply_mask(image: Image.Image, mask: Image.Image) -> Image.Image:
    """
    생성된 이미지에서 mask 밖(검은 영역)을 흰색으로 처리
    """
    img_np = np.array(image)
    mask_np = np.array(mask)

    # mask: 흰색(255) = keep, 검정(0) = outside
    outside = mask_np < 128
    img_np[outside] = 255  # 바깥 영역 흰색

    return Image.fromarray(img_np)


# =========================
# 4. 메인 생성 함수
# =========================

def generate_landuse_for_id(pipe, id_str: str, device="cuda"):
    cond_img, mask_img = load_pair_images(id_str)

    prompt = PROMPT_BASE
    negative_prompt = NEGATIVE_PROMPT

    print(f"🔹 Generating land-use image for id={id_str} ...")

    # 재현 가능성을 위해 seed 고정 (원하면 None 으로 바꿔도 됨)
    generator = torch.Generator(device=device).manual_seed(1234)

    # Stable Diffusion + ControlNet 실행
    out = pipe(
        prompt=prompt,
        image=cond_img,
        num_inference_steps=NUM_STEPS,
        guidance_scale=GUIDANCE,
        controlnet_conditioning_scale=CONTROL_SCALE,
        negative_prompt=negative_prompt,
        generator=generator,
    )

    gen_img = out.images[0]

    # mask 밖은 흰색으로 처리
    gen_img_masked = apply_mask(gen_img, mask_img)

    # 저장
    out_path = OUT_DIR / f"{id_str}_landuse.png"
    gen_img_masked.save(out_path)
    print(f"✅ Saved: {out_path}")


# =========================
# 5. 엔트리 포인트
# =========================

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"👉 Using device: {device}")

    pipe = load_pipeline(device=device)

    # roads/ 폴더에 있는 *_condition.png 파일들 기준으로 id 리스트 만들기
    ids = sorted([p.stem.replace("_condition", "") for p in ROADS_DIR.glob("*_condition.png")])

    print("🎯 Target IDs:", ids)

    for id_str in ids:
        generate_landuse_for_id(pipe, id_str, device=device)


if __name__ == "__main__":
    main()
