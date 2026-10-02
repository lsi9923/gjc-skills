# 쿠팡 Wing 등록 화면 절차 (섹션별 전수 입력 체크리스트)

URL: `https://wing.coupang.com/tenants/seller-web/vendor-inventory/formV2` (상품관리 > 상품 등록). 사용자가 직접 로그인·2단계 인증.

## 조작 원칙
- 각 섹션 입력 전후로 `snapshot(page)` 로 **라벨 텍스트**(예: "노출상품명", "판매가", "출고소요일") 기준으로 요소를 찾는다. CSS 선택자를 지어내지 않는다. 섹션 이름은 화면 표기를 따르고, 바뀌었으면 가장 가까운 섹션을 찾는다.
- 값 입력 후 snapshot 으로 실제 반영 확인. 드롭다운이 클릭으로 확정 안 되면 키보드+Enter.
- 값 출처 표기: `plan` = registration_plan.json, `coupang_build` = coupang_build.json, `coupang_category` = coupang_category.json, `profile` = config/seller_profile.json, `사용자확인` = 근거 없으면 물어야 하는 값.

## 공식 제약 (Coupang Open API 상품 생성 스펙, 2026-09 확인)
- 등록상품명(발주서용)·노출상품명 각 **최대 100자**. 노출상품명 권장 = 브랜드(없으면 생략) + 제품명, **옵션값 제외**.
- 대표이미지: **정사각형** JPG/PNG, **500~5000px, 3MB 이하**. 추가(기타)이미지 최대 9장.
- 검색어: **최대 20개, 개당 20자**, 특수문자는 `!@#$%^&*-+;:'.` 만.
- 옵션(아이템) 최대 200개, 옵션명 150자, 판매가능수량 최대 99999, 인당 최대구매 0 = 제한없음.
- **반품배송비는 초도반품배송비의 100~150% 범위만** 가능.
- 해외구매대행(AGENT_BUY)은 **해외 출고지 주소만** 가능 + 인보이스 영수증 첨부 + 개인통관부호(PCC) 필수. 국내(인천) 출고지로는 구매대행 선택 불가 → 국내 위탁/재고 상품은 일반배송.
- 고시정보 항목명은 카테고리가 제공하는 것과 정확히 일치해야 함(품목군 선택 시 자동 표시되는 항목을 채운다).
- 필수 구매옵션(예: 수량, 개당 용량/중량)이 빠지면 등록/노출 제한.

---

## [섹션 1] 노출 카테고리
- **입력값**: Wing 카테고리 검색/추천 화면에 **실제로 뜬 후보만** `candidates.json` 으로 만들어 `coupang_category_pick.py` 로 점수화한 `coupang_category.json` 의 `categoryCandidates`(score·reasons) 중 확정 말단(= `plan.coupang.categoryPath`).
- **입력법**: 카테고리 검색 → 추천/검색 결과에서 말단 선택. 상위 판매자 경로(candidates 의 `topSeller`)와 대조.
- **확인**: 선택 후 카테고리가 확정되면 [섹션 9 고시]·[섹션 7 속성] 스키마가 동적으로 바뀐다 — 두 섹션이 다시 로드됐는지 확인.
- **함정**: `categoryCandidates=[]`(화면에 후보 없음)면 경로를 지어내지 말고 화면에서 다시 읽는다.

## [섹션 2] 상품명
- **노출상품명**: `coupang_build.json` 의 `exposureName`(옵션값·브랜드 제거된 제품명, ≤100자) = `plan.coupang.productName`.
- **등록상품명**(있으면): 노출상품명과 동일하게 두거나 롱테일 확장 가능(≤100자).
- **확인**: 화면 글자수 ≤100. 브랜드(`plan.brand.removedFromMarketing`)가 남아 있지 않은지 확인. `plan.brand.ownKept` 는 유지.
- **(미검증) 레거시 권장** : 구버전 문서의 "60~90자 롱테일", "브랜드+서브키워드+메인키워드 F자 배치", "일반상품명 별도 입력"은 화면·API 로 확인 안 됨 → **(미검증)**. 근거 없는 수식어(무선·대용량·방풍 등)를 상품명에 임의 추가하지 않는다.

