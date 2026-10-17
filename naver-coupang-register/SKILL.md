---
name: "naver-coupang-register"
description: "네이버 스마트스토어·쿠팡 윙 실제 상품 등록 스킬. Maker Selling Helper의 maker_ui.json에서 키워드 칩·카테고리 후보·태그 후보를 읽고 상품명은 원상품 사실과 Maker 칩으로 작성한다(추출기에 최종 상품명 필드 없음). Maker 태그 부재 시 관련 키워드 칩과 원상품 표현을 활용해 라이브 태그창에서 10개를 목표로 검증 선택한다. Wing 카테고리 추천 상위 1~3개에서 말단 ID를 선택하고 필수값을 입력한 뒤 간결한 통합 확인표 승인 후 제출·판매상태 검증·Argo 기록까지 수행한다. F12 분석, 전체 taxonomy 비교, 쿠팡 검색어 20개와 완전한 SEO JSON 감사는 기본 제출 요건이 아니다."
autoInject:
  url:
    - "sell.smartstore.naver.com/**"
    - "wing.coupang.com/tenants/seller-web/vendor-inventory/**"
---
실행 전 references/known-errors.md 와 references/ops-playbook-2026-10-17.md 를 반드시 먼저 읽고, 새 오류 해결 시 같은 형식으로 추가한다.
<!-- MAKER-SELLING-REGISTER:START -->
## 속도 우선 기본 경로 — Maker 우선, 필수값만 게이트
- 네이버는 Maker Selling Helper의 실제 `maker_ui.json`을 기본 경로로 즉시 읽는다(키워드 칩·카테고리 후보·태그 후보). 추출기에는 최종 상품명 필드가 없으므로 상품명은 원상품 사실과 Maker 칩으로 빌드한다. F12 패킷 수집·terms 분류는 사용자가 명시적으로 요청하지 않는 한 하지 않는다. 출처는 `maker_ui`로 보존하고 F12 근거로 가장하지 않는다.
- Maker JSON의 유효성은 실제 UI 캡처(file fixture 아님), 상품 핵심어와 맞는 query, 같은 세션 추출 세 가지만 확인한다. 유효하지 않으면 "Maker 근거 무효"로 멈추고 F12로 조용히 폴백하지 않는다.
- 상품명은 끄롱마제로 시작하고 Maker 칩이나 원상품 사실로 단어를 뒷받침한다. 안전·수동·방지·인증·특허 표현은 원본 사실을 확인하고 미확인 표현은 제거한다. 100자 초과는 BLOCK, 25~35자는 참고 INFO다.
- 네이버 태그는 Maker 태그 후보 또는 관련 키워드 칩과 원상품 사실을 바탕으로 고유한 관련어 10개를 목표로 실시간 입력창에서 선택 여부를 검증한다. Maker 태그가 비어 있거나 누락되어도 보이는 키워드 칩과 사실적 표현으로 채우며(지어내기 금지), 미달은 N/10 WARN이고 11개 초과와 플랫폼 하드 한도 위반은 BLOCK이다.
- Coupang 카테고리는 Wing live 검색 상위 1~3 추천의 ID·경로를 기록하고, 용도에 맞는 선택 가능 말단을 고른다. 맞는 후보가 없으면 검색어를 한 번 좁혀 재검색한 뒤, 동일상품 seller listing ID → 기존 공식 ID → 정확히 일치하는 원상품 공개 Coupang 경로 순으로 대체 후보를 찾는다. 후보마다 공식 tree 1회 조회/공식 lookup 1회와 live 선택으로 검증한다. 전체 taxonomy 비교는 하지 않는다. 검증된 후보가 없으면 Coupang만 중단하고 다른 마켓을 계속한다. 충돌 후보는 확인표에 함께 보여주고 사용자가 선택한다.
- Maker 기반 plan을 사용할 때 `naver.productNameSource`와 `naver.tagsSource`를 `maker_ui`로 기록한다. Coupang 상위 1~3 후보와 선택 이유는 `coupang.categoryCandidates`에 보존한다. 대체 경로는 `coupang.categoryEvidence`에 method, live queries, fallback source/ref, terminal ID/path, 단일 공식 확인 결과, liveSelected, `comparisonScope:"bounded_fallback"`, `fullTaxonomyComparison:false`로 남긴다. `fullLeafComparison:true`라고 쓰지 않는다.
- 확인표에 표시할 때 판매가 출처를 `pricing.salePriceSource`로 기록한다(사용자 제공, 승인된 계산식 또는 확인한 자료). 경쟁 상품 판매가는 원가로 표현하지 않는다.
- Coupang 검색어 20개는 최대치이며 미달은 WARN이다. 개별 검색어 길이·허용 문자·홍보어·제거 대상 브랜드 유출은 계속 BLOCK이다. 관측어라도 원상품 사실에 없는 기능·재질·규격이면 제외한다. term별 provenance JSON과 검색면 포화 조사는 기본 게이트가 아니다.
- 등록 완료 게이트는 상품명, 선택 카테고리, 가격, 실제 상품 이미지, 상세페이지, 관련 태그다. 실제 화면에서 필수로 요구되는 판매자·법정 필드도 입력한다. 선택값·검색량·완전한 plan JSON·전체 SEO 감사는 제출 조건이 아니다.
- 자체 브랜드 `끄롱마제`는 KIPRIS 조회를 생략한다. 예외는 이 브랜드명에만 적용하고 제3자·경쟁 브랜드는 기존 검토 규칙을 따른다.
- 여러 상품은 준비를 연속 진행해 한 장의 통합 확인표로 승인받는다. 확인표 승인 후 값이 바뀌면 변경분을 다시 보여주고 재승인받는다. Claude 검토나 "등록해" 요청은 최종 확인표 승인이 아니다. 승인 뒤 상품을 순차 제출하고 실제 상태를 확인한다.
- Maker 데이터가 실제 UI에서 최근 추출된 것이 아니거나 핵심 사실과 충돌할 때만 해당 충돌을 확인한다. 정보가 완벽한 JSON인지 확인하는 작업으로 되돌아가지 않는다.
<!-- MAKER-SELLING-REGISTER:END -->

