# Towards Automated Urban Concept Planning: A Generative AI Approach

**Chulhyun Kim & Youngchul Kim**  
Departments of Civil and Environmental Engineering, KAIST

---

## Slide 1: Title Slide

**Towards Automated Urban Concept Planning: A Generative AI Approach**

Chulhyun Kim, Youngchul Kim  
KAIST, Department of Civil and Environmental Engineering

---

## Slide 2: Outline

1. **Background & Motivation**
2. **Research Objectives**
3. **Proposed Framework**
4. **Implementation Details**
5. **Experimental Results**
6. **Conclusion & Future Work**

---

## Slide 3: Background & Motivation

### Current Challenges in Urban Planning

- **Heavy reliance on expert intuition** and manual drafting
- **Limited efficiency and scalability** in concept development
- **Repetitive spatial configuration tasks** consume significant time
- **Early-stage design** lacks systematic automation support

### Previous Approaches

- **Rule-based methods**: Limited design flexibility
- **Optimization-driven methods**: Insufficient integration of planning intent
- **Gap**: Need for flexible, intent-driven automation

---

## Slide 4: Research Objectives

### Main Goal

Explore the **feasibility of supporting early-stage urban design** through partial automation of repetitive spatial configuration tasks.

### Key Questions

1. Can LLMs translate **text-based planning instructions** into structured spatial layouts?
2. Can we generate **machine-readable plan data** that satisfies planning constraints?
3. Can we provide **basic spatial evaluation** to verify plan validity?

---

## Slide 5: Proposed Framework Overview

### Five Main Stages

1. **Input**: Planning requirements through structured prompts
2. **Generation**: Hierarchical plan data in machine-readable format
3. **Construction**: Grid-based street network and automatic land-use allocation
4. **Rendering**: SVG/PNG-based visual output
5. **Evaluation**: Basic spatial validation (land-use consistency, road connectivity)

---

## Slide 6: Preliminary Testing - Initial Prototype

### Initial Approach (`main.py`)

Before implementing the full pipeline, we first tested **LLM's capability to generate structured urban plans** from scratch.

#### Test Setup
- **Input**: Text prompt only (no road images)
- **Task**: Generate a 5×5 grid-based concept plan
- **Model**: GPT-4.1-mini
- **Output**: JSON with 25 blocks (200×200m each)

#### Key Features
- **Fixed grid structure**: 5×5 = 25 blocks
- **Site dimensions**: 1000×1000 meters
- **Land-use categories**: Residential, Commercial, Public, Green
- **Automatic visualization**: PNG output with color coding

#### Results
- ✅ LLM successfully generated valid JSON structures
- ✅ Reasonable land-use distribution patterns
- ✅ Demonstrated feasibility of LLM-based planning

#### Transition to Full Pipeline
This prototype validated that LLMs can handle structured spatial planning tasks, leading to the development of the **image-based pipeline** that incorporates real road networks.

---

## Slide 7: Implementation Architecture

### Three-Stage Pipeline

```
Input Images          Stage 1              Stage 2              Stage 3
(Roads + Masks)  →  Parcel Extraction  →  LLM Planning  →  Visualization
```

**Stage 1**: Road network → Parcel polygons  
**Stage 2**: Parcels → Land-use assignment (LLM)  
**Stage 3**: Land-use data → Colored map with roads

---

## Slide 8: Stage 1 - Parcel Extraction

### Input
- Road condition image (`{id}_condition.png`)
- Site mask image (`{id}_mask.png`)

### Process
1. **Road detection**: Binary mask from grayscale threshold (< 220)
2. **Dilation**: Expand road areas to create separation
3. **Connected components**: Identify individual parcels
4. **Contour extraction**: Convert to polygon coordinates
5. **Filtering**: Remove small noise and edge parcels

### Output
- `{id}_parcels.json`: Site geometry + parcel polygons with metadata

---

## Slide 9: Stage 1 - Technical Details

### Key Parameters
- **Target size**: 1024×1024 pixels
- **Site dimensions**: 1000×1000 meters
- **Road threshold**: Grayscale < 220
- **Dilation iterations**: 2 (parcel separation)
- **Erosion iterations**: 1 (road width expansion)
- **Minimum parcel area**: 1500 pixels

