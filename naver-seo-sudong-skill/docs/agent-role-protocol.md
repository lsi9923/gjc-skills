# 네이버 스마트스토어 상위노출 수동등록 다중 에이전트 역할 분담 프로토콜 (RACI)

---

## 1. 개요 및 설계 목적
1688, 타오바오 등 해외 소싱 상품을 네이버 스마트스토어에 수동 등록할 때, 셀러 1인이 감당해야 하는 20개 필수 항목 작성 및 네이버 상위노출 SEO 규칙(카테고리 1.0 실측, 25~30자 상품명, 인덱서 형태소, 태그 사전 등) 검증 부담을 **4대 전문 에이전트와 브라우저 브릿지**로 분업화하여 **등록 시간을 상품당 30분 -> 2분으로 단축**하고 알고리즘 컷오프를 원천 차단한다.

---

## 2. 역할 분담 및 책임 매트릭스 (RACI Matrix)

| 구분 | 인간 셀러 (Supervisor) | Agent 1: 소싱/스펙 분석기 | Agent 2: 네이버 SEO 실측기 | Agent 3: 스마트스토어 폼 작성기 | Agent 4: 브라우저 Auto-fill 브릿지 |
|---|:---:|:---:|:---:|:---:|:---:|
| **소싱 상품 선정** | **Accountable (A)** | Informed (I) | - | - | - |
| **상품 스펙/속성 추출** | - | **Responsible (R)** | Consulted (C) | Informed (I) | - |
| **카테고리 1.0 실측** | - | - | **Responsible (R)** | - | Informed (I) |
| **25~30자 상품명 조합** | - | - | **Responsible (R)** | Consulted (C) | Informed (I) |
| **태그 10개 확정** | - | - | **Responsible (R)** | - | Informed (I) |
| **판매가/마진 계산** | Consulted (C) | Informed (I) | - | **Responsible (R)** | - |
| **상세페이지 스토리보드** | - | Consulted (C) | - | **Responsible (R)** | - |
| **20개 항목 종합 페이로드** | - | - | - | **Responsible (R)** | Consulted (C) |
| **스마트스토어 폼 자동입력** | - | - | - | Informed (I) | **Responsible (R)** |
| **최종 검수 및 저장 클릭** | **Accountable (A)** | - | - | - | - |

* **R (Responsible)**: 실제 작업을 수행하는 주체
* **A (Accountable)**: 최종 승인 및 책임을 지는 주체 (인간 셀러)
* **C (Consulted)**: 작업 수행에 필요한 정보/의견을 제공하는 주체
* **I (Informed)**: 작업 결과를 통보받아 다음 단계에 활용하는 주체

---

## 3. 4대 에이전트 세부 역할 및 입출력 계약 (Contracts)

### [Agent 1] 소싱 및 스펙 분석 에이전트 (`sourcing-analyzer`)
* **역할**: 1688/타오바오 상품 상세페이지(DOM/텍스트/이미지)에서 핵심 스펙과 셀링 포인트를 추출한다.
* **입력**: 상품 소싱 URL 또는 텍스트/스펙 데이터
* **출력 데이터 (`SourcingSpecOutput`)**:
  ```json
  {
    "rawTitle": "원문 상품명",
    "cnyPrice": 25.5,
    "specs": {
      "material": "네오프렌, 통기성 메쉬",
      "size": ["M", "L", "XL"],
      "color": ["블랙", "레드", "블루"],
      "weight": "85g",
      "keyFeatures": ["충격흡수 젤패드", "터치스크린 인식", "미끄럼방지 실리콘"]
    },
    "candidateMainKeywords": ["자전거장갑", "라이딩장갑", "싸이클장갑"]
  }
  ```

---

