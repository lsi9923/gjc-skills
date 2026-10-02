# 네이버 스마트스토어 등록 화면 절차 (섹션별 전수 입력 체크리스트)

URL: `https://sell.smartstore.naver.com/#/products/create` (사용자가 직접 로그인). 상품등록 화면은 위→아래 한 페이지에 섹션이 나열된다.

## 조작 원칙
- 각 섹션 입력 전후로 `snapshot(page)` 를 찍어 **라벨 텍스트**(예: "상품명", "판매가", "배송비") 기준으로 요소를 찾는다. CSS 선택자를 지어내지 않는다 — 화면 구조가 자주 바뀌므로 snapshot 의 accessibility 트리에서 라벨로 ref 를 얻는다.
- 드롭다운이 마우스 클릭으로 확정되지 않으면 **키보드 방향키 + Enter** 로 확정한다(메모리 실측: 유료배송 드롭다운).
- 값 입력 후 반드시 그 값이 실제로 들어갔는지 snapshot 으로 재확인한다(setValue 가 무시되는 필드 있음).
- 버튼 ref 가 불안정하면 visual-browse 로 좌표 클릭 후 재확인.
- 값 출처 표기: `plan` = registration_plan.json, `title_build` = title_build.json, `profile` = config/seller_profile.json, `사용자확인` = 근거 없으면 물어봐야 하는 값.

---

## [섹션 1] 카테고리
- **입력값**: `naver_category_pick.py` 출력 `naver_category.json` 의 `leafCandidates` 중 확정한 말단 경로(= `plan.naver.categoryPath`).
- **입력법**: `카테고리명 검색` 입력창에 말단 키워드 입력 → 드롭다운에서 **경로가 정확히 같은 항목** 선택. 대/중/소/세 4단 경로 전체가 화면에 표시되는지 본다.
- **확인**: 선택 후 카테고리 경로 텍스트가 `leafCandidates` 경로와 글자까지 동일한지 snapshot 으로 확인.
- **기본값 함정(중요)**: 카테고리 선택 직후 원산지 `국산`, 배송 `무료(0원)`, 반품/교환 `0원` 같은 기본값이 자동 주입될 수 있다. → 섹션 8·10 에서 반드시 덮어쓴다. 여기서 확인만 하고 넘어가면 잘못된 기본값으로 등록된다.
- **판정불가 시**: `naver_category.json` 의 `verdict:"판정불가"`(데이터 없음/차단)면 경로를 강행하지 말고 사용자 확인. 서로 다른 키워드의 카테고리를 임의 조합하지 않는다.

## [섹션 2] 상품명
- **입력값**: `title_build.json` 의 `titleCandidates` 중 사용자가 고른 것(= `plan.naver.productName`). 완성형 키워드 0번(맨 왼쪽), 조합형 왼→오·거리 최소, 공백 포함 25~30자 권장(최대 35).
- **입력법**: 상품명 입력란에 붙여넣기.
- **확인**: 화면 글자수 카운터가 25~30자(≤35) 인지, `judgeTable` 의 완성형/조합형 순서와 일치하는지 확인.
- **함정**: 브랜드/판매자명(`plan.brand.removedFromMarketing`)이 상품명에 남아 있으면 안 된다. `plan.brand.ownKept`(예: 끄롱마제) 는 유지. 특수기호·옵션값(색상/사이즈)은 상품명에서 뺀다.

## [섹션 3] 판매가
- **입력값**: `plan.naver.salePrice`(원가 근거 있으면 `plan.pricing.suggested`, 없으면 사용자확인).
- **입력법**: 판매가 입력. 할인은 사용자가 따로 지정한 경우만 설정.
- **함정**: `salePrice` 가 null 이면 이 단계로 넘어오면 안 된다(가격 미확정 게이트). 부가세는 `과세상품`(profile.naver.taxType) 확인.

## [섹션 4] 재고수량
- **입력값**: 옵션 없으면 단일 재고 `999`(profile.naver.stockPerOption).
- **함정(메모리 실측)**: 조합형 옵션이면 옵션별 999 를 넣으면 **총재고 = 조합 수 × 999 로 자동 합산**된다(예: 42조합 × 999 = 41,958). 총재고를 직접 999 로 다시 쓰지 않는다.

## [섹션 5] 옵션 (원상품에 실제 옵션이 있을 때만)
- **입력값**: `plan.source.optionRows` / `optionsText` 중 **사용자가 쓰겠다고 지정한 항목만**. 1688 원문을 전부 자동 등록하지 않는다. 원문 의미와 한국어 상품 용어를 해설해 확인받은 뒤 사용.
- **입력법**: 조합형 선택 → 옵션명(색상/사이즈 등) + 옵션값 → `옵션목록으로 적용` → 옵션가 0(차액 있으면 입력) → 옵션별 재고 999.
- **확인**: 옵션 조합 수 × 999 = 총재고 자동계산 값 확인.
- **함정**: 번역이 여러 의미면 임의 확정하지 말고 사용자확인.

## [섹션 6] 상품이미지
- **입력값(세션 폴더 안 경로만)**: 대표 = `plan.images.naver.representative`(thumb_1). 추가 = `plan.images.naver.additional`(thumb_2~5). 대표 1 + 추가 최대 9.
- **입력법**: filechooser 로 세션 폴더 upload 경로만 setFiles(세션 폴더 밖 경로는 거부됨).
  ```js
  const fc = page.waitForEvent('filechooser');
  await page.locator('<대표이미지 등록 ref>').click();   // snapshot 라벨 "대표이미지"
  (await fc).setFiles('<workDir>\\upload\\thumb_1.png');
  ```
  추가이미지는 한 번에 여러 개 선택 가능(예: thumb_2~5 를 배열로).