### Coordinate Transformation
- Pixel coordinates → Site coordinates (0-1000m)
- Y-axis flip: Image top → Site top
- Centroid normalization: 0-1 range for LLM input

---

## Slide 10: Stage 2 - LLM-Based Land-Use Assignment

### Input
- Parcel JSON with:
  - `id`, `area_px`, `centroid_norm`, `polygon`

### LLM Prompt Strategy
- **Model**: GPT-4.1-mini
- **Temperature**: 0.4 (balanced creativity/consistency)
- **Heuristic rules**:
  - Large parcels near center → Commercial
  - Outer boundary parcels → Residential/Green
  - Medium parcels near intersections → Public
  - Target mix: Mostly Residential, fewer Commercial, some Public/Green

### Output
- `{id}_landuse.json`: Parcels with assigned land-use categories

---

## Slide 11: Stage 2 - LLM Prompt Design

### Land-Use Categories
- **Residential** (주거)
- **Commercial** (상업)
- **Public** (공공)
- **Green** (녹지)

### Prompt Structure
```
You are an urban planner AI.
Given: site + parcels (id, area, centroid, polygon)
Task: Assign land_use to each parcel
Rules: [heuristic guidelines]
Output: JSON with same structure + land_use field
```

### Optimization (v2)
- **Summary-based**: Send parcel summaries (not full polygons) to reduce token usage
- **Area-based targets**: Target share by area, not count
- **Position tags**: Coarse location labels (center_top, left_bottom, etc.)

---

## Slide 12: Stage 3 - Visualization

### Input
- Land-use JSON (`{id}_landuse.json`)
- Original road/mask images

### Process
1. **Road polygon extraction**: Reuse Stage 1 logic
   - Road dilation (4 iterations for visibility)
   - Contour → polygon conversion
2. **Parcel rendering**: Color-coded polygons
3. **Layering**: Roads (zorder=1) → Parcels (zorder=2)

### Color Scheme
- **Residential**: `#fff59d` (연노랑)
- **Commercial**: `#ef5350` (빨강)
- **Public**: `#42a5f5` (파랑)
- **Green**: `#66bb6a` (초록)
- **Roads**: `#dddddd` (밝은 회색)

### Output
- `{id}_landuse_flat_with_roads.png` (300 DPI)

---

## Slide 13: Evaluation Module

### Basic Spatial Validation

1. **Land-use allocation consistency**
   - Verify all parcels have valid land-use categories
   - Check distribution matches heuristic expectations

2. **Road connectivity** (future work)
   - Verify road network forms connected graph
   - Check parcel accessibility

3. **Spatial validity**
   - Parcel boundaries within site limits
   - No overlapping parcels (by construction)
   - Minimum parcel size constraints

### Current Status
- ✅ Basic validation implemented
- 🔄 Advanced metrics: Future work

---

## Slide 14: Experimental Setup

### Test Site
- **Simplified rectangular site**: 1000×1000 meters
- **Multiple road network patterns**: Various configurations
- **Input images**: 10 test cases (000-009)

### Evaluation Metrics
- **Processing time**: Per-stage breakdown
- **Parcel extraction accuracy**: Visual inspection
- **Land-use distribution**: Category counts and ratios
- **Visual quality**: Output image assessment

---

## Slide 15: Results - Parcel Extraction

### Stage 1 Performance

- **Average parcels per site**: ~15-30 parcels
- **Processing time**: < 1 second per image
- **Success rate**: 100% (all test cases processed)

### Observations
- ✅ Reliable road detection with threshold-based method
- ✅ Effective parcel separation through morphological operations
- ⚠️ Edge parcels filtered out (by design)
- ⚠️ Very small parcels removed (noise reduction)

---

## Slide 16: Results - LLM Planning

### Stage 2 Performance

- **Model**: GPT-4.1-mini
- **Average response time**: ~2-3 seconds per site
- **JSON parsing success**: 100% (with code fence removal)

