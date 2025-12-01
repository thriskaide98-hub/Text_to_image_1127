"""
sd_landuse_from_roads.py (clean roads + masked outside)

- input/roads/{id}_condition.png  : 도로 + 주변 맵
- input/masks/{id}_mask.png       : 대상지(흰색) / 배경(검정) 마스크
- Stable Diffusion + ControlNet 으로 land-use 이미지 생성
- 결과: result/sd_landuse/{id}_landuse.png
"""

from pathlib import Path

import torch
import numpy as np
from PIL import Image, ImageDraw

from diffusers import StableDiffusionControlNetPipeline, ControlNetModel


# -------------------------
# 1. 기본 설정
# -------------------------

ROOT_DIR = Path(__file__).resolve().parent
ROADS_DIR = ROOT_DIR / "input" / "roads"
MASKS_DIR = ROOT_DIR / "input" / "masks"
OUT_DIR   = ROOT_DIR / "result/0.main&sd/sd" / "sd_landuse_2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SD_MODEL_ID = "runwayml/stable-diffusion-v1-5"
CONTROLNET_MODEL_ID = "lllyasviel/sd-controlnet-scribble"

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
    "3d, perspective, buildings details, windows, cars, people, "
    "trees with texture, fog, shadow, reflection, noise, blur, "
    "sketch text, labels, numbers, watermark"
)

NUM_STEPS       = 35
GUIDANCE        = 10.0
CONTROL_SCALE   = 1.1
TARGET_SIZE     = (768, 768)  # cond/mask resize 크기


# -------------------------
# 2. 파이프라인 로드
# -------------------------

def load_pipeline(device: str = "cuda"):
    print("🔹 Loading ControlNet model...")
    controlnet = ControlNetModel.from_pretrained(
        CONTROLNET_MODEL_ID,
        torch_dtype=torch.float16,
    )

    print("🔹 Loading Stable Diffusion + ControlNet pipeline...")
    pipe = StableDiffusionControlNetPipeline.from_pretrained(
        SD_MODEL_ID,
        controlnet=controlnet,
        torch_dtype=torch.float16,
        safety_checker=None,
    ).to(device)

    pipe.enable_attention_slicing()
    return pipe


# -------------------------
# 3. 유틸
# -------------------------

def load_pair_images(id_str: str):
    cond_path = ROADS_DIR / f"{id_str}_condition.png"
    mask_path = MASKS_DIR / f"{id_str}_mask.png"
    if not cond_path.exists():
        raise FileNotFoundError(cond_path)
    if not mask_path.exists():
        raise FileNotFoundError(mask_path)

    cond = Image.open(cond_path).convert("RGB").resize(TARGET_SIZE)
    mask = Image.open(mask_path).convert("L").resize(TARGET_SIZE)

    return cond, mask


def pre_mask_condition(cond: Image.Image, mask: Image.Image) -> Image.Image:
    """
    ControlNet에 넣기 전에: 대상지 밖(검정 영역)을 완전 흰색으로 만들어 줌.
    """
    c = np.array(cond)
    m = np.array(mask)
    outside = m < 128
    c[outside] = 255
    return Image.fromarray(c)


def overlay_roads_on_top(base: Image.Image, cond: Image.Image) -> Image.Image:
    """
    최종 결과 위에 roads를 회색/검정 선으로 다시 덧그리기.
    - cond: 원래 도로 이미지 (RGB)
    """
    base_np = np.array(base)
    cond_gray = np.array(cond.convert("L"))

    # 도로 추출 (밝은 도로라면 threshold 반대로 바꿔야 할 수도 있음)
    # 여기서는 "도로가 비교적 밝은 회색"이라고 가정하고 Canny 대신 간단 threshold 사용
    road_mask = cond_gray < 230  # 값은 데이터 보고 조정

    # 회색(또는 검정) 값
    road_color = np.array([180, 180, 180], dtype=np.uint8)

    base_np[road_mask] = road_color

    return Image.fromarray(base_np)


def apply_mask_final(img: Image.Image, mask: Image.Image) -> Image.Image:
    """
    최종 결과에서 대상지 밖을 흰색으로 정리.
    """
    img_np = np.array(img)
    mask_np = np.array(mask)
    outside = mask_np < 128
    img_np[outside] = 255
    return Image.fromarray(img_np)


# -------------------------
# 4. 생성 함수
# -------------------------

def generate_landuse_for_id(pipe, id_str: str, device: str = "cuda"):
    cond_raw, mask = load_pair_images(id_str)

    # 1) ControlNet input용 cond: 대상지 밖은 미리 흰색 처리
    cond_for_cn = pre_mask_condition(cond_raw, mask)

    print(f"🔹 Generating land-use image for id={id_str} ...")
    generator = torch.Generator(device=device).manual_seed(1234)

    out = pipe(
        prompt=PROMPT_BASE,
        image=cond_for_cn,
        num_inference_steps=NUM_STEPS,
        guidance_scale=GUIDANCE,
        controlnet_conditioning_scale=CONTROL_SCALE,
        negative_prompt=NEGATIVE_PROMPT,
        generator=generator,
    )

    gen = out.images[0]

    # 2) 결과 위에 roads를 다시 회색으로 overwrite
    gen_with_roads = overlay_roads_on_top(gen, cond_for_cn)

    # 3) 최종적으로 대상지 밖은 전부 흰색
    final_img = apply_mask_final(gen_with_roads, mask)

    out_path = OUT_DIR / f"{id_str}_landuse.png"
    final_img.save(out_path)
    print(f"✅ Saved: {out_path}")


# -------------------------
# 5. 엔트리 포인트
# -------------------------

def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("👉 Using device:", device)

    pipe = load_pipeline(device=device)

    ids = sorted(
        p.stem.replace("_condition", "") for p in ROADS_DIR.glob("*_condition.png")
    )
    print("🎯 Target IDs:", ids)

    for id_str in ids:
        generate_landuse_for_id(pipe, id_str, device=device)


if __name__ == "__main__":
    main()