# 네이버·쿠팡 상품 등록

더미 JSON이나 복붙용 텍스트만 주고 끝내지 않는다. 실제 등록 화면에 직접 입력한다. Naver는 `저장하기`, Coupang은 현재 화면의 최종 제출 버튼(확인된 라벨은 `상품등록`)을 사용자 최종 확인 후에만 누른다.

`<skill>` = 이 SKILL.md 가 있는 폴더. 스크립트는 bash(PowerShell)에서 `python` 으로 실행한다(표준 라이브러리만 사용).

## 실행 계약: 준비부터 판매 검증까지
- 이 통합 스킬을 네이버·쿠팡 등록의 단일 실행 진입점으로 쓴다. 이전의 Naver/Coupang 단일 마켓 스킬은 근거 참고용이며, 서로 다른 등록 절차를 따로 실행하지 않는다.
- 사용자가 `등록`을 요청하면 기존 상품 중복 확인, 원상품·가격·옵션·고시·이미지 조사, SEO·카테고리 근거 수집, 판매자 화면 입력, 최종 확인표, 명시적 승인 뒤 실제 제출, 등록 ID·재고·판매 상태·고객용 페이지 확인, Argo 기록까지 끝낸다. 계획서나 임시저장만으로 완료 처리하지 않는다.
- 이전 대화, Argo, Aside 세션과 원본 폴더를 먼저 찾아 이미 제공된 이미지·입력법을 재사용한다. 옵션·비용·배송값은 출처를 조사해 구체적인 최선안을 제시한다. 사용자가 단일상품이라고 하면 근거와 명시적 선택 전까지 옵션을 만들지 않는다.
- 네이버 기존 일치 상품이 판매중·전시중이면 수정·중복 등록하지 않는다. 여러 상품은 준비를 연속으로 끝내고 한 번의 통합 확인표로 승인받은 뒤 순차 등록·검증한다.
- 제출 버튼은 사용자가 최종 확인표를 보고 승인한 뒤에만 누른다. 로그인·인증·캡차는 사용자가 처리한다. 개인정보·이미지 URL·비밀정보는 Argo나 공개 기록에 남기지 않는다.