### Land-Use Distribution (Example)
- Residential: ~60% (target: 60%)
- Commercial: ~20% (target: 20%)
- Public: ~10% (target: 10%)
- Green: ~10% (target: 10%)

### Observations
- ✅ LLM follows heuristic rules consistently
- ✅ Reasonable spatial distribution patterns
- ⚠️ Some variability in edge cases

---

## Slide 17: Results - Visualization

### Stage 3 Output Quality

- **Resolution**: 300 DPI, suitable for presentation
- **Visual clarity**: Clear distinction between land-use categories
- **Road integration**: Roads properly overlaid on parcels

### Sample Results
- Multiple test cases successfully rendered
- Consistent color scheme across all outputs
- Clean, schematic map style (as intended)

---

## Slide 18: Key Findings

### What Works Well

1. ✅ **End-to-end pipeline**: Successfully links road images to land-use maps
2. ✅ **LLM integration**: Effectively translates spatial context to planning decisions
3. ✅ **Flexible framework**: Adaptable to different road network patterns
4. ✅ **Machine-readable output**: JSON format enables further processing

### Limitations

1. ⚠️ **Conceptual resolution**: Simplified representation, not detailed design
2. ⚠️ **Basic evaluation**: Limited validation metrics
3. ⚠️ **No iterative refinement**: Single-pass generation
4. ⚠️ **Fixed site size**: Currently 1000×1000m only

---

## Slide 19: Contributions

### Technical Contributions

1. **Novel pipeline**: First integration of computer vision + LLM for urban planning
2. **Parcel extraction method**: Robust road-based segmentation
3. **LLM prompt engineering**: Effective translation of spatial context to planning decisions
4. **Evaluation framework**: Basic validation for generated plans

### Practical Implications

- **Time savings**: Automates repetitive early-stage tasks
- **Design exploration**: Enables rapid iteration of concept plans
- **Scalability**: Can process multiple sites efficiently
- **Accessibility**: Reduces barrier to entry for planning tasks

---

## Slide 20: Future Work

### Short-term Improvements

1. **Enhanced evaluation metrics**
   - Road connectivity analysis
   - Accessibility measures
   - Land-use compatibility scoring

2. **Iterative refinement**
   - Feedback loop for plan improvement
   - Multi-pass generation with constraints

3. **Extended input formats**
   - Text-based planning requirements
   - Multiple site sizes and shapes

### Long-term Directions

1. **Integration with CAD/GIS tools**
2. **Multi-objective optimization** (density, accessibility, etc.)
3. **Interactive design interface**
4. **Learning from expert plans** (fine-tuning)

---

## Slide 21: Conclusion

### Summary

- ✅ **Feasibility demonstrated**: LLMs can generate valid urban concept plans
- ✅ **Framework operational**: End-to-end pipeline from images to maps
- ✅ **Basic evaluation**: Simple validation mechanisms in place

### Positioning

This study is an **exploratory step** toward AI-assisted urban design, not a complete solution. It highlights the potential of LLMs as **design co-agents** in urban planning.

### Next Steps

- Expand evaluation metrics
- Integrate iterative refinement
- Test on diverse real-world sites

---

## Slide 22: Thank You

### Questions?

**Contact**:  
Chulhyun Kim: Chulhyun98@kaist.ac.kr  
Youngchul Kim: youngchulkim@kaist.ac.kr

**Code Repository**: Available upon request

---

## Appendix: Technical Stack

### Libraries & Tools
- **Computer Vision**: OpenCV, PIL/Pillow, NumPy
- **LLM**: OpenAI API (GPT-4.1-mini)
- **Visualization**: Matplotlib
- **Data Format**: JSON

### Processing Pipeline
- **Stage 1**: Image processing → Polygon extraction
- **Stage 2**: LLM API calls → JSON parsing
- **Stage 3**: Matplotlib rendering → PNG export

---

## Appendix: Example Output Structure

### Input Files
```
input/
  roads/{id}_condition.png
  masks/{id}_mask.png
```

### Intermediate Files
```
result/
  1.parcels/{id}_parcels.json
  2.plans/{id}_landuse.json
```

### Final Output
```
result/
  3.landuse_flat/{id}_landuse_flat_with_roads.png
```

