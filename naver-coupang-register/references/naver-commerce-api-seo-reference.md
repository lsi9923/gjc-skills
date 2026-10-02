# NAVER Commerce API — SEO-Relevant Field Reference

**Endpoint:** `POST https://api.commerce.naver.com/external/v2/products`  
**API Docs:** https://apicenter.commerce.naver.com/ko/basic/commerce-api (v2.83.0 as of 2026-07-21)  
**GitHub Support:** https://github.com/commerce-api-naver/commerce-api

> This document covers every field in the `originProduct` + `smartstoreChannelProduct` request body that affects Naver Shopping search exposure / SEO.

---

## 1. `originProduct.name` — 상품명

| Property | Value |
|----------|-------|
| JSON path | `originProduct.name` |
| Type | `string` |
| Required | **Yes** |
| Max length | **100 characters** (공백 포함) |
| Forbidden chars | `< > \\ ' " { }` and 기타 HTML-special characters are rejected at registration. The Smartstore FAQ "상품등록 시 제한되는 특수문자는 무엇인가요?" documents the restricted set. |

**Source:** Smartstore FAQ (https://help.sell.smartstore.naver.com/faq/content.help — "상품등록 시 제한되는 특수문자는 무엇인가요?"), confirmed by working API payloads (https://santapia.tistory.com/81)

### 네이버 쇼핑 상품명 작성 가이드 (검색품질/SEO 규칙)

The Smartstore Seller Center has a dedicated menu "상품정보 검색품질(SEO)" and FAQ items "상품명 등록 기준을 알고 싶어요" and "검색설정 등록 시 유의사항을 알려주세요":

**Source:** https://help.sell.smartstore.naver.com — 상품관리 > 상품정보 검색품질(SEO), 상품 등록 > "상품명 등록 기준을 알고 싶어요"

| Rule | Detail |
|------|--------|
| Recommended structure | `[브랜드명] + [고유 상품명/모델명] + [핵심속성(색상/사이즈/소재 등)]` |
| Keyword stuffing prohibition | 동일 키워드 반복, 무관한 키워드 나열, 경쟁사 브랜드명 삽입 시 **검색 노출 제외** 조치 |
| Forbidden content | 판매조건(무료배송, 할인율, 1+1), 홍보문구, 특수문자 남용(★♥●), 검색용 유사어 나열 |
| Language | 한글/영문/숫자 혼용 가능. 일본어·중국어 등 비한글 문자 단독 사용 시 검색 불이익 가능 |
| Penalty | 위반 시 네이버쇼핑 검색 결과에서 노출 제외 또는 순위 하락 (내부 검색품질 점수 감산) |
| Best practice | 핵심 키워드를 앞쪽 배치, 50자 이내 권장 (100자 가능하나 짧을수록 유리), 띄어쓰기 정상 사용 |

> ⚠️ UNVERIFIED precise char: 공식 API 문서에서 "100자"라는 정확한 숫자를 직접 확인하지 못함. 실무적으로 100 bytes UTF-8 또는 100 chars 한글 기준이 통용됨. 스마트스토어 UI에서는 100자로 제한 표시.

---

## 2. `originProduct.detailAttribute.seoInfo`

| JSON path | Type | Required | Limits | SEO Impact |
|-----------|------|----------|--------|------------|
| `.seoInfo.pageTitle` | `string` | Optional | **최대 60자** (UNVERIFIED exact — UI 기준) | 스마트스토어 상품 페이지 `<title>` 태그에 반영. 검색엔진 노출 제목. |
| `.seoInfo.metaDescription` | `string` | Optional | **최대 160자** (UNVERIFIED exact — UI 기준) | 스마트스토어 상품 페이지 `<meta name="description">` 태그에 반영. 네이버 검색 스니펫. |
| `.seoInfo.sellerTags[]` | `array of object` | Optional | **최대 10개** | 네이버 쇼핑 검색에서 태그 기반 검색 매칭에 사용 |

### `sellerTags` 객체 구조

```json
{
  "code": 308797,   // number, optional — 기존 등록된 태그의 code (수정 시 유지용)
  "text": "천장몰딩" // string, required — 태그 텍스트
}
```

| Field | Type | Required | Limits |
|-------|------|----------|--------|
| `code` | `integer` | Optional | 기존 태그 code. 신규 등록 시 미입력 가능, 서버가 자동 부여 |
| `text` | `string` | **Yes** | 최대 **20자**, 특수문자/공백 제한, 한글·영문·숫자 |

**Source:** Working API payload confirmed from https://santapia.tistory.com/81 showing `sellerTags` with `code` + `text` structure. Smartstore FAQ "태그는 직접입력형으로 몇개까지 설정 가능한가요?" confirms 10개 제한. FAQ "검색설정 등록 시 유의사항을 알려주세요" and "등록한 '태그'로 검색 시 상품이 검색되지 않아요" cover tag rules.

### 태그 사용 규칙 (검색품질)

- 상품과 **직접 관련 있는 키워드**만 사용
- 상품명에 이미 포함된 키워드를 중복 태그로 넣어도 추가 이점 없음
- 무관한 인기 키워드 삽입 시 검색 품질 페널티
- 경쟁 브랜드명, 타 상품명 등 부정 키워드 사용 금지
- FAQ "태그 등록 시 태그명 옆 번호는 왜 노출되나요?" → `code`는 시스템 내부 식별자

---

## 3. `originProduct.detailAttribute.naverShoppingSearchInfo`

가격비교(Price Comparison) 매칭에 직접 사용되는 필드.

| JSON path | Type | Required | Max length | SEO Impact |
|-----------|------|----------|------------|------------|
| `.naverShoppingSearchInfo.manufacturerName` | `string` | Optional* | UNVERIFIED (추정 100자) | 네이버쇼핑 제조사 필터 매칭 |
| `.naverShoppingSearchInfo.brandName` | `string` | Optional* | UNVERIFIED (추정 100자) | 네이버쇼핑 브랜드 필터 + 가격비교 매칭 핵심 |
| `.naverShoppingSearchInfo.modelName` | `string` | Optional* | UNVERIFIED (추정 100자) | 카탈로그(가격비교) 매칭의 핵심 식별자 |

> *Optional이지만, 가격비교 노출을 원하면 사실상 **필수**

**Source:** GitHub Discussion #2061 (https://github.com/commerce-api-naver/commerce-api/discussions/2061) — 공식 답변: "상품 등록/수정 시 네이버쇼핑 등록 여부(`naverShoppingRegistration`) 필드 값을 `true`로 설정하는 경우 '가격비교 사이트 등록' 신청 및 네이버 쇼핑에 상품이 노출됩니다." Smartstore FAQ "네이버쇼핑에 '가격비교 매칭'은 어떻게 요청 하나요?" (faqId=15553) confirms brand+model matching.

### 가격비교 매칭 메커니즘

1. `brandName` + `modelName` 조합으로 네이버쇼핑 카탈로그 DB에서 매칭 시도
2. 매칭 성공 시 → 가격비교 페이지에 해당 상품 노출 (동일 카탈로그 상품들과 가격 경쟁)
3. `manufacturerName`은 부가 필터용
4. GitHub Discussion #2127 확인: 동일 브랜드+모델명에 다수 카탈로그 ID 존재 가능 (속성 차이)

> ⚠️ `seriesName` 필드 존재 여부: UNVERIFIED — 공식 문서에서 직접 확인 불가. 일부 커뮤니티에서 언급되나 현재 API v2에서 실제 존재하는지 확인 필요.



---

## 4. `originProduct.detailAttribute.productInfoProvidedNotice` — 품목별 상품정보 제공고시

전자상거래법에 따른 필수 고시정보. 미입력 시 상품 등록 자체가 거부되거나 네이버쇼핑 노출 제한.

### Wrapper 구조

```json
{
  "productInfoProvidedNotice": {
    "productInfoProvidedNoticeType": "FURNITURE",
    "furniture": {
      "itemName": "상품상세참조",
      "material": "상품상세참조",
      ...
    }
  }
}
```

| JSON path | Type | Required |
|-----------|------|----------|
| `.productInfoProvidedNotice.productInfoProvidedNoticeType` | `string` (enum) | **Yes** |
| `.productInfoProvidedNotice.<typeKey>` | `object` | **Yes** — enum 값에 대응하는 키로 실제 고시항목 입력 |

### `productInfoProvidedNoticeType` Enum Values

아래는 공식 API 문서 및 실제 동작 확인된 enum 값 목록:

| Enum Value | 한글명 | typeKey (JSON property) |
|------------|--------|------------------------|
| `WEAR` | 의류 | `wear` |
| `SHOES` | 구두/신발 | `shoes` |
| `BAG` | 가방 | `bag` |
| `FASHION_ITEMS` | 패션잡화(모자/벨트/액세서리) | `fashionItems` |
| `SLEEPING_GEAR` | 침구류/커튼 | `sleepingGear` |
| `FURNITURE` | 가구(침대/소파/싱크대/DIY제품) | `furniture` |
| `IMAGE_APPLIANCES` | 영상가전(TV류) | `imageAppliances` |
| `HOME_APPLIANCES` | 가정용 전기제품(냉장고/세탁기/식기세척기/전자레인지) | `homeAppliances` |
| `SEASON_APPLIANCES` | 계절가전(에어컨/온풍기) | `seasonAppliances` |
| `OFFICE_APPLIANCES` | 사무용기기(컴퓨터/노트북/프린터) | `officeAppliances` |
| `OPTICS_APPLIANCES` | 광학기기(디지털카메라/캠코더) | `opticsAppliances` |
| `MICRO_ELECTRONICS` | 소형전자(MP3/전자사전 등) | `microElectronics` |
| `NAVIGATION` | 내비게이션 | `navigation` |
| `CAR_ARTICLES` | 자동차용품(자동차부품/기타) | `carArticles` |
| `MEDICAL_APPLIANCES` | 의료기기 | `medicalAppliances` |
| `KITCHEN_UTENSILS` | 주방용품 | `kitchenUtensils` |
| `COSMETIC` | 화장품 | `cosmetic` |
| `JEWELLERY` | 귀금속/보석/시계 | `jewellery` |
| `FOOD` | 식품(농산물/축산물/수산물) | `food` |
| `GENERAL_FOOD` | 가공식품 | `generalFood` |
| `HEALTH_FUNCTIONAL_FOOD` | 건강기능식품 | `healthFunctionalFood` |
| `KIDS` | 어린이제품 | `kids` |
| `MUSICAL_INSTRUMENT` | 악기 | `musicalInstrument` |
| `SPORTS_EQUIPMENT` | 스포츠용품 | `sportsEquipment` |
| `BOOKS` | 서적 | `books` |
| `RENTAL_ETC` | 물품대여 서비스(정수기/비데 등) | `rentalEtc` |
| `DIGITAL_CONTENTS` | 디지털 콘텐츠(음원/게임/인터넷강의 등) | `digitalContents` |
| `GIFT_CARD` | 상품권/쿠폰 | `giftCard` |
| `MOBILE_COUPON` | 모바일쿠폰 | `mobileCoupon` |
| `MOVIE_SHOW` | 영화/공연 | `movieShow` |
| `ETC_SERVICE` | 기타 용역 | `etcService` |
| `BIOCHEMISTRY` | 생활화학제품 및 살생물제 | `biochemistry` |
| `BIOCIDAL` | 살생물제품 | `biocidal` |
| `CELLPHONE` | 휴대폰 | `cellphone` |
| `ETC` | 기타 재화 | `etc` |

> ⚠️ 일부 enum값은 UNVERIFIED (API 버전별 추가/변경 가능). 위 목록은 공식 문서 + 커뮤니티 확인 기반. 정확한 최신 목록은 `apicenter.commerce.naver.com` 공식 스키마 참조 필요.

**Source:** Confirmed `FURNITURE` from actual working payload (https://santapia.tistory.com/81). Enum list derived from 전자상거래법 품목별 고시 표준 + API 커뮤니티 사용례.

### 가구(FURNITURE) 필수 키

```json
"furniture": {
  "itemName": "string",           // 품명
  "material": "string",           // 소재 (천연/인조가죽, 합판 등)
  "color": "string",              // 색상
  "components": "string",         // 구성품
  "size": "string",               // 크기
  "manufacturer": "string",       // 제조자/수입자
  "importer": "string",           // 수입자 (해외 제품 시)
  "producer": "string",           // 제조국
  "certificationType": "string",  // 품질보증기준
  "installedCharge": "string",    // 배송/설치비용
  "warrantyPolicy": "string",     // 품질보증기준
  "afterServiceDirector": "string", // A/S 책임자/전화번호
  "returnCostReason": "string",   // 교환/반품 비용 부담 조건 (0 = 상품상세참조)
  "noRefundReason": "string",     // 교환/반품 불가 사유 (0 = 상품상세참조)
  "qualityAssuranceStandard": "string", // 품질보증기준 (0 = 상품상세참조)
  "compensationProcedure": "string",    // 보상기준 (0 = 상품상세참조)
  "troubleShootingContents": "string"   // 불만/분쟁처리 (0 = 상품상세참조)
}
```

### 기타 재화(ETC) 필수 키

```json
"etc": {
  "itemName": "string",           // 품명
  "modelName": "string",          // 모델명
  "certificationType": "string",  // 법에 의한 인증·허가 등
  "manufacturer": "string",       // 제조자/수입자
  "afterServiceDirector": "string", // A/S 책임자/전화번호
  "returnCostReason": "string",
  "noRefundReason": "string",
  "qualityAssuranceStandard": "string",
  "compensationProcedure": "string",
  "troubleShootingContents": "string"
}
```

> 공통 패턴: `returnCostReason`, `noRefundReason`, `qualityAssuranceStandard`, `compensationProcedure`, `troubleShootingContents`는 거의 모든 타입에 공통 존재. 값으로 `"0"` 입력 시 "상품상세참조"로 처리.



---

## 5. `originProduct.detailAttribute.productAttributes` — 상품 속성

카테고리별로 정의된 상품 속성(색상, 소재, 사이즈 등)을 구조화하여 입력. **네이버쇼핑 필터 검색의 핵심.**

### 구조

```json
"productAttributes": [
  {
    "attributeSeq": 12345,           // number — 속성 ID (필수)
    "attributeValueSeq": 67890,      // number — 속성값 ID (사전정의 값 선택 시)
    "attributeRealValue": "커스텀값",  // string — 직접입력값 (realValueUsable=true 속성용)
    "attributeValueId": "string"     // string — 속성값 식별자 (일부 속성에서 사용)
  }
]
```

| Field | Type | When to use |
|-------|------|-------------|
| `attributeSeq` | `integer` | 항상 필수. 카테고리별 조회 API로 획득 |
| `attributeValueSeq` | `integer` | 사전 정의된 선택지 중 고를 때 |
| `attributeRealValue` | `string` | 직접 입력이 허용된 속성(`realValueUsable: true`)에서 자유 텍스트 입력 |
| `attributeValueId` | `string` | 일부 속성(브랜드 등)에서 사용하는 식별자 |

### 카테고리별 속성 조회 API

```
GET https://api.commerce.naver.com/external/v1/product-attributes/categories/{categoryId}
```

**또는** (표준옵션 조회):
```
GET https://api.commerce.naver.com/external/v1/product-attributes/standard-options/categories/{categoryId}
```

**Source:** Context7 docs (https://context7.com/websites/apicenter_commerce_naver) — "Get Standard Option By Category" endpoint confirmed. Response 예시:
```json
[{
  "useStandardOption": true,
  "standardOptionCategoryGroups": [{
    "attributeId": 0,
    "attributeName": "string",
    "groupName": "string",
    "imageRegistrationUsable": true,
    "realValueUsable": true,
    "optionSetRequired": true,
    "standardOptionAttributes": [{
      "attributeId": 0,
      "attributeValueId": 0,
      "attributeValueName": "string",
      "attributeColorCode": "string",
      "imageUrls": ["string"]
    }]
  }]
}]
```

### 카테고리 목록 조회

```
GET https://api.commerce.naver.com/external/v1/categories
```

Returns: `[{ "wholeCategoryName": "string", "id": "string", "name": "string", "last": true }]`

**Source:** Context7 docs confirmed endpoint and response shape.

### SEO 영향

- 속성을 정확히 채울수록 네이버쇼핑 **필터 검색**(색상별, 사이즈별, 소재별 등)에 노출
- 필수 속성 미입력 시 해당 필터에서 제외 → 검색 노출 기회 감소
- `optionSetRequired: true`인 속성은 반드시 옵션과 매핑해야 정상 노출

---

## 6. `originProduct.detailAttribute.originAreaInfo` — 원산지 정보

```json
"originAreaInfo": {
  "originAreaCode": "00",    // string — 원산지 코드 ("00"=국산, "02"=수입 등)
  "content": "국산",          // string — 원산지 표기 텍스트
  "plural": false            // boolean — 복수 원산지 여부
}
```

| Field | Type | Required | Note |
|-------|------|----------|------|
| `originAreaCode` | `string` | Yes | "00"=국산, "02"=중국, "03"=미국... 코드표 별도 |
| `content` | `string` | Yes | 실제 표시 텍스트 |
| `plural` | `boolean` | Yes | 원산지가 여러 곳이면 `true` |

**SEO 영향:** 네이버쇼핑에서 "국산" 필터 매칭. 원산지 허위기재 시 상품 노출 정지.

**Source:** Confirmed from working payload (https://santapia.tistory.com/81), GitHub Discussion #2127 답변에서 `originProduct.detailAttribute.originAreaInfo` 언급.

---

## 7. `originProduct.detailAttribute.afterServiceInfo` — A/S 정보

```json
"afterServiceInfo": {
  "afterServiceTelephoneNumber": "063-262-2539",  // string, required
  "afterServiceGuideContent": "A/S안내"            // string, optional
}
```

| Field | Type | Required | Max length |
|-------|------|----------|------------|
| `afterServiceTelephoneNumber` | `string` | **Yes** | UNVERIFIED (전화번호 형식) |
| `afterServiceGuideContent` | `string` | Optional | UNVERIFIED (추정 최대 1000자) |

**SEO 영향:** 직접적 검색 영향은 적으나, 필수 입력 미비 시 상품 등록 실패 또는 네이버쇼핑 노출 제한.

---

## 8. 인증 관련 필드

### `certificationTargetExcludeContent`

```json
"certificationTargetExcludeContent": {
  "kcCertifiedProductExclusionYn": "TRUE"  // "TRUE" | "FALSE"
}
```

KC인증 대상 제외 여부. `"TRUE"` = 인증 대상 아님 선언.

### `productCertifications` (UNVERIFIED field name)

KC인증 정보 배열. 카테고리에 따라 필수.

```json
"productCertifications": [
  {
    "certificationInfoId": "string",
    "certificationKindType": "string",  // KC_CERTIFICATION, CHILDREN_CERTIFICATION 등
    "name": "string",
    "certificationNumber": "string"
  }
]
```

> ⚠️ UNVERIFIED: 정확한 field name은 `productCertifications` 또는 `certificationInfo`일 수 있음. 공식 스키마 확인 필요.

### `minorPurchasable`

```json
"minorPurchasable": true  // boolean
```

미성년자 구매 가능 여부. `false`로 설정 시 19세 미만 구매 차단. 주류/담배 등 카테고리에서 필수.

**SEO 영향:** 직접적 검색 영향 없으나, 미입력 시 카테고리별 등록 거부 가능.

**Source:** Confirmed from working payload (https://santapia.tistory.com/81): `"minorPurchasable":true`

---

## 9. `originProduct.detailAttribute.optionInfo` — 옵션 정보

```json
"optionInfo": {
  "simpleOptionSortType": "CREATE",
  "optionSimple": [],
  "optionCustom": [],
  "optionCombinationSortType": "CREATE",
  "optionCombinationGroupNames": {
    "optionGroupName1": "색상",
    "optionGroupName2": "사이즈"    // 최대 3개 그룹
  },
  "optionCombinations": [
    {
      "id": "",
      "optionName1": "중백색",
      "stockQuantity": 999,
      "price": 0,
      "usable": true
    }
  ],
  "standardOptionGroups": [],
  "useStockManagement": true,
  "optionDeliveryAttributes": []
}
```

### 검색 관련 제약

| Constraint | Value |
|-----------|-------|
| 옵션 그룹 수 | 최대 **3개** (`optionGroupName1` ~ `optionGroupName3`) |
| 조합형 옵션 수 | 최대 **500개** 조합 (Smartstore FAQ "상품의 옵션은 몇 개까지 등록 가능한가요?" 참조) |
| 옵션명 길이 | 최대 **25자** (FAQ "옵션 등록 시 글자수에 제한이 있나요?" 참조) |
| 표준옵션 연동 | `standardOptionGroups`로 네이버 표준옵션 코드 매핑 시 필터 검색 정확도 향상 |

**SEO 영향:**
- 표준옵션(`standardOptionGroups`)을 사용하면 네이버쇼핑 사이즈/색상 필터에 정확히 매칭
- 옵션명에 키워드를 자연스럽게 포함하면 상세 검색 매칭 가능
- 품절 옵션(`usable: false`)이 과다하면 상품 품질 점수 하락 가능

**Source:** Confirmed structure from https://santapia.tistory.com/81

---

## 10. `smartstoreChannelProduct` — 스마트스토어 채널 설정

### 핵심 SEO 필드

```json
"smartstoreChannelProduct": {
  "naverShoppingRegistration": true,
  "channelProductDisplayStatusType": "ON",
  "storeKeepExclusiveProduct": false
}
```

| JSON path | Type | Required | Values | SEO Impact |
|-----------|------|----------|--------|------------|
| `.naverShoppingRegistration` | `boolean` | **Yes** | `true` / `false` | **`true`여야 네이버쇼핑에 상품 노출 + 가격비교 등록 신청됨** |
| `.channelProductDisplayStatusType` | `string` | Yes | `"ON"` / `"OFF"` / `"SUSPENSION"` | `"ON"`이어야 스토어 및 검색에 전시 |
| `.storeKeepExclusiveProduct` | `boolean` | Optional | `true` / `false` | `true` = 스토어 단독 전시 (네이버쇼핑 검색 미노출). 스토어킵 전용 상품 |

**Source:** GitHub Discussion #2061 (https://github.com/commerce-api-naver/commerce-api/discussions/2061) — 공식 Maintainer 답변:
> "상품 등록/수정 시 네이버쇼핑 등록 여부(`naverShoppingRegistration`) 필드 값을 `true`로 설정하는 경우 '가격비교 사이트 등록' 신청 및 네이버 쇼핑에 상품이 노출됩니다."
> - `smartstoreChannelProduct.naverShoppingRegistration`: 스마트스토어 채널상품의 가격비교 사이트 등록 여부
> - `windowChannelProduct.naverShoppingRegistration`: 쇼핑윈도 채널상품의 가격비교 사이트 등록 여부

**추가 필드 (SEO 간접 영향):**

| Field | Description |
|-------|-------------|
| `channelProductDisplayStatusType` | `"ON"` = 전시중, `"OFF"` = 전시중지, `"SUSPENSION"` = 판매중지. OFF/SUSPENSION 시 검색 미노출 |
| `storeKeepExclusiveProduct` | 스토어킵 단독 상품 여부. `true` 시 네이버쇼핑 통합검색에서 제외됨 |

> 네이버쇼핑 반영 소요시간: 등록/수정 후 약 **2~8시간**, 지연 시 최대 **1~2일** (공식 답변)

---

## 11. 검색품질/SEO 가이드라인 종합 (네이버 쇼핑 파트너)

**Source:** Smartstore Seller Center FAQ 메뉴 구조 (https://help.sell.smartstore.naver.com) — "상품정보 검색품질(SEO)" 전용 섹션 + "검색 순위 진단" 메뉴 존재 확인.

### 카테고리 적합도

- 상품을 **가장 하위(leaf) 카테고리**에 정확히 등록해야 검색 노출 최적화
- 잘못된 카테고리 등록 시 검색 순위 하락 또는 노출 제외
- API에서는 `originProduct.leafCategoryId`로 지정
- 카테고리 조회: `GET /v1/categories` → `last: true`인 항목이 leaf 카테고리

### 상품명 (반복)

- **구조:** `브랜드 + 고유상품명 + 주요속성`
- **금지:** 키워드 스터핑, 특수문자 남용, 홍보문구, 무관 키워드
- **페널티:** 네이버쇼핑 검색 노출 제외

### 태그 (sellerTags)

- 최대 10개, 각 20자 이내
- 상품과 직접 관련 있는 검색어만 사용
- HOT 태그 추천 기능 존재 (스마트스토어 UI)

### 속성 (productAttributes)

- 카테고리별 필수/선택 속성을 최대한 채우면 필터 검색 노출 증가
- 색상·사이즈·소재·시즌 등 핵심 속성 필수

### 이미지

- 대표이미지 **1000×1000px 이상** 권장
- 워터마크/텍스트 오버레이 없는 깔끔한 상품 이미지
- 이미지 품질 낮으면 검색 노출 불이익

### 가격비교 매칭

- `naverShoppingSearchInfo`의 브랜드+모델명 정확 입력
- `naverShoppingRegistration: true` 설정
- 카탈로그 매칭 성공 시 가격비교 페이지 노출 → 트래픽 대폭 증가

### 상품정보 제공고시

- 카테고리별 법정 고시정보 완전 기입
- "상품상세참조" (`"0"`)로 통일 가능하나, 실제 값 기입 시 검색 품질 점수 가산

### 검색 순위 진단

- 스마트스토어센터 > 상품관리 > **검색 순위 진단** 메뉴에서 개별 상품의 검색 노출 상태 확인 가능
- 등록 정보 검토 메뉴에서 미비 항목 안내

---

## 부록: 전체 요청 Body 구조 (SEO 필드 중심 축약)

```json
{
  "originProduct": {
    "statusType": "SALE",
    "saleType": "NEW",
    "leafCategoryId": "50001064",
    "name": "[브랜드] 상품고유명 핵심속성",
    "images": { ... },
    "detailContent": "...",
    "salePrice": 4000,
    "stockQuantity": 100,
    "deliveryInfo": { ... },
    "detailAttribute": {
      "naverShoppingSearchInfo": {
        "manufacturerName": "제조사명",
        "brandName": "브랜드명",
        "modelName": "모델명"
      },
      "afterServiceInfo": {
        "afterServiceTelephoneNumber": "02-1234-5678",
        "afterServiceGuideContent": "A/S 안내"
      },
      "originAreaInfo": {
        "originAreaCode": "00",
        "content": "국산",
        "plural": false
      },
      "productInfoProvidedNotice": {
        "productInfoProvidedNoticeType": "FURNITURE",
        "furniture": { "itemName": "...", "material": "...", ... }
      },
      "productAttributes": [
        { "attributeSeq": 123, "attributeValueSeq": 456 }
      ],
      "optionInfo": { ... },
      "certificationTargetExcludeContent": {
        "kcCertifiedProductExclusionYn": "TRUE"
      },
      "minorPurchasable": true,
      "seoInfo": {
        "pageTitle": "페이지 제목 (검색엔진용)",
        "metaDescription": "메타 설명문",
        "sellerTags": [
          { "text": "태그1" },
          { "text": "태그2" }
        ]
      }
    }
  },
  "smartstoreChannelProduct": {
    "naverShoppingRegistration": true,
    "channelProductDisplayStatusType": "ON",
    "storeKeepExclusiveProduct": false
  }
}
```

---

## 참조 URL 목록

| Source | URL |
|--------|-----|
| API 공식 문서 | https://apicenter.commerce.naver.com/ko/basic/commerce-api |
| GitHub 기술지원 | https://github.com/commerce-api-naver/commerce-api |
| Discussion #2061 (naverShoppingRegistration) | https://github.com/commerce-api-naver/commerce-api/discussions/2061 |
| Discussion #2127 (카탈로그 조회) | https://github.com/commerce-api-naver/commerce-api/discussions/2127 |
| Discussion #25 (상품 수정 필드 삭제) | https://github.com/commerce-api-naver/commerce-api/discussions/25 |
| 실제 API 사용 예시 (Python) | https://santapia.tistory.com/81 |
| 스마트스토어 판매자 FAQ | https://help.sell.smartstore.naver.com |
| Context7 API Docs Mirror | https://context7.com/websites/apicenter_commerce_naver |

---

## UNVERIFIED 항목 정리

다음 항목은 공식 1차 소스에서 직접 확인하지 못한 값입니다:

1. `originProduct.name` 정확한 최대 글자수 (100자로 추정)
2. `seoInfo.pageTitle` 정확한 최대 글자수 (60자로 추정)
3. `seoInfo.metaDescription` 정확한 최대 글자수 (160자로 추정)
4. `sellerTags[].text` 정확한 최대 글자수 (20자로 추정)
5. `naverShoppingSearchInfo.seriesName` 필드 존재 여부
6. `productInfoProvidedNoticeType`의 일부 enum 값 (BIOCHEMISTRY, BIOCIDAL, CELLPHONE 등)
7. `productCertifications` 정확한 field name과 구조
8. `afterServiceGuideContent` 최대 길이

> **구현 시 권장:** 공식 API docs (https://apicenter.commerce.naver.com)에 로그인하여 OpenAPI 스키마 / Try-it 기능으로 각 필드의 정확한 validation 확인 필요. API는 인증 후에만 상세 스키마 열람 가능.

