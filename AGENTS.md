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
  - 상세페이지 메이커 완료폴더(`C:\Users\imda0\Downloads\완료된폴더\<N>`) 기반 `prepare_product.py` → 네이버 F12(`naver_f12_capture.js` / `naver_search_extract.js` / `maker_helper_extract.js`) → 카테고리 말단 확정(`naver_category_pick.py`) → 이호 5분류 상품명·태그 조립(`naver_title_builder.py`) → 쿠팡 노출상품명·검색어·카테고리(`coupang_helper.py` / `coupang_category_pick.py`) → 플랜 병합 및 SEO 감사(`apply_to_plan.py --run-audit` / `seo_audit.py`) → 최종 확인표 생성(`build_confirm_table.py`) → 판매자센터/윙 등록 화면 입력. (최종 `저장하기`/`판매요청` 클릭은 반드시 사용자 최종 확인 후 실행)
- **네이버 수동등록·구매대행 고시 스킬 (`naver-seo-sudong-skill`, `naver-shopping-listing`, `naver-rank-probe`)**:
  - `C:/Users/imda0/.gjc/agent/skills/naver-seo-sudong-skill/SKILL.md`
  - `C:/Users/imda0/.gjc/agent/skills/naver-shopping-listing/SKILL.md`
  - `C:/Users/imda0/.gjc/agent/skills/naver-rank-probe/SKILL.md`
- **쿠팡 윙 수동등록·구매대행 설정 스킬 (`coupang-sudong-skill`)**:
  - `C:/Users/imda0/.gjc/agent/skills/coupang-sudong-skill/SKILL.md`
- **Argo Vault 자동 기록 (`argo-vault-sync`)**:
  - `C:\Users\imda0\.argo\vault`의 `끄쫀꾸` 프로젝트 핸드오버 연동)

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