---

## Appendix: Code Structure

### Main Scripts
1. `main.py`: Initial prototype (5×5 grid generation test)
2. `1.roads_to_parcels_1127.py`: Parcel extraction
3. `2.plan_from_parcel_llm_1127.py`: LLM-based planning
4. `3.render_landuse_from_json_1127.py`: Visualization

### Key Functions
- `call_llm_for_plan()`: Direct LLM-based grid generation (prototype)
- `extract_parcels()`: Road detection → Parcel polygons
- `assign_land_use_for_id()`: LLM call → Land-use assignment
- `render_for_id()`: JSON → Colored map

---

# 한국어 버전 (Korean Version)

# 도시 개념 계획 자동화를 위한 생성형 AI 접근법

**김철현 & 김영철**  
한국과학기술원 건설및환경공학과

---

## 슬라이드 1: 제목 슬라이드

**도시 개념 계획 자동화를 위한 생성형 AI 접근법**

김철현, 김영철  
한국과학기술원 건설및환경공학과

---

## 슬라이드 2: 발표 개요

1. **배경 및 동기**
2. **연구 목적**
3. **제안 프레임워크**
4. **구현 상세**
5. **실험 결과**
6. **결론 및 향후 연구**

---

## 슬라이드 3: 배경 및 동기

### 도시 계획의 현재 과제

- **전문가 직관과 수동 도면 작업에 대한 높은 의존성**
- **개념 개발 단계의 제한된 효율성과 확장성**
- **반복적인 공간 구성 작업이 상당한 시간 소모**
- **초기 단계 설계에 대한 체계적인 자동화 지원 부족**

### 기존 접근법

- **규칙 기반 방법**: 제한된 설계 유연성
- **최적화 기반 방법**: 계획 의도 통합 부족
- **공백**: 유연하고 의도 기반의 자동화 필요

---

## 슬라이드 4: 연구 목적

### 주요 목표

반복적인 공간 구성 작업의 부분적 자동화를 통해 **초기 단계 도시 설계 지원의 실현 가능성** 탐구

### 핵심 질문

1. LLM이 **텍스트 기반 계획 지시사항**을 구조화된 공간 레이아웃으로 변환할 수 있는가?
2. 계획 제약 조건을 만족하는 **기계 판독 가능한 계획 데이터**를 생성할 수 있는가?
3. 계획 유효성을 검증하기 위한 **기본 공간 평가**를 제공할 수 있는가?

---

## 슬라이드 5: 제안 프레임워크 개요

### 5단계 주요 과정

1. **입력**: 구조화된 프롬프트를 통한 계획 요구사항
2. **생성**: 기계 판독 가능 형식의 계층적 계획 데이터
3. **구성**: 그리드 기반 도로망 및 자동 토지이용 배치
4. **렌더링**: SVG/PNG 기반 시각적 출력
5. **평가**: 기본 공간 검증 (토지이용 일관성, 도로 연결성)

---

## 슬라이드 6: 사전 테스트 - 초기 프로토타입

### 초기 접근법 (`main.py`)

전체 파이프라인 구현 전, **LLM이 처음부터 구조화된 도시 계획을 생성할 수 있는 능력**을 먼저 테스트했습니다.

#### 테스트 설정
- **입력**: 텍스트 프롬프트만 (도로 이미지 없음)
- **작업**: 5×5 그리드 기반 개념 계획 생성
- **모델**: GPT-4.1-mini
- **출력**: 25개 블록(각 200×200m)을 포함한 JSON

#### 주요 특징
- **고정 그리드 구조**: 5×5 = 25개 블록
- **대지 크기**: 1000×1000 미터
- **토지이용 카테고리**: 주거, 상업, 공공, 녹지
- **자동 시각화**: 색상 코딩이 포함된 PNG 출력

#### 결과
- ✅ LLM이 유효한 JSON 구조를 성공적으로 생성
- ✅ 합리적인 토지이용 분포 패턴
- ✅ LLM 기반 계획의 실현 가능성 입증