## 0. 입력 확정
- 대상: "완료된폴더 N번"/폴더 경로/상품 URL. URL만 받으면 `C:\Users\imda0\Downloads\완료된폴더\*\source.json` 의 url 상품번호로 폴더를 찾는다. 못 찾으면 상세페이지 메이커(`<skill>/config/seller_profile.json` sourceFolders.makerProgram)로 먼저 만들어야 한다고 알린다.
- 마켓: "네이버 쿠팡" = 둘 다, 한쪽만 말하면 그쪽만. 여러 폴더면 준비를 연속 진행하고 통합 확인표로 승인받은 뒤 순차 등록한다.
- 엑셀이 함께 오면 행 순서 = 폴더 순서로 매칭하고 URL 상품번호를 대조한다. 어긋나면 멈춘다.

## 1. 준비 스크립트
작업폴더를 GJC 범용 폴더(`C:\tmp\reg-<폴더명>`) 또는 `aside.sessions.current()` 의 세션 폴더 아래 `tmp\reg-<폴더명>` 으로 정한다. `prepare_product.py`는 각 상품에 한 번 실행해 로컬 facts/assets를 `registration_plan.json`에 정리한다. Maker 기본 경로에서는 이 계획을 데이터 컨테이너로만 쓰며 F12/SEO audit을 돌리거나 optional blocker를 해결하려고 반복하지 않는다:
```
python "<skill>\scripts\prepare_product.py" "<완료폴더\N>" --out "C:\tmp\reg-N" [--cost-krw 원가 | --cost-cny 위안]
```
- `registration_plan.json`의 blocker를 그대로 제출 중단으로 처리하지 않는다. 상품명·카테고리·가격·이미지·상세페이지·태그 또는 실제 seller form 필수 필드에 해당하는 blocker만 해결한다. 선택값·검색량·SEO JSON 누락은 blocker가 아니다.
- `needsBrowser`는 자동 등록 blocker가 아니다. 상품명·가격 또는 live form에서 필수인 고시 사실이 완료폴더에 없으면 그 필드만 확인하기 위해 Aside 브라우저로 원상품을 연다. 페이지가 막혀도 해당 값이 필수가 아니면 진행하고, 필수인데 사실을 확인할 수 없을 때만 정확한 사유로 중단한다. 1688 가격은 원가로 간주하지 않는다.
- 필요한 사용자 확인은 실제 등록 필수값이 없을 때만 한 번에 묻는다. A/S 전화 등 seller form에서 필수로 요구되는 고정값은 확인 후 profile에 저장한다(비밀번호·인증번호·API secret 은 저장·요청 금지).
- 업로드는 반드시 plan 의 `upload\thumb_*.png`, `detail_page.png`, `section_*.png` 경로를 쓴다(세션 폴더 밖 경로는 setFiles 가 거부됨).
- 1688 옵션은 원문을 전부 자동 등록하지 않는다. 사용자가 쓰고 싶다고 지정한 옵션만 원문 의미와 한국어 상품 용어를 해설해 확인받고, 선택된 옵션만 네이버·쿠팡 입력값으로 구성한다. 선택이 불명확하거나 번역이 여러 의미면 임의 확정하지 않고 묻는다.

