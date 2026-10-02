# 쿠팡 윙 상위노출 수동 상품등록 전문 스킬 (`coupang-sudong-skill`)

쿠팡 윙(Coupang Wing)의 11대 섹션 48개 입력 필드를 **단 하나도 빠짐없이 꽉 채워서** 등록하는 전문 자동화 스킬입니다.

---

## 1. 아키텍처 및 모듈 구성 (확장 가능한 모듈화 설계)

본 스킬은 추가 기능(소싱 플랫폼 확장, 자동 번역기, 이미지 슬라이서 등)을 레고 블록처럼 쌓아 올릴 수 있도록 모듈화되어 있습니다:

```text
coupang-sudong-skill/
├── SKILL.md                          # GJC 런타임 스킬 명세 및 트리거 규칙
├── README.md                         # 아키텍처 및 확장 가이드
├── contracts/
│   └── coupang-listing-payload.schema.json  # 11대 섹션 48개 필드 전수 JSON Schema
├── docs/
│   └── coupang-wing-fields.md        # 11대 섹션 48개 필드 세부 명세서
├── scripts/
│   ├── coupang_title_composer.py     # 60~90자 롱테일 고밀도 상품명 조합 엔진
│   ├── coupang_tags_generator.py     # 20개 검색어 태그 빈자리 0개 생성기
│   ├── coupang_category_matcher.py   # 카테고리 매칭 및 고시/속성 템플릿 엔진
│   └── run_coupang_pipeline.py       # 4단계 엔드투엔드 파이프라인 조립기
└── test/
    └── test_coupang_pipeline.py      # 파이프라인 정합성 및 스키마 검증 테스트
```

---

## 2. 쿠팡 윙 5대 핵심 룰

1. **상품명 100자 롱테일 조합**: 네이버 25~30자 제한을 풀고 60~90자 고밀도 유입 키워드 구성.
2. **검색어 20개 풀장착**: 20개 빈칸 없이 연관 키워드 전수 입력 (각 20자 이내).
3. **카테고리별 동적 속성(Attributes) 매핑**: 모바일 앱 필터 검색 노출 필수 확보.
4. **상품정보제공고시 35개 군 매칭**: 카테고리별 고시 항목 매핑 및 `'상세페이지 참조'` 안전 방어.
5. **해외구매대행 AGENT_BUY 규칙**: 개인통관고유부호(PCC) 필수 수집, 바코드 없음 사유 체크, 출고소요일 7~14일 보정.

---

## 3. 테스트 및 실행 방법

```bash
# 단위 및 통합 정합성 테스트 실행
python test/test_coupang_pipeline.py

# 파이프라인 실행
python scripts/run_coupang_pipeline.py
```