- **확인**: 대표 썸네일 미리보기 표시, 추가이미지 카운터(예: 4/9) 확인.

## [섹션 7] 상세설명
- **입력값(세션 폴더 안 경로만)**: `plan.images.naver.detailEditor` — 기본 `detail_page.png` 1장, 없으면 `section_01~` 순서.
- **입력법**: `SmartEditor ONE으로 작성` → 이미지(사진) 버튼 → 파일 업로드 → 에디터 `등록`(상세설명 반영일 뿐, 상품 등록 아님).
- **확인**: 에디터 안 이미지가 `data:image/svg` placeholder 가 아니라 네이버 서버 URL(`https://...pstatic.net` 등)인지, 개수·순서가 맞는지 확인. 상품등록 화면에 "작성된 내용이 있습니다" 표시 확인.
- **함정**: 이호 강의 자료·임의 SEO 카드 이미지를 상세에 추가하지 않는다. 메이커 상세페이지 이미지만 넣는다.

## [섹션 8] 상품 주요정보
- **모델명**(선택): 제품명 또는 비움.
- **브랜드**: 비움 또는 `자체제작`(브랜드 제거 규칙). 검색품질 체크의 "브랜드 입력 안됨" 경고는 의도된 것으로 본다. `plan.brand.ownKept` 가 있으면 그 값(자체 브랜드).
- **제조사**: `plan.notice.제조자/수입자`(원상품 제조자/수입자 근거값) 또는 `협력업체`. 모르면 사용자확인.
- **상품상태**: `신상품`(profile.naver.condition).
- **원산지**: `plan.notice.제조국` 근거값. 근거 없으면 `수입산 > 아시아 > 중국`(profile.naver.originDefault). 원상품 근거가 다르면 그 값.
- **수입사**: 근거값(plan.notice).
- **인증(KC 등)**: `plan.notice.인증` 근거가 있을 때만 입력. 대상 여부 불명이면 **사용자확인**(추측 금지).
- **함정**: 원산지 기본값 `국산` 이 남아 있지 않은지 반드시 확인.

## [섹션 9] 상품정보제공고시
- **입력법**: 카테고리 추천 품목군 선택 → 화면이 자동 표시하는 항목만 채운다.
- **입력값**: 품명/모델명, 제조국, 제조자·수입자, 인증, 크기·재질 등 = `plan.notice` + `plan.sectionCopy` 근거값. 근거 없는 항목만 `상세페이지 참조`.
- **고정문구**: 품질보증기준 = `관련법 및 소비자분쟁해결기준에 따름`. A/S 책임자·전화 = `profile.seller.asPhone`(없으면 사용자확인 후 profile 저장), A/S 안내 = `profile.seller.asGuide`.
- **함정**: 전 항목을 `상세페이지 참조` 로 도배하지 않는다 — 근거 있는 항목은 실제 값으로.

## [섹션 10] 배송
- **배송방법**: 택배/소포/등기.
- **택배사**: `CJ대한통운`(profile.naver.courier).
- **배송비**: `유료 3,500원`(profile.naver.shippingFeeType/shippingFee). **드롭다운은 키보드 방향키+Enter 로 확정**(마우스 클릭이 안 먹을 수 있음 — 메모리 실측).
- **출고지**: 판매자센터에 등록된 인천 주소 선택(`profile.seller.shipFromAddress` / `zipCode 23466`).
- **함정**: 카테고리 선택 시 들어간 `무료(0원)` 기본값이 남아 있지 않은지 확인.

## [섹션 11] 반품/교환
- **반품배송비(편도)**: `3,500원`(profile.naver.returnFee).
- **교환배송비(왕복)**: `7,000원`(profile.naver.exchangeFee).
- **반품/교환지**: 출고지와 동일 주소(`profile.seller.returnAddress`).
- **함정**: 반품/교환 `0원` 기본값이 남아 있지 않은지 확인.

## [섹션 12] 검색설정 (태그)
- **입력값**: `title_build.json` 의 `tagCandidates`(F12 근거 통과 태그, 최대 10개) = `plan.naver.tags`.
- **입력법**: 태그를 하나씩 입력 → **사전 추천 목록에 뜨는 것만** 선택. 등록 안 되는 태그는 대체 후보로 교체.
- **함정**: `title_build.judgeTable` 에서 `미적용`/`판정불가(terms 없음)` 인 단어는 태그로 쓰지 않는다(추측 금지).

## [섹션 13] 검색품질 체크
- 하단 `쇼핑 상품정보 검색품질 체크` 실행 → 카테고리·상품명·태그 결과를 캡처해 최종 확인표에 싣는다.

---

## 최종 확인 → 등록
14. 여기서 **멈추고** `build_confirm_table.py` 로 만든 최종 확인표(키워드 판정표 + 최종 확인표)를 사용자에게 보여준다.
15. 사용자가 "등록"/"진행" 이라고 하면 `저장하기`. "임시저장" 이면 `임시저장`("임시저장 완료" 문구 확인 — 메모리 실측). **사용자 최종 확인 전에는 절대 클릭하지 않는다.**
16. 등록 후 상품번호·판매상태 캡처, `plan.naver.result` 기록. `memory/projects/naver-coupang-registration.md` History 에 한 줄 기록.

## 새로 확인된 화면 동작
- 새로 알게 된 동작은 `memory/sites/smartstore.naver.com.md` History 에 추가한다.
