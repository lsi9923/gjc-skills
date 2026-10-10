# GJC 사용자 영구 지침 (User Global Guidelines)

## 0. 행동 양식 및 태도 (절대 불변 원칙)
- 질문/설명 모드로 빠지지 말고 **즉각 실행(Action Mode)**으로 전환한다.
- 핑계, 어설픈 겉핥기식 답변, 풀린 태도를 엄격히 금지하며 철저하게 실행 위주로 움직인다.

## 1. 필수 지침: 답변 종료 시 토큰 현황 리포트 상시 표기
사용자의 지침에 따라 모든 작업 완결 및 답변 끝에는 반드시 토큰 사용량, 잔여 쿼터 및 컨텍스트 현황 블록을 포함하여 보고한다.
이 설정은 세션 재시작 후에도 영구 유지된다.

## 2. 해외구매대행 및 사입 유망 상품 50선 추천 엑셀 자동화 (`sourcing-top50-curator`)
사용자가 데이터 파일(`ProductIdeaRadar`의 `cycle_ideas`, `ideas`, `catalog_ideas` CSV/XLSX 등)을 주면서 "50개 추천해줘", "50개 추려서 가져와", "엑셀 만들어서 작업해"라고 지시하면 질문(`deep-interview` 등) 없이 즉시 아래 스킬 스크립트를 실행하여 `구매대행 추천`(25개)·`사입 추천`(25개)·`전체 통합 TOP 50` 탭과 이미지 URL(텍스트)이 포함된 바탕화면 엑셀 파일을 생성한다:
```bash
python C:/Users/imda0/.gjc/agent/skills/sourcing-top50-curator/scripts/generate_top50_excel.py <입력경로들> --out "C:/Users/imda0/Desktop/해외구매대행_사입_추천상품_TOP50.xlsx"
```
생성 규격·근거/추정 구분·이미지 검증 및 4개 시트 계약은 `C:/Users/imda0/.gjc/agent/skills/sourcing-top50-curator/SKILL.md`를 따른다. 확인되지 않은 시세·마진을 실측처럼 표현하거나 내부 진단용 상태 컬럼을 엑셀에 내보내지 않는다.

## 3. 네이버 스마트스토어·쿠팡 윙 상품 등록 및 구매대행 정리 (`naver-coupang-register` 외)
사용자가 "네이버 쿠팡 등록해", "네이버 등록해줘", "쿠팡 등록해줘", "스마트스토어 등록", "윙 등록", "완료된폴더 N번 등록", "상품명 텀스", "이호 방식 상품명", "구매대행 정리/등록" 등을 지시하면 더미 JSON이나 단순 복붙용 텍스트만 던지고 끝내지 않고, 아래 등록 스킬 체계를 즉시 로드하여 실행한다:
- **통합 실전 등록 스킬 (`naver-coupang-register`)**: `C:/Users/imda0/.gjc/agent/skills/naver-coupang-register/SKILL.md`
  - 상세페이지 메이커 완료폴더(`C:\Users\imda0\Downloads\완료된폴더\<N>`) 기반 `prepare_product.py` → 네이버 F12(`naver_f12_capture.js` / `naver_search_extract.js` / `maker_helper_extract.js`) → 카테고리 말단 확정(`naver_category_pick.py`) → 이호 5분류 상품명·태그 조립(`naver_title_builder.py`) → 쿠팡 노출상품명·검색어·카테고리(`coupang_helper.py` / `coupang_category_pick.py`) → 플랜 병합 및 SEO 감사(`apply_to_plan.py --run-audit` / `seo_audit.py`) → 최종 확인표 생성(`build_confirm_table.py`) → 판매자센터/윙 등록 화면 입력. (최종 Naver `저장하기`/Wing 화면상 제출 버튼—현재 `상품등록`—은 반드시 사용자 최종 확인 후 실행)
- **네이버 레거시·참고 스킬 (통합 등록에서 독립 실행하지 않음)**:
  - `C:/Users/imda0/.gjc/agent/skills/naver-seo-sudong-skill/SKILL.md`
  - `C:/Users/imda0/.gjc/agent/skills/naver-shopping-listing/SKILL.md`
  - `C:/Users/imda0/.gjc/agent/skills/naver-rank-probe/SKILL.md`
- **쿠팡 레거시·참고 스킬 (통합 등록에서 독립 실행하지 않음)**:
  - `C:/Users/imda0/.gjc/agent/skills/coupang-sudong-skill/SKILL.md`
- **Argo Vault 자동 기록 (`argo-vault-sync`)**:
  - `C:\Users\imda0\.argo\vault`의 `끄쫀꾸` 프로젝트 핸드오버 연동)