#### 전체 파이프라인으로의 전환
이 프로토타입은 LLM이 구조화된 공간 계획 작업을 처리할 수 있음을 검증했으며, 실제 도로망을 통합하는 **이미지 기반 파이프라인** 개발로 이어졌습니다.

---

## 슬라이드 7: 구현 아키텍처

### 3단계 파이프라인

```
입력 이미지          1단계              2단계              3단계
(도로 + 마스크)  →  필지 추출      →  LLM 계획      →  시각화
```

**1단계**: 도로망 → 필지 폴리곤  
**2단계**: 필지 → 토지이용 할당 (LLM)  
**3단계**: 토지이용 데이터 → 도로가 포함된 색상 지도

---

## 슬라이드 8: 1단계 - 필지 추출

### 입력
- 도로 조건 이미지 (`{id}_condition.png`)
- 대지 마스크 이미지 (`{id}_mask.png`)

### 처리 과정
1. **도로 검출**: 그레이스케일 임계값(< 220)으로 바이너리 마스크 생성
2. **팽창**: 도로 영역 확장하여 분리 공간 생성
3. **연결된 구성요소**: 개별 필지 식별
4. **윤곽선 추출**: 폴리곤 좌표로 변환
5. **필터링**: 작은 노이즈 및 경계 필지 제거

### 출력
- `{id}_parcels.json`: 대지 기하학 + 메타데이터가 포함된 필지 폴리곤

---

## 슬라이드 9: 1단계 - 기술적 세부사항

### 주요 파라미터
- **목표 크기**: 1024×1024 픽셀
- **대지 크기**: 1000×1000 미터
- **도로 임계값**: 그레이스케일 < 220
- **팽창 반복**: 2회 (필지 분리)
- **침식 반복**: 1회 (도로 폭 확장)
- **최소 필지 면적**: 1500 픽셀

### 좌표 변환
- 픽셀 좌표 → 대지 좌표 (0-1000m)
- Y축 반전: 이미지 상단 → 대지 상단
- 중심점 정규화: LLM 입력을 위한 0-1 범위

---

## 슬라이드 10: 2단계 - LLM 기반 토지이용 할당

### 입력
- 다음을 포함한 필지 JSON:
  - `id`, `area_px`, `centroid_norm`, `polygon`

### LLM 프롬프트 전략
- **모델**: GPT-4.1-mini
- **Temperature**: 0.4 (창의성/일관성 균형)
- **휴리스틱 규칙**:
  - 중심부 근처 큰 필지 → 상업
  - 외곽 경계 필지 → 주거/녹지
  - 교차로 근처 중간 크기 필지 → 공공
  - 목표 혼합: 대부분 주거, 적은 상업, 일부 공공/녹지

### 출력
- `{id}_landuse.json`: 토지이용 카테고리가 할당된 필지

---

## 슬라이드 11: 2단계 - LLM 프롬프트 설계

### 토지이용 카테고리
- **Residential** (주거)
- **Commercial** (상업)
- **Public** (공공)
- **Green** (녹지)

### 프롬프트 구조
```
당신은 도시 계획 AI입니다.
주어진 것: 대지 + 필지 (id, 면적, 중심점, 폴리곤)
작업: 각 필지에 토지이용 할당
규칙: [휴리스틱 가이드라인]
출력: land_use 필드가 추가된 동일한 구조의 JSON
```

### 최적화 (v2)
- **요약 기반**: 토큰 사용량 감소를 위해 필지 요약만 전송 (전체 폴리곤 제외)
- **면적 기반 목표**: 개수가 아닌 면적 기준 목표 비율
- **위치 태그**: 대략적인 위치 레이블 (center_top, left_bottom 등)

---

## 슬라이드 12: 3단계 - 시각화

### 입력
- 토지이용 JSON (`{id}_landuse.json`)
- 원본 도로/마스크 이미지

### 처리 과정
1. **도로 폴리곤 추출**: 1단계 로직 재사용
   - 도로 팽창 (가시성을 위해 4회 반복)
   - 윤곽선 → 폴리곤 변환
2. **필지 렌더링**: 색상 코딩된 폴리곤
3. **레이어링**: 도로 (zorder=1) → 필지 (zorder=2)

