# IllusionCAPTCHA / IllusionDiffusion 재현 모델 기획서

## 1. 모델 셋업 개요

- **목표**: Google Sites `Illusionary CAPTCHA` 및 논문 *IllusionCAPTCHA: A CAPTCHA based on Visual Illusion*에서 사용하는 이미지 착시 기반 CAPTCHA 생성 파이프라인을, 공개된 `AP123/IllusionDiffusion` Space와 기타 공개 리소스를 활용해 로컬·클라우드 환경에서 재현하고 확장한다.[web:1][web:2][web:13][web:60]
- **배경**
  - IllusionCAPTCHA는 시각 착시를 이용해 인간에게는 직관적이지만 LLM·비전 모델에게는 어렵게 느껴지는 “Human-Easy but AI-Hard” 유형의 CAPTCHA를 제안한다.[web:2][web:60]
  - 착시 이미지는 주로 Hugging Face Space `AP123/IllusionDiffusion`의 Stable Diffusion 1.x + ControlNet 파이프라인을 활용해 생성된다.[web:13]
  - 공식 구현 전체(데이터셋, 생성 코드)는 별도 깃허브 등으로 공개되어 있지 않으므로, 논문 설명과 공개된 `app.py`, 유관 논문의 코드를 조합해 재현해야 한다.[web:1][web:2][web:9]

## 2. 참고 리소스

### 2.1 핵심 레퍼런스

- Illusionary CAPTCHA 사이트  
  - URL: https://sites.google.com/view/illusionarycaptcha  
  - 내용: IllusionCAPTCHA 개념 소개, 인터페이스 스크린샷, 실험 관련 안내.[web:1]

- 논문: *IllusionCAPTCHA: A CAPTCHA based on Visual Illusion*  
  - arXiv: https://arxiv.org/abs/2502.05461  
  - HTML: https://arxiv.org/html/2502.05461v1  
  - 주요 내용:  
    - 시각 착시를 활용한 새로운 CAPTCHA 설계.[web:2][web:60]  
    - “베이스 이미지 + 프롬프트” 혼합을 통한 착시 생성 3단계 파이프라인.[web:2]  
    - 여러 시드로 생성 후 cosine similarity 기반 후보 선택, LLM 혼동을 유도하는 선택지 설계.[web:2]

- Hugging Face Space: `AP123/IllusionDiffusion`  
  - URL(Space): https://huggingface.co/spaces/AP123/IllusionDiffusion  
  - 설명: 이미지 인풋(패턴/QR/사진)과 텍스트 프롬프트를 받아 착시 이미지를 생성하는 공개 Space.[web:13][web:64]

- Space 코드: `app.py`  
  - URL: https://huggingface.co/spaces/AP123/IllusionDiffusion/blob/main/app.py  
  - 내용: Stable Diffusion 1.x + ControlNet + VAE 구성, 전처리 및 `inference()` 로직, Gradio UI 정의 포함.[web:9]  
  - 별도의 비공개 모듈 없이, 착시 생성 파이프라인은 `app.py`와 동일 Space 내 유틸 스크립트에서 완결되는 형태.[web:9][web:24]

### 2.2 보조 레퍼런스 (확장/아이디어용)

- Diffusion Illusions: Hiding Images in Plain Sight  
  - 사이트: https://diffusionillusions.com  
  - 내용: score distillation 기반으로 이미지 안에 다른 이미지/메시지를 숨기는 다양한 착시·스테가노그래피 기법 및 코드.[page:3]

- Visual Anagrams (CVPR): Generating Multi-View Optical Illusions with Diffusion Models  
  - 코드: https://github.com/dangeng/visual_anagrams  
  - 내용: 하나의 이미지를 회전/뷰포인트에 따라 다른 것으로 인식되게 만드는 diffusion 기반 착시 기법.[web:12][web:14]

- Color Visual Illusions and Diffusion Models  
  - 논문: https://arxiv.org/html/2412.10122v1  
  - 데모: https://alviur.github.io/color-illusion-diffusion/  
  - 내용: diffusion latent에서 인간과 유사한 색·밝기 착시가 나타나는 현상 분석 및 착시 생성 알고리즘.[web:10][web:7]

