# GJC (Gajae-Code) AI Agent Production Skills Collection

350개 이상의 한국 이커머스(스마트스토어·쿠팡·1688), KIPRIS 상표권 검색, SEO 최적화, 딥 리서치 및 시스템 자동화 전문 GJC 에이전트 스킬 컬렉션입니다.

---

## 🌟 주요 핵심 스킬

### 1. 해외구매대행 & 사입 전문 큐레이션 (`sourcing-top50-curator`)
- **경로**: `sourcing-top50-curator/`
- **주요 기능**:
  - `ProductIdeaRadar` 데이터 기반 실물 유망 상품 자동 선별 및 4개 시트 엑셀 자동 빌드
  - **특허청 KIPRIS 공식 웹사이트 상표권 직결 검색** (네이버 검색 완전 배제)
  - **상품 이미지 기반 딥 리서치 엔진 (`product_image_deep_research.py`)**: 텍스트 검색 실패 시 썸네일·대표 이미지를 자동 추출하여 비전 판독 및 1688 중국어 검색어, 1688 이미지 검색(拍立淘) 프로토콜, 원가 마진 40%+ 리포트 생성
  - 1688 중국 공장 왕왕/위챗 직발송용 중문+한국어 문의 메시지 자동 작성
  - KC인증, 식약처 식품기구 수입신고, 생활화학제품 고시 우회 및 최소비용 인증 전략 탑재

### 2. 네이버 스마트스토어 & 쿠팡 윙 통합 실전 상품 등록 (`naver-coupang-register`)
- **경로**: `naver-coupang-register/`
- **주요 기능**:
  - 상세페이지 메이커 완료폴더(`완료된폴더/<N>`) 기반 원클릭 상품 등록 플랜 생성
  - 네이버 F12 실시간 카테고리/태그 정밀 검증 및 이호 5분류 SEO 상품명 빌드
  - 쿠팡 윙 카테고리 매핑, 노출 상품명, 검색어 조립
  - 최종 등록 확인표 생성 및 판매자센터 자동화

### 3. 특허청 공식 상표권 직접 검색 (`korean-patent-search`)
- **경로**: `korean-patent-search/`
- **주요 기능**:
  - 특허청 KIPRIS Plus 공식 API 및 KIPRIS 공식 웹 다이렉트 쿼리 연동
  - `trademark_search.py`: 키워드별 등록 상표, 출원번호, 등록상태, 출원인, 상품분류(Nice 류) 실시간 조회

### 4. 이커머스 수동 등록 및 랭킹 추적
- `naver-seo-sudong-skill/`: 네이버 쇼핑 수동 등록 가이드라인 및 고시
- `coupang-sudong-skill/`: 쿠팡 윙 수동 등록 및 옵션 매핑
- `naver-shopping-listing/` & `naver-rank-probe/`: 네이버 쇼핑 노출 순위 실시간 프로브

### 5. 딥 리서치 & 분석
- `deep-research/`, `insane-research/`: 광범위 웹 리서치 및 크로스 검증

---

## 📜 사용자 영구 지침 (Global Guidelines)
- 본 저장소의 `AGENTS.md`를 통해 모든 AI 세션에서 아래 원칙이 영구 강제됩니다:
  1. **KIPRIS 상표권 공식 직접 검색 절대 준수 (네이버 검색 절대 금지)**
  2. **상품 텍스트 검색 실패 시 이미지 추출 & 비전 딥 리서치(Deep Research) 의무 실행**
  3. **답변 종료 시 토큰 & 쿼터 현황 상시 표기**