### 색상 체계
- **주거**: `#fff59d` (연노랑)
- **상업**: `#ef5350` (빨강)
- **공공**: `#42a5f5` (파랑)
- **녹지**: `#66bb6a` (초록)
- **도로**: `#dddddd` (밝은 회색)

### 출력
- `{id}_landuse_flat_with_roads.png` (300 DPI)

---

## 슬라이드 13: 평가 모듈

### 기본 공간 검증

1. **토지이용 할당 일관성**
   - 모든 필지가 유효한 토지이용 카테고리를 가지는지 확인
   - 분포가 휴리스틱 기대치와 일치하는지 확인

2. **도로 연결성** (향후 작업)
   - 도로망이 연결된 그래프를 형성하는지 확인
   - 필지 접근성 확인

3. **공간 유효성**
   - 필지 경계가 대지 한계 내에 있는지
   - 중복 필지 없음 (구성상)
   - 최소 필지 크기 제약 조건

### 현재 상태
- ✅ 기본 검증 구현 완료
- 🔄 고급 지표: 향후 작업

---

## 슬라이드 14: 실험 설정

### 테스트 대지
- **단순화된 직사각형 대지**: 1000×1000 미터
- **다양한 도로망 패턴**: 다양한 구성
- **입력 이미지**: 10개 테스트 케이스 (000-009)

### 평가 지표
- **처리 시간**: 단계별 세부 분석
- **필지 추출 정확도**: 시각적 검사
- **토지이용 분포**: 카테고리 개수 및 비율
- **시각적 품질**: 출력 이미지 평가

---

## 슬라이드 15: 결과 - 필지 추출

### 1단계 성능

- **대지당 평균 필지 수**: 약 15-30개 필지
- **처리 시간**: 이미지당 < 1초
- **성공률**: 100% (모든 테스트 케이스 처리 완료)

### 관찰 사항
- ✅ 임계값 기반 방법으로 신뢰할 수 있는 도로 검출
- ✅ 형태학적 연산을 통한 효과적인 필지 분리
- ⚠️ 경계 필지 제외 (설계상)
- ⚠️ 매우 작은 필지 제거 (노이즈 감소)

---

## 슬라이드 16: 결과 - LLM 계획

### 2단계 성능

- **모델**: GPT-4.1-mini
- **평균 응답 시간**: 대지당 약 2-3초
- **JSON 파싱 성공률**: 100% (코드 펜스 제거 포함)

### 토지이용 분포 (예시)
- 주거: 약 60% (목표: 60%)
- 상업: 약 20% (목표: 20%)
- 공공: 약 10% (목표: 10%)
- 녹지: 약 10% (목표: 10%)

### 관찰 사항
- ✅ LLM이 휴리스틱 규칙을 일관되게 따름
- ✅ 합리적인 공간 분포 패턴
- ⚠️ 일부 엣지 케이스에서 가변성 존재

---

## 슬라이드 17: 결과 - 시각화

### 3단계 출력 품질

- **해상도**: 300 DPI, 발표에 적합
- **시각적 명확성**: 토지이용 카테고리 간 명확한 구분
- **도로 통합**: 필지 위에 도로가 적절히 오버레이됨

### 샘플 결과
- 여러 테스트 케이스 성공적으로 렌더링
- 모든 출력에서 일관된 색상 체계
- 깔끔한 개략도 스타일 (의도대로)

---

## 슬라이드 18: 주요 발견사항

### 잘 작동하는 부분

1. ✅ **엔드투엔드 파이프라인**: 도로 이미지를 토지이용 지도로 성공적으로 연결
2. ✅ **LLM 통합**: 공간 맥락을 계획 결정으로 효과적으로 변환
3. ✅ **유연한 프레임워크**: 다양한 도로망 패턴에 적응 가능
4. ✅ **기계 판독 가능한 출력**: JSON 형식으로 추가 처리 가능

### 한계점

1. ⚠️ **개념적 해상도**: 단순화된 표현, 상세 설계 아님
2. ⚠️ **기본 평가**: 제한된 검증 지표
3. ⚠️ **반복적 개선 없음**: 단일 패스 생성
4. ⚠️ **고정된 대지 크기**: 현재 1000×1000m만 지원