### [Agent 2] 네이버 SEO 실측 및 최적화 에이전트 (`naver-seo-probe`)
* **역할**: 네이버쇼핑 검색엔진의 실시간 원천 데이터(`cmp`, `relatedQueries`, `idxTerm`)를 추출하여 GBDT 1위 카테고리와 25~30자 상품명을 확정한다.
* **입력**: `candidateMainKeywords` (후보 메인 키워드)
* **출력 데이터 (`NaverSeoOutput`)**:
  ```json
  {
    "category": {
      "path": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
      "relevance": 1.000,
      "category1": "스포츠/레저",
      "category2": "자전거",
      "category3": "자전거의류/잡화",
      "category4": "장갑"
    },
    "titles": {
      "titleA": "자전거장갑 여름 바이크 장갑 라이딩 장갑 자전거 반장갑",
      "lengthA": 30,
      "titleB": "여름 바이크 장갑 자전거장갑 라이딩 장갑 사이클 반장갑",
      "lengthB": 29
    },
    "relatedKeywords": ["라이딩 장갑", "겨울 자전거 장갑", "시마노 자전거 장갑"],
    "indexerTerms": ["자전거", "장갑", "라이딩", "싸이클"],
    "tags": ["자전거장갑", "라이딩장갑", "여름바이크장갑", "자전거반장갑", "싸이클장갑", "로드자전거장갑", "산악자전거장갑", "MTB장갑", "터치장갑", "통기성장갑"]
  }
  ```

---

### [Agent 3] 스마트스토어 리스팅 컴포저 (`smartstore-composer`)
* **역할**: 소싱 스펙과 SEO 실측 데이터를 결합하여 스마트스토어 센터 등록에 필요한 20개 항목 완성형 페이로드를 생성한다.
* **입력**: `SourcingSpecOutput` + `NaverSeoOutput` + 판매자 기본 고정정보
* **출력 데이터 (`SmartStoreListingPayload`)**:
  ```json
  {
    "category": "스포츠/레저 > 자전거 > 자전거의류/잡화 > 장갑",
    "productName": "자전거장갑 여름 바이크 장갑 라이딩 장갑 자전거 반장갑",
    "salePrice": 14900,
    "stockQuantity": 999,
    "options": [
      { "groupName": "색상", "values": ["블랙", "레드", "블루"] },
      { "groupName": "사이즈", "values": ["M", "L", "XL"] }
    ],
    "tags": ["자전거장갑", "라이딩장갑", "여름바이크장갑", "자전거반장갑", "싸이클장갑", "로드자전거장갑", "산악자전거장갑", "MTB장갑", "터치장갑", "통기성장갑"],
    "detailHtml": "<div class='detail-wrap'>...후킹 문구 -> 3대 특장점 -> 상세 스펙표 -> 배송안내...</div>",
    "shipping": {
      "feeType": "PAID",
      "fee": 3500,
      "returnFee": 3500,
      "exchangeFee": 7000,
      "outboundAddress": "인천광역시 검단구 완정로 146 (리더스빌) 2층 208-43c호 (23466)"
    },
    "seo": {
      "pageTitle": "자전거장갑 여름 바이크 라이딩 반장갑 - 스마트스토어",
      "metaDescription": "충격흡수 젤패드와 통기성 메쉬를 갖춘 최상급 라이딩 자전거장갑"
    }
  }
  ```

---

### [Agent 4] 브라우저 현장 HUD & Auto-fill 브릿지 (`browser-autofill-bridge`)
* **역할**:
  1. 네이버쇼핑 검색창: 카테고리 1.0 및 추천 키워드 실시간 HUD 제공
  2. 스마트스토어 센터 등록창(`sell.smartstore.naver.com/#/products/create`): 플로팅 패널에 `SmartStoreListingPayload` JSON을 원클릭으로 붙여넣으면 각 DOM 폼 필드에 값을 자동 주입(Auto-fill).

---

## 4. 단계별 핸드오프 시퀀스 (Execution Pipeline)

```text
[인간 셀러] 1688 소싱 상품 URL 결정
     │
     ▼
[Agent 1: sourcing-analyzer]
스펙 및 핵심 속성 추출 -> candidateMainKeywords 도출
     │
     ▼
[Agent 2: naver-seo-probe]
네이버쇼핑 CDP 실측 -> 카테고리 1.0 락온, 25~30자 상품명, 태그 10개 확정
     │
     ▼
[Agent 3: smartstore-composer]
20개 항목 완성형 페이로드(SmartStoreListingPayload JSON) 일괄 생성
     │
     ▼
[Agent 4: browser-autofill-bridge]
스마트스토어 등록센터 페이지에서 원클릭 Auto-fill 버튼 실행 -> 폼 자동 채움
     │
     ▼
[인간 셀러]
화면 최종 육안 점검 후 "저장하기" 클릭 완료!
```