## 3. 현재까지 파악된 기술 맥락

### 3.1 IllusionCAPTCHA 파이프라인 개요

- 베이스 콘텐츠
  - 텍스트 CAPTCHA: 짧고 명확한 영어 단어(예: day, sun)를 이미지로 렌더링해 베이스 이미지로 사용.[web:2]
  - 이미지 CAPTCHA: 명확하게 라벨링 가능한 오브젝트/랜드마크의 베이스 이미지.[web:2]

- 착시 이미지 생성
  - 입력: 베이스 이미지 + 착시용 텍스트 프롬프트(예: “huge forest”).[web:2]
  - 모델: Stable Diffusion 기반 text-to-image 파이프라인 + ControlNet (IllusionDiffusion에서 사용하는 패턴/QR 기반 설정).[web:13][web:9]
  - 여러 시드로 샘플링 후, 베이스와 cosine similarity가 가장 낮은 이미지를 최종 후보로 선택.[web:2]

- 문제 구성
  - 인간에게는 숨은 단어/오브젝트가 쉽게 인지되도록 하고,  
  - LLM·비전 모델은 프롬프트 기반 전경 설명에 끌리도록 선택지와 질문 문장을 설계.[web:2][web:60]

### 3.2 IllusionDiffusion Space 구조 (현행 app.py 기준)

- 주요 구성요소[web:9]
  - 베이스 모델: SD 1.x 계열 커스텀 체크포인트(예: `Realistic_Vision_V5.1_noVAE`).[web:45]
  - ControlNet: QR/패턴용 ControlNet(예: `monster-labs/control_v1p_sd15_qrcode_monster`).[page:1]
  - VAE, safety checker, CLIP image processor 등.
  - `inference()` 함수:
    - 입력 패턴/이미지 전처리 및 리사이즈.
    - main Stable Diffusion 파이프라인으로 저해상도 latent 생성.
    - 업샘플 후 image_pipe로 최종 고해상도 이미지 생성.[web:9]

- UI 레이어
  - Gradio Blocks 기반 웹 UI, Spaces용 데코레이터(`@spaces.GPU`) 등은 모두 `app.py` 상단/하단에 위치하며, inference 로직과 분리 가능.[web:9]

## 4. 이번 프로젝트 스코프

### 4.1 1단계: 논문 기반 IllusionCAPTCHA 착시 생성 모델 재현 (우선 목표)

- IllusionCAPTCHA 논문에서 설명한 3단계 파이프라인을, 공개된 IllusionDiffusion `app.py`를 사용해 그대로 재현하는 것을 1차 목표로 한다.[web:2][web:9]
- 이 단계에서는:
  - IllusionDiffusion Space와 동일한 구조(SD 1.x + ControlNet + VAE) 기반 inference 파이프라인을 로컬/클라우드에서 동작시키고,[web:9][web:13]
  - 논문과 동일하게 “베이스 이미지 + 프롬프트 → 다수 시드로 착시 이미지 생성 → cosine similarity 최소 후보 선택” 과정을 구현한다.[web:2]
- 베이스 이미지는 **원문 이미지(실세계/공개 리소스)를 수집해 그대로 입력으로 사용**하며, 이 단계에서는 별도의 실루엣 가공은 필수가 아니라 옵션으로만 고려한다.[web:2]

### 4.2 2단계: 아이코닉 실루엣 기반 베이스 이미지 설계 (후속 작업, 별도 섹션)

- 1단계에서 논문 파이프라인이 충분히 안정적으로 착시 이미지를 생성하는지 확인한 이후,
  - 사람 기준으로 즉시 인지 가능한 아이코닉 실루엣/심볼 세트를 별도 섹션에서 정의하고,[web:2][web:75]
  - 이들을 베이스 이미지로 사용하는 고품질 CAPTCHA 전용 데이터셋을 구축한다.