## [섹션 3] 판매정보 및 옵션
- **옵션 구분**: 단일상품이면 옵션 없음(단일). 필수 구매옵션이 요구되면 실제 값(예: 수량 `1개`). 실제 옵션이 있으면 옵션명·값 입력 → 옵션목록 생성.
  - 옵션 근거: `plan.source.optionRows` 중 사용자가 지정한 것만. `coupang_category.json` 의 `droppedOptions`(품절·판매종료)는 제외.
  - 색상은 **쿠팡 표준명**(흰색→화이트, 회색→그레이, 검정→블랙 — coupang_category 판정).
- **판매가**: `plan.coupang.salePrice`(무료배송이므로 배송비 포함 가격).
- **정상가(할인율기준가)**: `plan.coupang.originalPrice`. 없으면 판매가와 동일(→ '쿠팡가' 표시).
  - **(미검증)** 구버전의 "정상가를 판매가보다 20~30% 높게" 는 근거 없는 임의 인상 → 하지 않는다. profile.coupang 에는 참고용 `coupangOriginalPriceRatio 1.25` 만 있고, 실제 정상가는 근거 있을 때만.
- **재고**: 옵션별 `999`(profile.coupang.stockPerOption). **인당 최대구매 0**(제한없음, profile.coupang.maxBuyPerPerson).
- **과세**: `과세`(profile.coupang.taxType). **미성년자 구매 가능**(전체 이용가).
- **바코드**: 없으면 `바코드 없음` 체크 + 사유 — 국내 위탁: "제조사 바코드 미제공 상품", 해외구매대행: "해외구매대행 상품으로 바코드가 없습니다".
- **확인**: 옵션별 판매가·정상가·재고가 일괄 적용됐는지, 필수옵션 경고가 없는지 확인.

## [섹션 4] 상품이미지
- **입력값(세션 폴더 안 경로만)**: 대표 = `plan.images.coupang.representative`(thumb_1, 정사각 500~5000px·3MB 이하). 추가 = `plan.images.coupang.additional`(thumb_2~5, 최대 9장).
- **입력법**: filechooser + 세션 폴더 경로. (세션 폴더 밖 경로는 거부됨)
- **확인**: 대표이미지가 정사각형으로 반려되지 않는지, 추가이미지 개수 확인.
- **함정**: 대표이미지가 3MB 초과·비정사각이면 반려 → 규격 확인 후 재업로드(임의 리사이즈 생성 금지, 업로드 실패 시 사용자에게 알림).

## [섹션 5] 상세설명
- **입력값(세션 폴더 안 경로만)**: `plan.images.coupang.detailContents`(`section_01~` 순서). 섹션이 없을 때만 `detail_page.png` 시도.
- **입력법**: `이미지 업로드` 방식으로 업로드 → 미리보기에서 순서·개수 확인.
- **함정**: `detail_page.png` 용량 오류(3MB 초과 등) 시 사용자에게 알림. 이호 자료·임의 SEO 카드 이미지 추가 금지.

## [섹션 6] 상품 주요정보
- **브랜드**: `브랜드 없음` 체크(브랜드 제거 규칙). `plan.brand.ownKept` 가 있으면 그 값.
- **제조사**: `plan.notice.제조자/수입자`(원상품 제조자/수입자). 모르면 **사용자확인**(구버전의 "모르면 브랜드명과 동일" 은 임의값 → 하지 않는다).
- **모델명**: 비움 가능.
- **원산지**: `plan.notice.제조국` 근거값. 없으면 `중국`(profile.coupang.originDefault).
- **상품상태**: `새상품`. **병행수입 아님**. **상품구성**: 단일/세트 = 실제 근거.
- **인증**: 대상 아님이 **확실할 때만** `인증대상 아님`, 아니면 사용자확인(추측 금지).

## [섹션 7] 검색필터(속성)
- **입력값**: 화면에 뜬 필터 스펙을 `attributes.json` 으로 만들어 `coupang_category_pick.py --attributes-json` 판정 → `coupang_category.json` 의 `attributes.filled`(색상=쿠팡 표준명·숫자형=숫자만·enum 일치)만 선택. `attributes.empty` 는 **비운다**.
- **원칙**: 원상품 근거가 있는 항목만. 무관한 속성을 남발하면 알고리즘 일치도 하락(구버전·현행 공통).
- **확인**: 필수 속성이 채워졌는지, empty 로 둔 항목이 필수 경고를 내지 않는지 확인.