## 2. SEO 구성 (`references/seo-rules.md` 참조; 속도 우선 기본 경로 적용)
### 기본 경로와 완료 기준
- 네이버: `maker_ui.json`의 키워드 칩·카테고리·태그 후보를 읽고 원상품 사실과 결합해 제목·카테고리·고유 태그 10개를 정한다(Maker 태그 부재 시 키워드 칩/원상품 사실 활용, 실시간 입력창 검증). F12 `terms`/`intersectionTerms` 수집은 사용자가 요청한 경우에만 한다.
- 쿠팡: 상품 사실에 맞는 제목을 만들고 Wing live 검색의 상위 1~3 추천에서 선택 가능한 말단 ID를 고른다. 5.5만 행 taxonomy 전수 비교는 하지 않는다.
- 쿠팡 검색어는 Wing 추천어와 확인된 상품 표현 중 관련 있는 항목을 가능한 만큼 사용한다. 20개 미달, 검색면 포화 조사, term별 provenance JSON은 blocker가 아니다.
- 확인표는 상품명·카테고리·가격·이미지·상세페이지·태그와 실제 화면에서 필수인 입력만 간단히 표시한다. 선택값이나 모든 JSON 경로가 완성되지 않아도 진행한다. 실제 폼 필수 필드가 미확정이거나 상품 사실 충돌이 있을 때만 해당 항목을 blocker로 둔다.
1. 대표 키워드 후보: plan 의 `keywordSeeds.seeds` (원상품명·제목 꼬리·메이커 섹션 제목·메이커 seo_keywords.json, 출처 표시됨)에 1688 중국어 제목(`keywordSeeds.from1688.title`)을 한국어 상품 용어로 번역한 후보를 더한다. 브랜드(`brand.removedFromMarketing`)는 제외. 이 단계의 키워드는 모두 '후보'다.
2. 고급 선택 경로: 사용자가 F12 수집 또는 이호 terms 분석을 요청한 경우에만 아래 F12 절차를 실행한다. Maker 우선 기본 등록에서는 생략한다.
   - 새 탭에서 `https://search.shopping.naver.com/search/all?query=<키워드>` 로 이동(사람처럼 한 번에 하나씩, 검색 사이 10~20초 간격, 강제 스크롤 최소화 — f12_live 실측상 짧은 간격·과도한 스크롤이 차단 트리거).
   - **차단 조기 판정(중요)**: `page.goto` 응답의 `resp.status` 가 **405/418/429/403** 이면 즉시 차단으로 보고 중단한다(우회 금지). 스크립트 실행 전에 하네스에서 상태코드로 먼저 거른다. f12_capture 도 `httpBlocked`/`blockStatuses` 를 함께 반환한다.
   - ① 카테고리·연관어: `<skill>/scripts/naver_search_extract.js` 내용을 읽어 `await page.evaluate(src)`.
   - ② F12 패킷(terms·intersectionTerms·카테고리 relevance):
     ```js
     const f12 = String(await fs.readFile('<skill>\\scripts\\naver_f12_capture.js'));
     const ev = await page.evaluate(`(${f12})(${JSON.stringify({ target: kw })})`);
     ```
     각 키워드 결과를 세션 작업폴더의 `<workDir>\f12\f12_<키워드>.json` 로 저장한다(수집시각·URL·경로 포함). `f12\` 폴더가 없으면 만든다 — §2-④/⑤ 의 `--in-dir`/`--f12-dir` 가 이 폴더를 읽는다(다른 산출물과 섞이지 않게 하위폴더로 분리). 상위 5~8개(confidence high 우선)는 초기 검색 seed다. 그 결과의 관련어와 새롭고 적합한 후보를 추가 검색해 포화 기준까지 넓힌다. `연결형` 판별이 필요하면(예: 생유산균) `생 유산균`처럼 띄운 변형도 한 번 더 검색해 같은 폴더에 저장한다(builder 가 자동으로 연결형 판정에 사용).
   - ③ (선택 F12 경로 전용) 구형 메이커 셀링 도우미 보조 스크립트: F12 분석을 요청받은 경우에만 확장이 활성이면 `<skill>/scripts/maker_helper_extract.js`를 F12 보조자료로 읽을 수 있다. 기본 등록 경로는 canonical `maker_ui.json` 직접 추출이며 이 단계를 사용하지 않는다. 확장 파일은 수정하지 않는다.
   - ④ 카테고리 말단 확정(강의 §1): 위에서 저장한 검색결과 JSON(`naver_search_extract.js`·`naver_f12_capture.js` 출력)들을 그대로 넣어 relevance 를 합친다. 입력 JSON은 에이전트가 만들지 않는다 — F12/검색 단계에서 저장한 파일을 경로로 넘기기만 한다.
     ```
     python "<skill>\scripts\naver_category_pick.py" --in-dir "<workDir>\f12" --product-use "<상품 실제 용도>" --out "<workDir>\naver_category.json"
     ```
     출력의 `leafCandidates`(leaf·relevance·`parentChildConnected`·`nearOne`), `keywordAgreement`, `warnings` 를 카테고리 확정 근거로 쓴다. `verdict:"판정불가"`(데이터 없음/차단)면 카테고리를 강행하지 말고 스토어 카테고리 검색창에서 사용자 확인. 서로 다른 키워드의 카테고리를 임의 조합하지 않는다.
   - ④' (선택) 검색량 보강: 네이버 검색광고 API 자격증명(`NAVER_SEARCHAD_API_KEY`/`NAVER_SEARCHAD_SECRET`/`NAVER_SEARCHAD_CUSTOMER_ID`)이 환경변수에 있을 때만.
     ```
     python "<skill>\scripts\naver_searchad_volume.py" --check                 # 미설정이면 이 단계 건너뜀
     python "<skill>\scripts\naver_searchad_volume.py" --keywords "유산균,질유산균,..." --out "<workDir>\vol.json"
     ```
     `--check` 가 `allSet:false` 면(자격증명 없음) 검색량 없이 진행하고 아래 `--search-volume` 인자를 뺀다(스크립트는 미설정 시 `available:false`+exit 0 로 파이프라인을 막지 않음). 자격증명은 환경변수 전용, 파일에 저장 금지.
   - ⑤ 이호 판정 + 상품명·태그 조립(표준 라이브러리):
     ```
     python "<skill>\scripts\naver_title_builder.py" --f12-dir "<workDir>\f12" --facts "<workDir>\registration_plan.json" [--search-volume vol.json] --out "<workDir>\title_build.json"
     ```
     출력의 `judgeTable`(키워드/판정 완성형·조합형·연결형·교집합·미적용/근거), `titleCandidates`(상품명 후보 2개, 글자수·단어별 근거), `tagCandidates`(태그 10개 후보), `excluded`(제외 단어·사유), `verification`(terms+intersection 검증)을 사용자 최종 확인표에 그대로 싣는다. `판정불가(terms 없음)` 키워드는 상품명·태그에 쓰지 않는다(추측 금지).
   - ⑥ 최종 상품명 검증(강의 2-5): 완성 상품명 전체로 다시 검색해 `naver_f12_capture.js` 를 `{ target: 상품명, title: 상품명 }` 으로 실행 → `ev.titleCheck` 의 `누락` 단어는 빼거나 교체, `intersection` 단어는 교집합 처리로 기록. 카테고리 relevance 가 여전히 1.0 근처인지 확인.
   - `blockedOrCaptcha`(또는 `httpBlocked`) 면 사용자에게 캡차/로그인을 요청하고 우회하지 않는다. `schemaNote` 가 "terms 키를 찾지 못함" 이면 `networkRequests` 목록과 함께 `memory/sites/search.shopping.naver.com.md` 에 기록하고, 그 상품은 terms 판정을 "판정불가"로 표시해 최종 확인표에 알린다.
   - 결과는 모두 plan 의 `naver.categoryEvidence`, `naver.f12Evidence`(수집시각·URL·JSON 경로), `naver.keywordJudgements`(title_build.judgeTable)에 저장.
3. 네이버: Maker 결과와 원상품 사실로 카테고리·상품명·태그 10개를 정하고 화면 입력을 시작한다. F12 `title_build`나 상세 keyword judgement 표를 필수로 만들지 않는다.
4. 쿠팡 선택 SEO 보강: 기본 경로에서는 Wing 추천어와 상품 사실로 확인된 관련 검색어를 가능한 만큼 쓴다. 아래 helper와 장시간 native-query 확장은 사용자가 추가 SEO 조사를 요청한 경우에만 쓴다.
   ```
   python "<skill>\scripts\coupang_helper.py" --plan "<workDir>\registration_plan.json" --sources-json "<workDir>\sources.json" --out "<workDir>\coupang_build.json"
   ```
   `exposureName`(옵션값·브랜드 제거된 제품명), `searchTerms`(출처가 확인된 고유 후보어), `excluded` 는 §2-6 의 `apply_to_plan.py` 가 plan 의 `coupang.productName`/`coupang.tags`/`coupang.categoryPath`/`coupang.attributes` 에 병합한다(손으로 편집하지 않는다). 색상은 쿠팡 표준명(화이트/블랙/그레이).
   - `sources.json` 생성, 네이티브 쿼리 포화 조사, 다중 검색면 조사 및 term별 출처 원장 보존 절차는 **선택적 심층 SEO 연구(OPTIONAL SEO research)** 절차이며, 기본 Coupang 등록 워크플로우의 필수 요구사항이 아니다.
   - 기본 등록에서는 Wing 등록화면에 표시되는 추천어와 확인된 상품 사실에서 관련 검색어를 즉시 입력한다. 20개를 채우기 위한 장시간 확장 조사나 검색어 provenance JSON은 요구하지 않으며, 20개 미달은 WARN으로만 남긴다. 상품 사실에 없는 표현은 관측됐더라도 제외한다.
   - Wing 카테고리 검색창에 핵심어를 입력해 상위 1~3 후보의 경로와 말단 ID를 확인한다. 상품 용도와 맞고 선택 가능한 후보를 고른다. 전체 분류표/API를 수집하거나 전수 비교하지 않는다. 적합한 말단이 없으면 검색어를 좁혀 한 번 더 검색한다.
   - 카테고리 말단 확정: Wing 카테고리 검색/추천 화면에서 읽은 후보만 `candidates.json`(`{"candidates":[{"path":..,"code":..,"leaf":..,"topSeller":true|false}]}`)으로, 화면 필수옵션/필터 스펙은 `attributes.json`(`{"required":[{"name","type","unit","values":[]}]}`)으로 만들어 넣는다(경로를 지어내지 않는다). 상품 사실은 `product.json`(`{productName, naverCategoryPath, keywords, options, attributesEvidence}`).
     ```
     python "<skill>\scripts\coupang_category_pick.py" --product-json "<workDir>\product.json" --candidates-json "<workDir>\candidates.json" --attributes-json "<workDir>\attributes.json" --out "<workDir>\coupang_category.json"
     ```
     출력의 `categoryCandidates`(score·reasons), `attributes.filled/empty`, `droppedOptions`(품절·판매종료) 를 근거로 말단·필수옵션을 채운다. 후보가 없으면 `categoryCandidates=[]` — 임의 경로를 만들지 않고 화면에서 다시 읽는다.
5. 가격: plan.pricing.suggested(확인된 원가가 있을 때) 또는 사용자가 준 판매가를 사용하고, 근거를 `pricing.salePriceSource`에 기록한다. 경쟁 상품의 판매가는 참고값이지 원가가 아니다. 배송 정책은 seller profile/live form을 확인한다. 무료배송이면 배송비 포함, 유료배송이면 실제 승인 배송비를 반영하고 이전 상품 설정을 임의 복사하지 않는다.
6. 선택된 JSON 분석 경로에서는 중간 산출물을 `apply_to_plan.py`로 병합할 수 있다. 기본 Maker 경로에서는 `apply_to_plan.py --run-audit`를 요구하지 않는다. 직접 seller UI에 입력하고 필수값을 확인한다. 사용자가 F12/SEO 분석을 명시적으로 요청한 경우에만 plan 병합과 전체 감사를 선택한다.
```
python "<skill>\scripts\apply_to_plan.py" --plan "<workDir>\registration_plan.json" --title-build "<workDir>\title_build.json" --naver-category "<workDir>\naver_category.json" --coupang "<workDir>\coupang_build.json" --coupang-category "<workDir>\coupang_category.json" --run-audit
```
- 병합 필드: `naver.productName/tags/keywordJudgements/categoryPath/categoryEvidence`, `coupang.productName/tags/categoryPath/attributes`, `seoAudit`. 상품명 후보 선택은 `--title-index`(기본 0), 카테고리는 `--leaf-index`/`--coupang-cat-index`(기본 0).
- F12/SEO 분석 요청이 있을 때 전체 검사 리포트를 만들려면 `seo_audit.py --plan` 을 실행한다:
```
python "<skill>\scripts\seo_audit.py" --plan "<workDir>\registration_plan.json"
```
F12 모드에서만 terms 판정과 IHO WARN을 검토한다. 기본 경로에서는 상품 사실, 공식 플랫폼 하드 한도, 브랜드 시작 규칙, 실제 seller 필수값에 해당하는 항목만 해결한다. 쿠팡 검색어 20개 미달과 선택 SEO 개선은 BLOCK이 아니다.

### 실행/차단 실패 시 동작
- `prepare_product.py` 는 Windows cp949 콘솔에서도 stdout 이 비지 않도록 UTF-8 로 출력한다. 그래도 stdout 이 비면 `<workDir>\registration_plan.json` 을 직접 읽어 blockers/needsUser 를 확인한다(exit 2 = blockers 있음, 준비 실패 아님).
- 셸 stdout 이 자주 비므로, 스크립트 결과는 항상 `--out` 파일로 남기고 그 파일을 다시 읽어 판단한다.
- Maker UI가 기본 경로이므로 F12 차단은 등록 blocker가 아니다. F12를 명시적으로 요청했을 때만 차단·CAPTCHA를 우회하지 않고 중단한다.
- 핵심 키워드 `판정불가`와 카테고리 relevance 검사는 F12 선택 경로에만 적용한다. Maker 경로에서는 Maker 추천을 live 카테고리 선택창에서 확인한다.
- `salePrice` 가 null 이면 화면 입력 단계로 넘어가지 않는다(가격 미확정 게이트).

## 3. 화면 입력
- 네이버: `references/naver-smartstore.md` 순서대로. 판매자센터 로그인은 사용자가 직접.
- 쿠팡: `references/coupang-wing.md` 순서대로. 윙 로그인은 사용자가 직접.
- 둘 다면 네이버 → 쿠팡 순. 각 입력 후 스냅샷으로 값이 들어갔는지 확인하고, 기본값(원산지 국산, 배송 무료, 반품 0원 등)이 남아 있지 않은지 본다.
- Wing의 `AI로 검색필터 채우기`는 선택 기능이다. 사용하면 화면상 필수 속성과 상품 사실만 확인하고, 선택 필터 전체 검수는 게이트로 삼지 않는다. 버튼이 없으면 실행했다고 기록하지 않는다.
- 버튼 ref 가 불안정하면 visual-browse 로 좌표 클릭 후 반드시 재확인.

## 4. 최종 확인 → 등록
마켓별 두 개의 표(키워드 판정표 + 최종 확인표)는 손으로 쓰지 말고 스크립트로 만든다:
```
python "<skill>\scripts\build_confirm_table.py" --plan "<workDir>\registration_plan.json" --plan "<workDir>\registration_plan_2.json" --out "<workDir>\confirm.md"
```
- 상품이 하나면 `--plan` 하나만 준다. Maker 기본 경로에서는 `--title-build`/`--coupang` JSON을 요구하지 않는다. F12 분석 모드일 때만 해당 옵션을 추가한다.
- `--markets naver,coupang` 로 표시 마켓을 고를 수 있다(기본: plan 에 있는 것).
- 빈 값은 `미확정`, seo_audit ok 라도 상품명이 비면 `검사 대상 없음`, blockers/needsUser 는 표 상단에 노출된다. 값을 발명하지 않는다.
- 필수 6개 필드 또는 실제 seller form/법률의 필수값이 미확정이면 해당 상품에 `제출 불가`와 정확한 이유를 표시한다. 선택값은 제출을 막지 않는다. 검색어별 provenance 파일을 따로 만들어 사용자에게 나열하지 않는다.
- 생성된 `confirm.md` 를 사용자에게 그대로 보여주고 확인을 받는다.

표 구성(build_confirm_table 출력):

(A) 키워드 판정표 (`title_build.json` judgeTable): 사용자가 F12/이호 분석을 요청한 경우에만 표시한다.

| 키워드 | 판정 | 근거(terms/카테고리) | 상품명/태그 반영 |
|---|---|---|---|
| 유산균 | 완성형 | terms 통째 | 상품명 0번 |
| 질유산균 | 조합형 | 질/유산균 분해 | 상품명(질 유산균 인접) |
| 유산균추천 | 미적용 | '추천' 소멸 | 제외 |

(B) 최종 확인표: 상품명·카테고리·가격·대표/추가 이미지·상세페이지·태그와 seller 필수값(브랜드, 제조사, 원산지, 고시, 배송/반품, A/S, 필수 옵션/속성)을 표시한다. 가격 근거, 기존 중복 상태, 제목·태그 출처, 태그 N/10, 쿠팡 검색어 N/20(max 경고), KIPRIS 자체 브랜드 생략, Wing 카테고리 상위 3개 ID·경로와 선택 이유를 포함한다. 선택 필터·전체 SEO 감사·term별 provenance는 요구하지 않는다.

사용자가 확인표를 승인한 뒤 현재 스냅샷에서 최종 버튼을 다시 식별한다. 표 승인 후 값이 바뀌면 변경분을 보여주고 재승인받는다. 신규 Wing 등록은 `상품등록`, 기존 상품 수정은 `수정 및 검수 요청`일 수 있다. 수정 확인창에 `수정요청 하시겠습니까?`가 표시되면 승인된 표와 같은 변경인지 확인한 뒤에만 `확인`을 누른다. 예상과 다른 동작·대상·값이면 멈추고 다시 승인받는다. 임시저장은 사용자가 명시한 경우에만 한다.
제출 뒤 네이버 상품번호, Coupang 등록상품ID·노출상품ID·vendorItemID를 캡처해 `plan`에 기록하고 보고한다. 제출 완료 알림만으로 완료 처리하지 않는다. 판매자 목록에서 승인상태·판매상태·실재고를 확인하고, 공개 상품페이지에서 품절 여부와 장바구니·바로구매 버튼이 활성인지 확인한다. 요청된 검색어·필터를 입력했다면 그 저장 여부도 확인한다. 표 승인 이후 값이 바뀌면 재승인 뒤 진행한다.

## 5. Argo 자동 연결과 기록
- 사용자가 별도로 말하지 않아도 등록 시작 전에 Argo `끄쫀꾸` 허브와 원본 상품·SEO·등록 기록을 읽는다.
- 상품 폴더, 원상품 근거, Maker 출처(또는 사용자가 요청한 F12 분석), 입력값, 사용자 승인 경계, 화면 검증, 등록 결과와 실제 차단 사유를 작업 종료 시 Argo 핸드오버로 저장한다.
- 네이버와 쿠팡은 각각 별도 기록을 남기고, 임시저장·검증완료·실제등록을 혼동하지 않는다.
- 로그인정보, 인증번호, 비밀번호, 토큰, API 키, 쿠키는 Argo에 저장하지 않는다.
- 실제 Naver `저장하기`·Coupang의 최종 제출 버튼은 기존처럼 최종 확인 후에만 실행한다.

## 6. 기존 메모리 기록
- 새로 알게 된 화면 동작은 `memory/sites/smartstore.naver.com.md` 또는 `memory/sites/wing.coupang.com.md` History 에 추가.
- 결과는 `memory/projects/naver-coupang-registration.md` History 에 한 줄 기록(상품폴더, 마켓, 상품번호, 이슈).

## 규칙
- 브랜드/판매자명(예: 더이안)은 상품명·태그·홍보 문구에서 제거, 고시의 제조자·수입자·제조국은 사실대로 유지.
- 상세 이미지·대표 이미지는 메이커 원본 또는 사용자가 제공했거나 정확히 일치하는 기존 활성 상품의 원본만 사용한다. 기존 listing 재사용 시 같은 상품인지 확인한다. 사용자가 이미 준 이미지와 입력법은 대화·Argo·Aside 기록에서 먼저 찾아 재사용하고, 경쟁사나 다른 형태의 상품 이미지는 쓰지 않는다. 임의 SEO 카드 이미지를 만들거나 추가하지 않는다.
- 이호 기준을 실제로 적용한 부분과 추정한 부분을 구분해서 보고한다.
- 근거 없는 인증·원산지·속성·수식어(추천/인기/신형 등) 금지. 가구매·리뷰조작·트래픽·판매상태 토글·캡차 우회 금지.
- 쿠팡 해외구매대행은 해외 출고지·인보이스가 있어야 가능하다. 국내(인천) 출고 위탁상품은 일반배송으로 등록한다.