- 가공 방식(실루엣 변환, 대비 조정 등)은 오브젝트별로 실험한 뒤, 필요할 때만 선택적으로 적용하는 옵션으로 두며, 기본 전제는 “원문 이미지를 기반으로 한다”이다.[web:2]

### 4.3 3단계: 모델 업그레이드 및 평가

- baseline 파이프라인이 구현·검증된 이후, 더 최신 SD 1.5 파생 모델/SDXL 계열로 확장하여 착시 품질과 자원 소모를 비교한다.[web:45][web:51]
- 모델 변경은 파이프라인 구조는 그대로 유지한 채, 베이스 모델·VAE·ControlNet 조합을 교체하는 방식으로 진행한다.

## 5. 작업 계획

### 5.1 단계별 작업

1. 코드 분석
   - 최신 Hugging Face `app.py` 확인 및 주요 함수/객체 정리.[web:9]
   - 모델/체크포인트 이름, 파이프라인 플로우 문서화.
2. 로컬/클라우드용 inference 스크립트 작성
   - `app.py`에서 Gradio/Spaces 부분 제거.
   - `inference()` 또는 유사 함수만 남긴 최소 실행 스크립트 작성.
   - CLI/파이썬 함수 형태의 간단한 인터페이스 제공 (예: `generate_illusion(...)`).
3. 베이스 이미지 구성 (1단계)
   - 원문 이미지(실세계/공개 라이선스 리소스 등)를 수집해, 별도 가공 없이 IllusionDiffusion 입력으로 사용.[web:2]
   - 숨은 콘텐츠 라벨(단어/오브젝트 이름)을 메타데이터로 관리.
4. 착시 이미지 배치 생성
   - 베이스 이미지별로 여러 시드를 사용해 착시 이미지 생성.
   - similarity 계산 및 최적 후보 선택 로직 구현.
5. CAPTCHA 포맷 설계
   - 문제 문장 템플릿, 선택지 구성 규칙 설계.
   - 결과를 JSON/이미지 파일 세트로 저장.
6. (후속) 2단계 아이코닉 실루엣 파이프라인 구현
   - 별도 섹션에 정의된 아이코닉 실루엣/심볼 세트를 베이스로 사용하는 파이프라인 추가.
7. (선택) LLM/비전 모델 평가
   - 프롬프트 템플릿 정의, 응답 파싱 로직 구성.

### 5.2 산출물

- 코드
  - `illusion_inference.py` : Gradio 제거한 순수 파이프라인 스크립트.
  - `captcha_generator.py` : 베이스 이미지 세트 + 일괄 착시 생성 + CAPTCHA 구성.
- 데이터
  - 생성된 착시 이미지 세트.
  - CAPTCHA 메타데이터(JSON): 정답/선택지/프롬프트/시드 등.
- 문서
  - 이 기획 문서 (`docs/plan_illusioncaptcha.md`).
  - 구현 상세 문서 (`docs/implementation_notes.md`).

## 6. 기술/환경 요구사항

- 하드웨어
  - Local: MacBook M4 Pro (Metal/MPS), 단일 이미지 테스트·디버깅용.[web:42]
  - Cloud: NVIDIA GPU (8–24GB VRAM) — Colab/RunPod 등, 대량 생성·SDXL 실험용.[web:35][web:51]
- 소프트웨어
  - Python 3.10±
  - PyTorch, diffusers, transformers, accelerate, safetensors, Pillow, opencv-python 등.
- 외부 의존성
  - Hugging Face 계정 (모델 다운로드 용도).
  - Stable Diffusion/ControlNet 체크포인트 접근 권한.

## 7. 모델 선택 및 자원/성능 평가 계획

### 7.1 베이스 모델 후보

- v1 (Baseline)
  - Realistic Vision V5.1 (SD 1.5 기반, `Realistic_Vision_V5.1_noVAE`).[web:45][web:52]
  - 장점: IllusionDiffusion Space와 동일 계열, 커뮤니티에서 이미지 품질 검증, SD 1.5 호환 ControlNet 사용.[web:13][web:45]
  - 자원: 8GB VRAM급 NVIDIA GPU에서 ControlNet 포함 512×512 inference 가능(일반적인 SD 1.5 + ControlNet 요구 수준 참고).[web:35]

