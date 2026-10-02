# 쿠팡 윙(Coupang Wing) 상품등록 11대 섹션 48개 필드 전수 명세서

---

## 1. 개요
쿠팡 윙 상품등록 페이지(`wing.coupang.com`) 및 Seller API(`POST /v2/providers/seller_api/apis/api/v1/marketplace/seller-products`)의 입력 규격을 단 하나도 누락 없이 100% 매핑한 전수 명세서입니다.

---

## 2. 11대 섹션별 48개 필드 세부 규격

### [섹션 1] 노출 카테고리 (Category)
* **1. 노출 카테고리 코드 (`displayCategoryCode`)**: 쿠팡 고유 6자리 내외의 숫자 코드.
  - 카테고리 확정 시 후속 [섹션 7. 상품고시정보]와 [섹션 11. 검색필터 속성]의 필수 스키마가 동적으로 결정됨.

### [섹션 2] 상품명 (Product Names)
* **2. 등록상품명 (`sellerProductName`)**: 
  - 셀러가 직접 등록하는 상품명.
  - 네이버 25~30자 제한을 풀고, **60~90자 권장 (최대 100자)**.
  - 검색어 중복을 적절히 수용하여 롱테일 유입 극대화.
* **3. 노출상품명 (`displayProductName`)**: 
  - 소비자 화면 상단에 노출되는 정제된 상품명 (브랜드 + 상품명 + 핵심 속성).
* **4. 일반상품명 (`generalProductName`)**: 
  - 카탈로그 매칭 및 가격비교용 표준 품목명.

### [섹션 3] 판매정보 및 옵션 (Pricing & Options)
* **5. 옵션 구분**: 단일상품 vs 조합형 옵션.
* **6. 옵션명**: `색상`, `사이즈`, `용량` 등 (최대 3개 축).
* **7. 옵션값**: `블랙`, `화이트`, `M`, `L`, `XL` 등.
* **8. 정상가 (`originalPrice`)**: 할인율 표기용 정상가 (판매가 대비 20~30% 높은 가격).
* **9. 판매가 (`salePrice`)**: 실제 결제 가격 (쿠팡가).
* **10. 재고수량 (`stockQuantity` / `maximumBuyCount`)**: 옵션별 999개 기본 설정.
* **11. 인당 최대구매수량 (`maximumBuyForPerson`)**: `0` (제한 없음 기본).
* **12. 과세 여부 (`taxType`)**: `과세(TAX)` / `면세(FREE)`.
* **13. 미성년자 구매 (`adultOnly`)**: `전체 이용가(EVERYONE)` / `성인 전용(ADULT_ONLY)`.
* **14. 바코드 유무 (`emptyBarcode`)**: `true` (바코드 없음 체크).
* **15. 바코드 없음 사유 (`emptyBarcodeReason`)**: `"해외구매대행 상품으로 바코드가 없습니다."`

### [섹션 4] 상품 이미지 (Images)
* **16. 대표이미지 (`REPRESENTATION`)**: 1000×1000 정방형 1장 (흰색/누끼 배경, 중국어 워터마크 제거 필수).
* **17. 추가/상세이미지 (`DETAIL`)**: 최대 9장 (`MAX_DETAIL_IMAGES = 9`).

### [섹션 5] 상세설명 (Contents)
* **18. 본문 콘텐츠 (`contents`)**: 
  - 모바일 최적화 반응형 HTML (가로 너비 860px 기준).
  - 후킹 문구 -> 3대 특장점 -> 상세 스펙표 -> 해외배송/통관 안내.

### [섹션 6] 상품 주요정보 (Basic Information)
* **19. 브랜드 (`brand`)**: 자체제작, 협력업체 또는 `'노브랜드'` (빈값 불가).
* **20. 제조사 (`manufacture`)**: 모르면 브랜드명과 동일 입력.
* **21. 모델명 (`modelName`)**: 선택 입력 (카탈로그 미매칭 시 비워도 됨).
* **22. 원산지 (`originCountry`)**: `수입산 > 아시아 > 중국` (필수).
* **23. 상품구성 (`productComposition`)**: `단일 상품` / `혼합 세트`.
* **24. 병행수입 여부 (`parallelImported`)**: `병행수입 아님`.
* **25. 인증정보 (`certifications`)**: `인증 대상 아님` 또는 `상세페이지 별도 표기`.

### [섹션 7] 상품정보제공고시 (Notices) — *35개 품목군*
* **26. 고시 품목군 (`noticeCategoryName`)**: 패션잡화, 소형가전, 생활용품 등.
* **27~34. 세부 고시 항목 (`noticeCategoryDetailName`)**: 
  - 소재, 색상, 치수, 제조국, 취급주의사항 등.
  - 미확인 항목은 공식 허용 문구인 `'상세페이지 참조'`로 100% 매핑.

### [섹션 8] 배송정보 (Shipping)
* **35. 배송방법 (`deliveryMethod`)**: `해외구매대행(AGENT_BUY)` / `일반순차(SEQUENCIAL)`.
* **36. 통관부호 필수 (`pccNeeded`)**: `true` (구매대행 시 개인통관고유부호 강제).
* **37. 택배사 (`deliveryCompanyCode`)**: CJ대한통운(`CJGLS`), 한진(`HANJIN`) 등.
* **38. 배송비 종류 (`deliveryChargeType`)**: `유료(NOT_FREE)` / `무료(FREE)`.
* **39. 기본 배송비 (`deliveryCharge`)**: 3,500원 ~ 6,000원.
* **40. 도서산간 배송비 (`remoteAreaDeliverable`)**: 가능(`Y`) / 불가(`N`).
* **41. 묶음배송 여부 (`unionDeliveryType`)**: `불가(NOT_UNION_DELIVERY)` 권장.
* **42. 출고소요일 (`outboundShippingTimeDay`)**: **7~14일 필수** (배송지연 패널티 방어).

### [섹션 9] 반품/교환 (Returns)
* **43. 출고지 주소록 (`outboundShippingPlaceCode`)**: Wing 등록 출고지 코드.
* **44. 반품지 주소록 (`returnCenterCode`)**: Wing 등록 반품지 코드.
* **45. 초도반품배송비 (`returnShippingCharge`)**: 3,500원 (무료배송 시).
* **46. 편도반품배송비 (`returnCharge`)**: 3,500원 ~ 7,000원 (합계 상한 검증).

### [섹션 10] 상품 검색어 (Search Tags)
* **47. 검색어 태그 (`searchTags`)**:
  - **정확히 20개 꽉 채움 (`minItems: 20, maxItems: 20`)**.
  - 각 키워드는 20자 이내. 빈칸 0개.

### [섹션 11] 검색필터 속성 (Attributes)
* **48. 카테고리 매칭 동적 속성 (`attributes`)**:
  - 카테고리 메타데이터에 정의된 필수/권장 속성(`attributeTypeName`)에 값 1:1 매핑.
  - 쿠팡 모바일 필터 검색 대응.
