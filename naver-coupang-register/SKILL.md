---
name: "naver-coupang-register"
description: "네이버 스마트스토어·쿠팡 윙 상품 등록 실행 스킬. 사용자가 별도로 스킬명을 말하지 않아도 네이버·쿠팡 등록 작업에 자동 사용한다. \"네이버 쿠팡 등록해\", \"네이버 등록해줘\", \"쿠팡 등록해줘\", \"스마트스토어 등록\", \"윙 등록\", \"상품등록\", \"완료된폴더 N번 등록\", \"상품명 텀스\", \"terms 분석\", \"완성형 조합형\", \"이호 방식 상품명\", \"메이커 셀링 도우미\" 요청 시 사용. 상세페이지 메이커 완료폴더(썸네일 1~5, detail_page, sections, source.json)와 이호 네이버 SEO 기준(F12 개발자도구 terms·intersectionTerms·카테고리 relevance)으로 카테고리·상품명·태그·고시·옵션·배송을 구성하고, 크롬 확장 '메이커 셀링 도우미'를 F12 근거를 보조하는 참고자료로 함께 읽으며, Aside 브라우저로 판매자센터/윙 등록 화면에 직접 입력한 뒤 최종 확인 후 등록한다. 모든 관련 진행·검증·결과는 Argo 끄쫀꾸에 자동 기록한다."
autoInject:
  url:
    - "sell.smartstore.naver.com/**"
    - "wing.coupang.com/tenants/seller-web/vendor-inventory/**"
---

# 네이버·쿠팡 상품 등록

더미 JSON이나 복붙용 텍스트만 주고 끝내지 않는다. 실제 등록 화면에 직접 입력한다. 단, 마지막 `저장하기`/`판매요청` 클릭은 사용자 최종 확인 후에만 한다.

`<skill>` = 이 SKILL.md 가 있는 폴더. 스크립트는 bash(PowerShell)에서 `python` 으로 실행한다(표준 라이브러리만 사용).

## 0. 입력 확정
- 대상: "완료된폴더 N번"/폴더 경로/상품 URL. URL만 받으면 `C:\Users\imda0\Downloads\완료된폴더\*\source.json` 의 url 상품번호로 폴더를 찾는다. 못 찾으면 상세페이지 메이커(`<skill>/config/seller_profile.json` sourceFolders.makerProgram)로 먼저 만들어야 한다고 알린다.
- 마켓: "네이버 쿠팡" = 둘 다, 한쪽만 말하면 그쪽만. 여러 폴더면 1개씩 순서대로(첫 상품 성공 확인 전 일괄 진행 금지).
- 엑셀이 함께 오면 행 순서 = 폴더 순서로 매칭하고 URL 상품번호를 대조한다. 어긋나면 멈춘다.

## 1. 준비 스크립트
작업폴더를 GJC 범용 폴더(`C:\tmp\reg-<폴더명>`) 또는 `aside.sessions.current()` 의 세션 폴더 아래 `tmp\reg-<폴더명>` 으로 정하고 실행:
```
python "<skill>\scripts\prepare_product.py" "<완료폴더\N>" --out "C:\tmp\reg-N" [--cost-krw 원가 | --cost-cny 위안]
```
- 결과 `registration_plan.json` 의 `blockers` 가 있으면 등록하지 않고 사용자에게 보고한다.
- `needsBrowser` 가 있으면(메이커 수집이 쿠팡 차단 페이지 등으로 실패) Aside 브라우저로 `source.url` 을 직접 열어 상품명·가격·옵션·고시표(제조자/제조국/인증)·브랜드를 읽어 plan.source 와 `cleanedName`·`notice`·`brand` 를 채운다. 여전히 열리지 않으면 1688 URL(`secondaryUrl`)과 섹션 카피로 후보만 만들고 사용자 확인을 받는다. 고시 사실값을 추측하지 않는다.
- `needsUser`(판매가/원가, A/S 전화, 공급방식 등)는 한 번에 모아서 묻는다. A/S 전화 등 고정값은 받으면 `config/seller_profile.json` 에 저장한다(비밀번호·인증번호·API secret 은 저장·요청 금지).
- 업로드는 반드시 plan 의 `upload\thumb_*.png`, `detail_page.png`, `section_*.png` 경로를 쓴다(세션 폴더 밖 경로는 setFiles 가 거부됨).
- 1688 옵션은 원문을 전부 자동 등록하지 않는다. 사용자가 쓰고 싶다고 지정한 옵션만 원문 의미와 한국어 상품 용어를 해설해 확인받고, 선택된 옵션만 네이버·쿠팡 입력값으로 구성한다. 선택이 불명확하거나 번역이 여러 의미면 임의 확정하지 않고 묻는다.