- v2 (개선된 SD 1.5 계열)
  - Realistic Vision V6.0 등 최신 1.5 파생 체크포인트.[web:48][web:49]
  - 목표: 디테일, 노이즈, 텍스트/엣지 표현 품질 향상.

- v3 (SDXL 계열)
  - SDXL 1.0 및 파생 모델들.[web:51][web:54]
  - 목표: 1024 해상도 기준 이미지 품질·구성 능력 향상, 고해상도 CAPTCHA 생성 실험.
  - 제약: 더 높은 VRAM 요구, SDXL 전용 ControlNet 필요.[web:51]

### 7.2 자원 요구/테스트 플랜

- 환경 구분
  - Local (MacBook M4 Pro, Metal/MPS):
    - 역할: v1 파이프라인 개발/디버깅, 저해상도(≤512) 단일 샷 테스트.
    - 측정: 1장당 생성 시간, 통합 메모리 사용량, 안정성.
  - Cloud (Colab / RunPod, NVIDIA GPU 8–24GB VRAM):
    - 역할: 대량 CAPTCHA 생성, multi-seed sampling + similarity 필터링, v2/v3 실험.
    - 측정: 100/1000장 배치 생성 시간, GPU/VRAM 사용량, 실패율.

- 테스트 항목
  - 품질:
    - 인간 평가: 숨은 오브젝트/단어가 명확히 보이는지, 전경 장면 품질/자연스러움.
    - 자동 지표 후보: CLIPScore, 이미지 내 텍스트 인식률(OCR) 등.
  - 혼동도(LLM/비전 모델):
    - 같은 베이스에 대해 v1/v2/v3로 생성한 CAPTCHA의 LLM/비전 모델 정답률 비교.[web:2][web:60]
  - 자원:
    - 모델·해상도별 1장당 평균 inference 시간, peak 메모리, 오류 발생률.

## 8. 아이코닉 실루엣 기반 숨은 이미지 파이프라인 (후속 단계)

- 숨은 콘텐츠 정의
  - 사람 기준으로 실루엣만 보아도 무엇인지 즉시 인지 가능한 아이코닉 오브젝트 리스트 구성 (예: 동물 실루엣, 상징적인 사물, 간단한 로고 형태).[web:2][web:75]
- 베이스 이미지 제작 및 QC (옵션)
  - 각 오브젝트를 고대비 실루엣/심볼 이미지로 제작하는 것은 선택적이며, 필요 시 적용.
  - 사람이 직접 검수해 “단독으로 봤을 때 무엇인지 1초 내 인지 가능”한 이미지만 채택.
- IllusionDiffusion 통합
  - 이 실루엣/아이코닉 이미지를 IllusionDiffusion 입력 이미지로 사용하고, 착시용 프롬프트를 설정해 multi-seed로 candidate 생성.[web:9][web:13]
  - similarity 계산 및 사람이 보는 QC를 조합해, 숨은 오브젝트가 유지되면서도 배경에 잘 섞인 seed·이미지만 최종 CAPTCHA 세트에 포함.[web:2]

## 9. 참고 링크 요약

- Illusionary CAPTCHA: https://sites.google.com/view/illusionarycaptcha[web:1]  
- IllusionCAPTCHA 논문(arXiv): https://arxiv.org/abs/2502.05461[web:60]  
- IllusionCAPTCHA 논문(HTML): https://arxiv.org/html/2502.05461v1[web:2]  
- IllusionDiffusion Space: https://huggingface.co/spaces/AP123/IllusionDiffusion[web:13]  
- IllusionDiffusion app.py: https://huggingface.co/spaces/AP123/IllusionDiffusion/blob/main/app.py[web:9]  
- Diffusion Illusions: https://diffusionillusions.com[page:3]  
- Visual Anagrams 코드: https://github.com/dangeng/visual_anagrams[web:14]  
- Color Visual Illusions and Diffusion Models (HTML): https://arxiv.org/html/2412.10122v1[web:10]