## [섹션 8] 검색어
- **입력값**: `coupang_build.json` 의 `searchTerms`(F12 근거 통과 키워드 + 태그 후보) = `plan.coupang.tags`. 하나씩 입력(Enter).
- **소스 보강(선택)**: 화면의 `추천 검색어`·`인기검색어`(`popularity-search` 도구)·자동완성 중 **실제로 뜬 단어만** `sources.json` 으로 `coupang_helper.py --sources-json` 에 넘겨 소스 우선순위 귀속. 화면에 없으면 지어내지 않는다.
- **함정**: **20개를 억지로 꽉 채우지 않는다**. 근거 없는 단어로 채우기 금지 — 20개 미달이면 미달로 둔다. (구버전 "정확히 20개 꽉 채움" 은 근거 있는 키워드가 충분할 때만.) 개당 20자·허용 특수문자만.

## [섹션 9] 상품정보제공고시
- **입력법**: 카테고리 품목군 선택 → 화면 자동 표시 항목을 채운다.
- **입력값**: `plan.notice` 근거값. '품명 및 모델명' 에는 제품명. 근거 없는 항목만 `상세페이지 참조`.
- **함정**: 항목명은 카테고리 제공 항목과 정확히 일치해야 등록됨. 전 항목 `상세페이지 참조` 도배 금지.

## [섹션 10] 배송
- **배송방법**: `plan.coupang.deliveryMethod` — 국내 위탁은 `일반배송(순차배송)`(profile.coupang.deliveryMethodDomestic). 해외구매대행은 `해외구매대행`(profile.coupang.deliveryMethodOverseas) + PCC·인보이스·해외 출고지 필요.
- **택배사**: `CJ대한통운`(profile.coupang.courier).
- **배송비**: `무료배송`(profile.coupang.shippingChargeType, 판매가에 포함).
- **출고소요일**: 국내 `2일`(profile.coupang.outboundDaysDomestic), 해외구매대행 `7~14일`(profile.coupang.outboundDaysOverseas). 사용자 운영값이 다르면 그 값.
  - **(미검증) 레거시 치트키 금지**: 구버전의 "주문제작(MAKE_ORDER)으로 출고일 20일 연장", "해외 아니어도 7~14일 필수" 는 실제 상품 조건과 다르면 허위 → 국내 상품에 임의 적용하지 않는다.
- **묶음배송**: 출고지 등록 시 가능. **도서산간**: 출고지 설정 따름.
- **출고지**: Wing 에 등록된 인천 출고지 선택(`profile.seller.shipFromAddress`).

## [섹션 11] 반품/교환
- **반품지**: 등록된 인천 반품지 선택(`profile.seller.returnAddress`).
- **초도반품배송비**: `3,500`(profile.coupang.initialReturnFee).
- **반품배송비**: `3,500`(profile.coupang.returnFee) — **초도반품비의 100~150% 규칙** 충족(3,500~5,250 범위).
- **교환비**: 화면 자동 계산값 확인.

## [섹션 12] 구비서류
- 카테고리가 요구하면 사용자에게 파일 요청. 없으면 등록 중단(임의 생성·제출 금지).

---

## 최종 확인 → 등록
13. 여기서 **멈추고** `build_confirm_table.py` 최종 확인표를 사용자에게 보여준다.
14. 사용자가 "등록" 이라고 하면 `판매요청`. "임시저장" 이면 `저장하기`. **사용자 최종 확인 전에는 절대 클릭하지 않는다.**
15. 결과: 등록상품ID·노출상품ID(상품조회 화면 드롭다운)를 캡처해 `plan.coupang.result` 로 기록하고, **노출상품ID 백업**을 사용자에게 알린다(상품명·태그 수정 후 ID 변경으로 노출 누락 시 쿠팡 1:1 문의 복구용).
16. `memory/projects/naver-coupang-registration.md` History 에 한 줄 기록.

## 오류 대응
- "필수 구매옵션" 경고 → 해당 옵션을 실제 값으로 추가. 값을 모르면 사용자확인.
- 이미지 반려/업로드 실패 → 규격(정사각형, 3MB) 확인 후 재업로드.
- 캡차·보안문자·재로그인 → 사용자에게 넘긴다. **우회하지 않는다.**
- 새로 알게 된 화면 동작은 `memory/sites/wing.coupang.com.md` History 에 추가한다.
