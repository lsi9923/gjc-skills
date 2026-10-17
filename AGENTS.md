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
  - 기본은 Maker `maker_ui.json`에서 네이버 키워드 칩·카테고리·태그 10개를 읽고, 상품명은 원상품 사실과 칩으로 조립한다. Wing 실시간 카테고리 추천 상위 1~3개 중 선택 가능한 말단 ID를 고른 뒤 필수값을 판매자 화면에 입력한다. F12 terms 분석, 전체 taxonomy 수집, 20개 쿠팡 검색어, 전체 SEO JSON 감사는 요청되지 않으면 실행하지 않는다. 최종 확인표 승인 후 제출한다.
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
- 속도 우선 기본 경로: 네이버는 Maker Selling Helper의 실제 `maker_ui.json`에서 키워드 칩·카테고리 후보·태그를 읽고, 상품명은 원상품 사실과 관측 칩으로 작성한다. 태그 10개를 목표로 한다. F12 `terms`/`intersectionTerms` 패킷 수집은 사용자가 명시적으로 요청하지 않는 한 하지 않는다. Maker JSON은 실제 캡처·상품 query·세션만 확인하고 전체 스키마·검색량·선택 탭 감사를 등록에 요구하지 않는다.
- 쿠팡 카테고리는 Wing 실시간 카테고리 검색창의 상위 1~3개 추천 중 상품 용도에 맞는 선택 가능 말단 ID를 고른다. 맞는 후보가 없으면 검색어를 한 번 좁혀 재검색한 뒤, 동일상품의 기존 seller listing ID → 이미 기록된 공식 말단 ID → 정확히 일치하는 원상품의 공개 Coupang 경로 순으로 제한적으로 찾는다. 후보마다 공식 분류 트리 1회 조회 또는 공식 조회 1회로 말단·활성·용도를 확인하고 live form에서 선택한다. 전체 taxonomy/API 또는 약 5.5만 행 비교는 하지 않는다. 후보가 없으면 Coupang만 중단하고 다른 마켓은 계속한다. 후보가 충돌하면 확인표에 경로를 함께 표시해 사용자가 선택한다.
- 태그는 네이버 10개를 목표로 Maker 결과와 원상품의 확인된 표현에서 중복 없이 채운다. 쿠팡 검색어는 현재 화면의 추천어와 상품 사실에서 바로 채울 수 있는 만큼 사용하며, 20개 미달·검색면 포화 조사·term별 provenance JSON은 제출 blocker가 아니다. 무관어·타브랜드·상품에 없는 기능이나 규격을 만들어 넣지 않는다.
- 등록 완료 필수값은 상품명, 선택된 카테고리, 판매가격, 실제 상품 이미지, 상세페이지, 관련 태그다. 확인표는 이 필드와 판매자 화면이 실제로 요구하는 필수 입력만 간단히 보여준다. 선택 필드의 빈 JSON, 검색량, exhaustive audit, 20개 검색어는 제출 blocker로 승격하지 않는다. 다만 실제 제출 화면에서 필수로 표시되거나 법규상 필요한 값을 확인할 수 없으면 그 항목만 정확히 중단 사유로 남긴다.
- Wing의 `AI로 검색필터 채우기`는 보이면 실행할 수 있지만 선택 기능이다. 실제 카테고리 필수 속성만 상품 사실과 대조하고, 선택 필터의 전체 검수·재진입 감사는 완료 조건이 아니다.
- 요청된 여러 상품은 준비를 연속으로 진행하고 한 번에 간결한 통합 확인표로 묶는다. 각 상품의 필수값과 충돌을 모두 표시하고 사용자가 해당 목록을 승인한 뒤 실제 제출을 순차 진행한다. 확인표 승인 전 최종 제출은 하지 않는다.
- 쿠팡 Wing 중간저장 배너/목록 열기 조작 시 텍스트 노드 클릭으로 인한 `Node is not an Element (text node)` 에러를 방지하기 위해, 반드시 `page.getByText(/중간저장 된 내용/).first()` locator로 클릭한다. 실패 시 해당 요소의 `boundingBox()` 중심 좌표로 `page.mouse.click(x, y)`를 수행하며, 중간저장 목록 모달에 저장 행(`savedRows`)이 정상 표시되는지 검증한다.
- 쿠팡 Wing 중간저장 목록 행 '선택' 시 나타나는 초안 전환 경고(`입력하신 정보는 저장되지 않습니다...`)는 브라우저 네이티브 `confirm` 대화상자이므로 페이지 렌더링 및 CDP 명령을 전면 차단하여 `Timeout waiting for element to be ready` / `CDP viewport timeout`을 유발한다. 따라서 DOM에서 확인 버튼을 찾으려 하지 말고, 반드시 '선택' 클릭 직전에 `page.once('dialog', d => d.accept())` (유지 시 `dismiss()`) 리스너를 먼저 등록한 뒤 클릭한다. 폼에 해당 초안의 상품명이 표시되는지 검증하고, 2회 실패 시 즉시 중단하여 "사용자 등록 시 직접 변경"으로 결과표(`next-session-result.md`)에 기록한다.