---

## 슬라이드 19: 기여도

### 기술적 기여

1. **새로운 파이프라인**: 도시 계획을 위한 컴퓨터 비전 + LLM의 첫 통합
2. **필지 추출 방법**: 강건한 도로 기반 분할
3. **LLM 프롬프트 엔지니어링**: 공간 맥락을 계획 결정으로 효과적으로 변환
4. **평가 프레임워크**: 생성된 계획에 대한 기본 검증

### 실용적 함의

- **시간 절약**: 반복적인 초기 단계 작업 자동화
- **설계 탐색**: 개념 계획의 빠른 반복 가능
- **확장성**: 여러 대지를 효율적으로 처리 가능
- **접근성**: 계획 작업의 진입 장벽 감소

---

## 슬라이드 20: 향후 연구

### 단기 개선사항

1. **향상된 평가 지표**
   - 도로 연결성 분석
   - 접근성 측정
   - 토지이용 호환성 점수

2. **반복적 개선**
   - 계획 개선을 위한 피드백 루프
   - 제약 조건이 있는 다중 패스 생성

3. **확장된 입력 형식**
   - 텍스트 기반 계획 요구사항
   - 다양한 대지 크기 및 형태

### 장기 방향

1. **CAD/GIS 도구와의 통합**
2. **다중 목표 최적화** (밀도, 접근성 등)
3. **대화형 설계 인터페이스**
4. **전문가 계획으로부터 학습** (파인튜닝)

---

## 슬라이드 21: 결론

### 요약

- ✅ **실현 가능성 입증**: LLM이 유효한 도시 개념 계획을 생성할 수 있음
- ✅ **프레임워크 작동**: 이미지에서 지도까지의 엔드투엔드 파이프라인
- ✅ **기본 평가**: 간단한 검증 메커니즘 구축

### 포지셔닝

이 연구는 완전한 솔루션이 아닌 AI 지원 도시 설계를 향한 **탐색적 단계**입니다. LLM이 도시 계획에서 **설계 협력 에이전트**로서의 잠재력을 강조합니다.

### 다음 단계

- 평가 지표 확장
- 반복적 개선 통합
- 다양한 실제 대지에서 테스트

---

## 슬라이드 22: 감사 인사

### 질문이 있으시면?

**연락처**:  
김철현: Chulhyun98@kaist.ac.kr  
김영철: youngchulkim@kaist.ac.kr

**코드 저장소**: 요청 시 제공 가능

---

## 부록: 기술 스택

### 라이브러리 및 도구
- **컴퓨터 비전**: OpenCV, PIL/Pillow, NumPy
- **LLM**: OpenAI API (GPT-4.1-mini)
- **시각화**: Matplotlib
- **데이터 형식**: JSON

### 처리 파이프라인
- **1단계**: 이미지 처리 → 폴리곤 추출
- **2단계**: LLM API 호출 → JSON 파싱
- **3단계**: Matplotlib 렌더링 → PNG 내보내기

---

## 부록: 출력 구조 예시

### 입력 파일
```
input/
  roads/{id}_condition.png
  masks/{id}_mask.png
```

### 중간 파일
```
result/
  1.parcels/{id}_parcels.json
  2.plans/{id}_landuse.json
```

### 최종 출력
```
result/
  3.landuse_flat/{id}_landuse_flat_with_roads.png
```

---

## 부록: 코드 구조

### 주요 스크립트
1. `main.py`: 초기 프로토타입 (5×5 그리드 생성 테스트)
2. `1.roads_to_parcels_1127.py`: 필지 추출
3. `2.plan_from_parcel_llm_1127.py`: LLM 기반 계획
4. `3.render_landuse_from_json_1127.py`: 시각화

### 주요 함수
- `call_llm_for_plan()`: 직접 LLM 기반 그리드 생성 (프로토타입)
- `extract_parcels()`: 도로 검출 → 필지 폴리곤
- `assign_land_use_for_id()`: LLM 호출 → 토지이용 할당
- `render_for_id()`: JSON → 색상 지도