## 2. SEO 구성 (`references/seo-rules.md` 필독)
1. 대표 키워드 후보: plan 의 `keywordSeeds.seeds` (원상품명·제목 꼬리·메이커 섹션 제목·메이커 seo_keywords.json, 출처 표시됨)에 1688 중국어 제목(`keywordSeeds.from1688.title`)을 한국어 상품 용어로 번역한 후보를 더한다. 브랜드(`brand.removedFromMarketing`)는 제외. 이 단계의 키워드는 모두 '후보'다.
2. 네이버 F12(개발자도구) 근거 수집 — 이호 방식 그대로, 생략 금지. **모든 상품명·태그 확정 근거는 F12 다.**
   - 새 탭에서 `https://search.shopping.naver.com/search/all?query=<키워드>` 로 이동(사람처럼 한 번에 하나씩, 검색 사이 10~20초 간격, 강제 스크롤 최소화 — f12_live 실측상 짧은 간격·과도한 스크롤이 차단 트리거).
   - **차단 조기 판정(중요)**: `page.goto` 응답의 `resp.status` 가 **405/418/429/403** 이면 즉시 차단으로 보고 중단한다(우회 금지). 스크립트 실행 전에 하네스에서 상태코드로 먼저 거른다. f12_capture 도 `httpBlocked`/`blockStatuses` 를 함께 반환한다.
   - ① 카테고리·연관어: `<skill>/scripts/naver_search_extract.js` 내용을 읽어 `await page.evaluate(src)`.
   - ② F12 패킷(terms·intersectionTerms·카테고리 relevance):
     ```js
     const f12 = String(await fs.readFile('<skill>\\scripts\\naver_f12_capture.js'));
     const ev = await page.evaluate(`(${f12})(${JSON.stringify({ target: kw })})`);
     ```
     각 키워드 결과를 세션 작업폴더의 `<workDir>\f12\f12_<키워드>.json` 로 저장한다(수집시각·URL·경로 포함). `f12\` 폴더가 없으면 만든다 — §2-④/⑤ 의 `--in-dir`/`--f12-dir` 가 이 폴더를 읽는다(다른 산출물과 섞이지 않게 하위폴더로 분리). 후보 상위 5~8개(confidence high 우선)를 각각 검색해 모은다. `연결형` 판별이 필요하면(예: 생유산균) `생 유산균`처럼 띄운 변형도 한 번 더 검색해 같은 폴더에 저장한다(builder 가 자동으로 연결형 판정에 사용).
   - ③ (선택) 메이커 셀링 도우미 보조 근거: 확장이 활성이면 `<skill>/scripts/maker_helper_extract.js` 를 `page.evaluate(src)` 로 실행해 확장이 렌더한 텀 칩/카테고리/검색량/스마트스토어 태그를 읽는다. **F12 근거를 보조하는 참고자료로만** 병기하고, `available:false`(확장 없음/미로드)면 이 단계를 건너뛴다. 확장 파일은 수정하지 않는다.
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
3. 네이버: 카테고리 경로, 상품명(완성형 0번, 조합형 왼→오·거리 최소, 25~30자 권장), 태그 10개 확정. plan 의 `naver.productName`/`naver.tags`/`naver.keywordJudgements`/`naver.categoryPath` 는 손으로 편집하지 말고 §6 의 `apply_to_plan.py` 로 채운다(title_build/naver_category 산출물에서 병합). 상품명 후보가 2개면 `--title-index` 로 고르고, 최종 확인표에 판정표(키워드/판정/근거 JSON 경로)를 함께 보여준다.
4. 쿠팡: 노출상품명(옵션값 제외, ≤100자) + 검색어 최대 20개를 근거 있는 키워드로 보강:
   ```
   python "<skill>\scripts\coupang_helper.py" --plan "<workDir>\registration_plan.json" --keyword-json "<workDir>\title_build.json" --out "<workDir>\coupang_build.json"
   ```
   `exposureName`(옵션값·브랜드 제거된 제품명), `searchTerms`(F12 근거 통과 키워드 + 태그 후보에서만 채움 — 20개 미달이면 미달로 둠, 지어내기 금지), `excluded` 는 §6 의 `apply_to_plan.py` 가 plan 의 `coupang.productName`/`coupang.tags`/`coupang.categoryPath`/`coupang.attributes` 에 병합한다(손으로 편집하지 않는다). 색상은 쿠팡 표준명(화이트/블랙/그레이).
   - 검색어 소스 보강(선택): Wing 등록화면 `추천 검색어`·`인기검색어` 도구·쿠팡 자동완성에서 **화면에 실제로 뜬 단어만** 읽어 `sources.json`(`{"wingRecommended":[...],"wingPopular":[...],"coupangAutocomplete":[...],"naverF12":[...]}`)으로 만들고 `--sources-json` 으로 넘기면 소스 우선순위로 검색어를 귀속한다(같은 단어는 높은 소스 1회). 화면에 없으면 지어내지 않는다.
     ```
     python "<skill>\scripts\coupang_helper.py" --name "<노출상품명>" --sources-json "<workDir>\sources.json" --out "<workDir>\coupang_build.json"
     ```
   - 카테고리 말단 확정: Wing 카테고리 검색/추천 화면에서 읽은 후보만 `candidates.json`(`{"candidates":[{"path":..,"code":..,"leaf":..,"topSeller":true|false}]}`)으로, 화면 필수옵션/필터 스펙은 `attributes.json`(`{"required":[{"name","type","unit","values":[]}]}`)으로 만들어 넣는다(경로를 지어내지 않는다). 상품 사실은 `product.json`(`{productName, naverCategoryPath, keywords, options, attributesEvidence}`).
     ```
     python "<skill>\scripts\coupang_category_pick.py" --product-json "<workDir>\product.json" --candidates-json "<workDir>\candidates.json" --attributes-json "<workDir>\attributes.json" --out "<workDir>\coupang_category.json"
     ```
     출력의 `categoryCandidates`(score·reasons), `attributes.filled/empty`, `droppedOptions`(품절·판매종료) 를 근거로 말단·필수옵션을 채운다. 후보가 없으면 `categoryCandidates=[]` — 임의 경로를 만들지 않고 화면에서 다시 읽는다.
5. 가격: plan.pricing.suggested(원가가 있을 때) 또는 사용자가 준 판매가. 쿠팡은 무료배송이므로 배송비 포함 가격.
6. 중간 산출물을 plan 에 병합하고 검사한다. 각 스크립트는 자기 out 파일에만 쓰므로, `apply_to_plan.py` 로 근거값을 `registration_plan.json` 에 한 번에 옮긴다(값이 없으면 건드리지 않음 — 발명 금지). `--run-audit` 는 병합 후 seo_audit 를 실행해 결과를 `plan.seoAudit` 에 기록하므로 `build_confirm_table.py` 가 그대로 읽는다.
```
python "<skill>\scripts\apply_to_plan.py" --plan "<workDir>\registration_plan.json" --title-build "<workDir>\title_build.json" --naver-category "<workDir>\naver_category.json" --coupang "<workDir>\coupang_build.json" --coupang-category "<workDir>\coupang_category.json" --run-audit
```
- 병합 필드: `naver.productName/tags/keywordJudgements/categoryPath/categoryEvidence`, `coupang.productName/tags/categoryPath/attributes`, `seoAudit`. 상품명 후보 선택은 `--title-index`(기본 0), 카테고리는 `--leaf-index`/`--coupang-cat-index`(기본 0).
- `--run-audit` 대신 검사만 따로 보려면(BLOCK 확인 등) `seo_audit.py --plan` 을 실행한다:
```
python "<skill>\scripts\seo_audit.py" --plan "<workDir>\registration_plan.json"
```
BLOCK 이 0 이 될 때까지 고친다(고친 뒤 `apply_to_plan.py --run-audit` 재실행으로 `plan.seoAudit` 갱신). `IHO_HEAD_COMPLETE`(완성형 0번 아님)·`IHO_COMBO_ORDER`(조합형 왼→오 위배) WARN 이 뜨면 상품명 순서를 재조정한다. WARN/INFO 는 최종 확인 표에 표시한다.

### 실행/차단 실패 시 동작
- `prepare_product.py` 는 Windows cp949 콘솔에서도 stdout 이 비지 않도록 UTF-8 로 출력한다. 그래도 stdout 이 비면 `<workDir>\registration_plan.json` 을 직접 읽어 blockers/needsUser 를 확인한다(exit 2 = blockers 있음, 준비 실패 아님).
- 셸 stdout 이 자주 비므로, 스크립트 결과는 항상 `--out` 파일로 남기고 그 파일을 다시 읽어 판단한다.
- F12 가 차단(405/418/429)·캡차면 우회하지 않고 사용자에게 사람 통과를 요청한 뒤, 확장(메이커 셀링 도우미) 비활성 프로필·요청 간격 완화(10~20s)를 검토한다(확장 파일 수정 금지 — 비활성화는 파일 수정 아님).
- 핵심 키워드가 `판정불가` 이거나 카테고리 relevance 가 실제 상품 카테고리를 안 가리키면 상품명 확정을 강행하지 말고 사용자 확인을 받는다.
- `salePrice` 가 null 이면 화면 입력 단계로 넘어가지 않는다(가격 미확정 게이트).

## 3. 화면 입력
- 네이버: `references/naver-smartstore.md` 순서대로. 판매자센터 로그인은 사용자가 직접.
- 쿠팡: `references/coupang-wing.md` 순서대로. 윙 로그인은 사용자가 직접.
- 둘 다면 네이버 → 쿠팡 순. 각 입력 후 스냅샷으로 값이 들어갔는지 확인하고, 기본값(원산지 국산, 배송 무료, 반품 0원 등)이 남아 있지 않은지 본다.
- 버튼 ref 가 불안정하면 visual-browse 로 좌표 클릭 후 반드시 재확인.

## 4. 최종 확인 → 등록
마켓별 두 개의 표(키워드 판정표 + 최종 확인표)는 손으로 쓰지 말고 스크립트로 만든다:
```
python "<skill>\scripts\build_confirm_table.py" --plan "<workDir>\registration_plan.json" --title-build "<workDir>\title_build.json" --coupang "<workDir>\coupang_build.json" --out "<workDir>\confirm.md"
```
- `--markets naver,coupang` 로 표시 마켓을 고를 수 있다(기본: plan 에 있는 것).
- 빈 값은 `미확정`, seo_audit ok 라도 상품명이 비면 `검사 대상 없음`, blockers/needsUser 는 표 상단에 노출된다. 값을 발명하지 않는다.
- 생성된 `confirm.md` 를 사용자에게 그대로 보여주고 확인을 받는다.

표 구성(build_confirm_table 출력):

(A) 키워드 판정표 (`title_build.json` judgeTable):

| 키워드 | 판정 | 근거(terms/카테고리) | 상품명/태그 반영 |
|---|---|---|---|
| 유산균 | 완성형 | terms 통째 | 상품명 0번 |
| 질유산균 | 조합형 | 질/유산균 분해 | 상품명(질 유산균 인접) |
| 유산균추천 | 미적용 | '추천' 소멸 | 제외 |

(B) 최종 확인표: 카테고리, 상품명(글자수), 판매가/정상가, 옵션·재고, 대표/추가 이미지 수, 상세 이미지 수, 브랜드/제조사/원산지, 고시 요약, 배송·반품비, 태그/검색어, SEO 검사 WARN(IHO_HEAD_COMPLETE/IHO_COMBO_ORDER 포함), 검색품질 체크 결과.

사용자가 "등록"/"진행"이라고 하면 네이버 `저장하기`, 쿠팡 `판매요청`. "임시저장"이면 임시저장만. 사용자 확인 전에는 절대 클릭하지 않는다.
등록 후 상품번호(네이버), 등록상품ID·노출상품ID(쿠팡)를 캡처해 plan 에 기록하고 보고한다.

## 5. Argo 자동 연결과 기록
- 사용자가 별도로 말하지 않아도 등록 시작 전에 Argo `끄쫀꾸` 허브와 원본 상품·SEO·등록 기록을 읽는다.
- 상품 폴더, 원상품 근거, SEO/F12 판정, 입력값, 사용자 승인 경계, 화면 검증, 등록 결과와 차단 사유를 작업 종료 시 Argo 핸드오버로 저장한다.
- 네이버와 쿠팡은 각각 별도 기록을 남기고, 임시저장·검증완료·실제등록을 혼동하지 않는다.
- 로그인정보, 인증번호, 비밀번호, 토큰, API 키, 쿠키는 Argo에 저장하지 않는다.
- 실제 `저장하기`·`판매요청`은 기존처럼 최종 확인 후에만 실행한다.

## 6. 기존 메모리 기록
- 새로 알게 된 화면 동작은 `memory/sites/smartstore.naver.com.md` 또는 `memory/sites/wing.coupang.com.md` History 에 추가.
- 결과는 `memory/projects/naver-coupang-registration.md` History 에 한 줄 기록(상품폴더, 마켓, 상품번호, 이슈).

## 규칙
- 브랜드/판매자명(예: 더이안)은 상품명·태그·홍보 문구에서 제거, 고시의 제조자·수입자·제조국은 사실대로 유지.
- 메이커 상세페이지 이미지만 상세설명에 넣는다. 임의 SEO 카드 이미지를 만들어 넣지 않는다.
- 이호 기준을 실제로 적용한 부분과 추정한 부분을 구분해서 보고한다.
- 근거 없는 인증·원산지·속성·수식어(추천/인기/신형 등) 금지. 가구매·리뷰조작·트래픽·판매상태 토글·캡차 우회 금지.
- 쿠팡 해외구매대행은 해외 출고지·인보이스가 있어야 가능하다. 국내(인천) 출고 위탁상품은 일반배송으로 등록한다.