### 통합 등록 실행 규칙
- 네이버·쿠팡을 함께 또는 각각 등록할 때 `naver-coupang-register`가 유일한 실행 절차다. `naver-seo-sudong-skill`과 `coupang-sudong-skill`은 이 절차와 충돌하지 않는 참고자료로만 읽고 독립 등록 흐름으로 실행하지 않는다.
- 항상 기존 상품·원본 이미지·사용자가 이미 제공한 작업법을 먼저 확인하고, 근거 수집부터 실제 판매자 화면 입력·최종 승인·실제 제출·공개 판매상태 확인·Argo 기록까지 완료한다. 임시저장이나 확인표 작성만으로 종료하지 않는다.
- 요청한 각 마켓의 검색면을 포화 조사한다. 네이버는 F12 `terms`/`intersectionTerms`, 연관검색어, 비광고 상품 제목·태그를 조사한다. 쿠팡은 Wing 추천·인기검색어, 쿠팡 자동완성·관련검색어를 여러 핵심 쿼리와 띄어쓰기 변형으로 조사한다. 현재 입력 한도까지 상품과 맞는 고유어만 채우고, 검색어마다 실제 출처·쿼리·근거 경로·적합 이유를 기록한다. 다른 마켓의 검색 결과는 해당 마켓에서 재확인하기 전까지 후보일 뿐이다.
- 쿠팡은 20개 한도, 네이버는 현재 입력 한도(통상 10개 태그)를 기준으로 근거 있는 검색어를 최대한 채운다. 모든 관련 출처와 쿼리를 다 조사하기 전에는 부족하다고 결론 내리지 않는다. 출처를 모두 조사해도 한도에 못 미치면 부족 수와 차단·부재 근거를 기록하고 제출을 막는다. 무관어·중복어·관측되지 않은 조합어를 만들어 채우지 않는다.
- 필수 판매자 필드와 확인표에는 설명 없는 공란을 두지 않는다. 원상품·기존 상품·공식 자료·판매자 설정을 끝까지 확인하고, 필수값이 여전히 없으면 정확한 BLOCKER로 제출을 중단한다. 근거가 없는 선택 항목은 빈칸 대신 `미확정: 사유`로 표시하되 값을 발명하지 않는다.
- Wing 검색필터의 `AI로 검색필터 채우기`를 실행하고 모든 적용값을 원상품 근거와 대조한다. 자동 입력값은 기본 신뢰하지 않으며, 재진입 후에도 필터와 검색어가 저장됐는지 확인한다. 검색어가 20개 미만이면 `TAG_COUNT_UNDER_TARGET` BLOCK을 해결하기 전 제출하지 않는다.
- 쿠팡 카테고리를 고르기 전 전체 공식 Wing 분류표/API를 확보하고 출처·버전·날짜·행 수를 기록해 전체 후보를 비교한 뒤 live picker에서 말단을 확인한다.

## 4. 키프리스(KIPRIS) 상표권 공식 직접 검색 절대 준수 (네이버 검색 절대 금지)
- 해외구매대행 및 사입 소싱, 스마트스토어·쿠팡 상품 등록 시 상표권 검증은 **포털(네이버/다음/구글 등) 검색으로 절대 때우지 않는다**.
- 반드시 **특허청 특허정보검색서비스(KIPRIS) 공식 웹사이트(`www.kipris.or.kr`) 및 상표(TM) 데이터베이스에 직접 접속하여 상표 출원·등록 여부, 출원인, 상품분류(류)를 확인**한다.
- 엑셀, 리포트, 등록 플랜에 들어가는 상표권 조회 링크는 반드시 KIPRIS 공식 상표 직결 URL이어야 한다:
  - `http://www.kipris.or.kr/khome/search/searchResult.do?searchKind=totalSearch&searchRight=trademark&queryText=<키워드>&queryTextTop=<키워드>&expression=<키워드>`
- CLI 및 자동 스크립트 실행 시 KIPRIS 공식 상표 조회 도구를 활용한다:
  - `python C:/Users/imda0/.gjc/agent/skills/korean-patent-search/scripts/trademark_search.py --query <브랜드명>`

## 5. 상품 텍스트 검색 실패 시 이미지 추출 & 비전 딥 리서치(Deep Research) 의무 실행
- 해외구매대행·사입 상품을 긁어오거나 소싱처/알리/타오바오/1688에서 상품 정보를 가져올 때, **상품명(이름)이나 텍스트 키워드로 검색되지 않거나 불명확할 경우 "상품을 찾을 수 없습니다"로 작업을 포기하거나 누락하지 않는다**.
- **반드시 상품 썸네일·대표 이미지·상세페이지 이미지를 로컬로 다운로드/추출**하여 **비전 멀티모달 딥 리서치 파이프라인(`product_image_deep_research.py`)**을 즉시 가동한다:
  - 실행 명령:
    ```bash
    python C:/Users/imda0/.gjc/agent/skills/sourcing-top50-curator/scripts/product_image_deep_research.py --name "<상품명>" --image "<이미지경로_또는_URL>" --price <국내목표가>
    ```
  - **비전 딥 리서치 필수 산출물**:
    1) 시각적 외형(형상, 구조, 부속품 구성, 결합 메커니즘, 표면 각인 텍스트) 정밀 판독
    2) 1688/타오바오 검색용 공용금형(公模) 최적화 중국어 소싱 키워드 및 다이렉트 링크 생성
    3) 1688 이미지 검색(拍立淘) 프로토콜 및 업로드용 고화질 이미지 경로 제공
    4) KIPRIS 공식 상표권 직접 검색 링크 및 침해 여부 교차 검증
    5) 1688 예상 도매가(위안) 기반 수입원가 환산 및 목표 순마진율 40%+ 실측 검증
    6) KC/식약처/생활화학 인증 우회 및 최소비용 통관 전략
    7) 1688 중국 공장 왕왕/위챗 발송용 중문 및 한국어 문의문 생성

## 6. 전체 스킬 GitHub 자동 동기화 (`gjc-skills`)
- 에이전트 스킬 컬렉션 및 지침은 GitHub 전용 저장소(`https://github.com/lsi9923/gjc-skills`)로 상시 관리·백업된다.
- 사용자가 "스킬 깃에 올려", "스킬 백업해", "깃 동기화해"라고 요청하거나 스킬 개선 완료 시 아래 명령을 실행하여 원클릭 동기화한다:
  ```bash
  python C:/Users/imda0/.gjc/agent/skills/sync_skills_to_git.py
  ```