## 4. 제3자 상표의 KIPRIS 공식 확인 (포털 검색 대체 금지)
- 해외구매대행 및 사입 소싱, 스마트스토어·쿠팡 상품 등록 시 상표권 검증은 **포털(네이버/다음/구글 등) 검색으로 절대 때우지 않는다**.
- 자체 브랜드 `끄롱마제`는 등록 중 KIPRIS 조회를 생략한다. 그 외 제3자·경쟁 브랜드 표장은 **특허청 특허정보검색서비스(KIPRIS) 공식 웹사이트(`www.kipris.or.kr`) 및 상표(TM) 데이터베이스에서 출원·등록 여부, 출원인, 상품분류(류)를 확인**한다.
- 엑셀, 리포트, 등록 플랜에 들어가는 상표권 조회 링크는 반드시 KIPRIS 공식 상표 직결 URL이어야 한다:
  - `http://www.kipris.or.kr/khome/search/searchResult.do?searchKind=totalSearch&searchRight=trademark&queryText=<키워드>&queryTextTop=<키워드>&expression=<키워드>`
- CLI 및 자동 스크립트 실행 시 KIPRIS 공식 상표 조회 도구를 활용한다:
  - `python C:/Users/imda0/.gjc/agent/skills/korean-patent-search/scripts/trademark_search.py --query <제3자 표장>`

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
  
## 7. NotebookLM 자동화 워크플로우 (노트북엘엠 / 노트북lm)
- 사용자가 "노트북엘엠", "노트북 엘엠", "노트북lm", "노트북 lm", "노트북 LM", "노트북LM", "notebook lm", "NotebookLM", "노트북엘앰", "노트북 엘앰" 등 띄어쓰기 여부와 무관하게 언급하며 자료 분석, 요약, 리서치, 팟캐스트, 영상, 퀴즈, 마인드맵 제작 등 작업을 지시하면 설명으로 빠지지 않고 즉시 `notebooklm` 도구/스킬/CLI를 가동하여 원스톱 자율 실행한다.
- **실행 절차**:
  1) `notebooklm auth check --json` 상태 확인 (미인증 시 `notebooklm login` 자동 호출)
  2) 작업별 전용 노트북 생성 (`notebooklm create "<주제명>"`) 및 선택
  3) 소스 자료(URL/PDF/유튜브/텍스트) 추가 (`notebooklm source add <자료경로>`) 또는 웹/드라이브 딥 리서치 (`notebooklm source add-research "<주제>" --mode deep --import-all`)
  4) 출처 기반 질의응답(`ask`) 또는 아티팩트 생성(`generate audio/video/quiz/flashcards/mind-map/slide-deck/report`)
  5) 생성물 로컬 파일 다운로드(`notebooklm download <종류> <경로>`) 및 사용자 인도 완료

## 8. Aside 브라우저 복구 및 창 활성화 규칙 (재부팅 대응)
- **증상**: 재부팅 후 OmO 또는 브라우저 조작 에이전트가 `Aside u0 프로필에 브라우저 창이 없음` 오류로 조작 불가한 경우.
- **원인**: Aside 프로세스는 백그라운드에 떠 있으나 메인 GUI 창(`MainWindowTitle`)이 생성/활성화되지 않음.
- **해결**: PowerShell에서 `Start-Process 'C:\Program Files\Aside\Application\Aside.exe'` 실행으로 창을 띄운 뒤 REPL에 재접속한다.
- **확인**: `Get-Process Aside | Where-Object { $_.MainWindowTitle }` 로 MainWindowTitle 있는 창 존재 여부를 반드시 확인한다.
- **Aside 사용자 로그인용 탭 실행 규칙 (보이는 창 띄우기)**:
  - **증상**: `aside repl openTab()`으로 로그인 탭을 열었다고 보고했으나 사용자 화면에는 보이지 않음.
  - **원인**: REPL 탭은 보이지 않는 백그라운드 자동화 세션에 열리고 세션 종료 시 소멸됨 (`listBrowserTabs` 빈 배열 반환).
  - **해결**: 사용자가 직접 로그인해야 하는 탭은 `aside repl openTab()`을 쓰지 않고, 보이는 창에 직접 띄우도록 PowerShell에서 실행한다:
    ```powershell
    Start-Process 'C:\Program Files\Aside\Application\Aside.exe' -ArgumentList <URL들>
    ```
  - **확인**: `Get-Process Aside | Where-Object { $_.MainWindowTitle }` 의 `MainWindowTitle`에 해당 사이트 제목이 표시되는지 검증하고 사용자 확인을 거친다.
