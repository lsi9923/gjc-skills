---
name: naver-rank-probe
description: 네이버쇼핑 랭킹 데이터를 직접 실측한다. 키워드의 카테고리 relevance, 상품명의 terms/intersectionTerms 매칭, 경쟁 상품 재고 차감(실판매 개수)을 스크립트로 뽑아 naver-shopping-listing에 넘긴다. 네이버 접근이 가능한 로컬 환경에서 사용.
---

# 네이버쇼핑 랭킹 실측 (probe)

`naver-shopping-listing` 스킬의 **실측 담당**. 그 스킬이 "F12로 확인해서 알려주세요"라고 하던 값을 여기서 직접 뽑는다.

**전제**: 이 스킬은 네이버에 접근 가능한 환경(사용자 로컬 머신 등)에서 돈다. 접근이 막힌 샌드박스에서는 동작하지 않으며, 그럴 땐 우회하지 말고 사용자에게 값을 요청한다.

## 스크립트

전부 이 스킬 폴더의 `scripts/` 아래에 있다. `nfetch.py`를 import 하므로 **반드시 그 폴더에서 실행**한다.

```bash
# GJC (사용자 전역)
cd ~/.gjc/agent/skills/naver-rank-probe/scripts
# GJC (프로젝트)
cd .gjc/skills/naver-rank-probe/scripts
# Claude Code
cd ~/.claude/skills/naver-rank-probe/scripts
```

| 스크립트 | 용도 | 대응 단계 |
|---|---|---|
| `relevance.py` | 키워드의 카테고리별 relevance | listing 1단계 (카테고리 확정) |
| `terms.py` | terms/intersectionTerms + 상품명 검증 | listing 2~3단계 (상품명) |
| `stock.py` | 경쟁 상품 재고 차감 = 실판매 개수 | listing 8~9단계 (벤치마킹) |

### 1. 카테고리 relevance

```bash
python3 relevance.py "트레이닝복"
python3 relevance.py "트레이닝복" --json --dump ./raw
```

출력: category1~4 각 후보의 relevance + 인덱스 짝맞춤 추천 경로.

해석 규칙:
- `1.0` = 적합도 만점. 그 레벨에서 다른 카테고리를 고르면 가점 0.
- `category2`의 n번 ↔ `category3`의 n번이 짝. **조합 전체**로 판단한다.
- `0.0x` 수준 = 사실상 노출 불가.
- 외부 솔루션(아이템스카우트 등)의 카테고리 **비율(%)은 등록 상품 수 통계일 뿐** relevance가 아니다. 실측값이 있으면 비율은 무시한다.

### 2. terms / 상품명 검증

```bash
python3 terms.py "햇완두콩"
python3 terms.py "질유산균" --title "여성 질유산균 30포 프리미엄"
```

`--title`을 주면 판정하는 것:
- terms / intersectionTerms 중 상품명에 **빠진 것**
- terms 등장 순서가 **좌→우 형태소 순서**와 맞는지
- 공백 포함 **25~30자(최대 35자)** 범위인지
- **중복 단어** 유무 (검색품질 체크 감점 위험)

사전 미등록어는 쪼개져 나온다(`햇완두콩` → `햇완두`+`완두콩`). 유사 확장도 함께 잡힌다(`연초필터` → `담배`·`필터`·`연초`). 그 구조를 역이용해 상품명을 구성한다.

### 3. 경쟁사 실판매 개수

```bash
python3 stock.py "<상품URL>" --log ./stock.csv     # 6시간 또는 1일 간격 반복
python3 stock.py --report ./stock.csv              # 차감량 리포트
```

주의: ERP·통합솔루션 셀러는 타 채널 판매·도매 출고·임의 재고 수정으로 재고가 급변한다. **차감분을 곧바로 판매량으로 단정하지 않는다.** 재고가 늘어난 구간은 리포트에 별도 표시된다.

## 실패했을 때 (중요)

네이버는 엔드포인트와 응답 구조를 수시로 패치한다. 스크립트는 키 이름으로 **재귀 탐색**하므로 경로 변경에는 강하지만, 엔드포인트 자체가 바뀌면 못 받는다.

실패 시 순서:

1. `--dump ./raw`로 원본 저장 시도 → 뭐가 오는지 확인
2. HTML(차단 페이지)이 오면 **TLS 위장**이 필요하다: `pip install curl_cffi` (설치돼 있으면 자동으로 우선 사용)
3. 그래도 안 되면 브라우저에서 해당 키워드를 검색하고 개발자도구 Network에서 **실제 요청 URL을 복사**해 `nfetch.py`의 `ENDPOINT_CANDIDATES` 맨 앞에 추가한다. 보정 1회면 이후 계속 동작한다.
4. `insane-search` 플러그인이 설치돼 있으면 그 fetch 체인(`python3 -m engine <URL>`)으로 폴백할 수 있다. 단 insane-search에는 쇼핑 relevance 추출 로직이 없으므로, **가져온 원본 JSON을 이 스크립트의 파서에 넣는 방식**으로 조합한다.

**절대 하지 않을 것**: 환경 정책이 네이버 접근을 막고 있는 경우, 그건 사이트의 봇 차단이 아니라 실행 환경의 제한이다. 다른 도구로 우회하지 말고 그 사실을 사용자에게 말하고 값을 요청한다.

## naver-shopping-listing과의 연동

```
[상품 URL 입력]
   ↓
listing 스킬: 스펙 추출 → 키워드 후보 도출
   ↓
probe 스킬: relevance.py  → 카테고리 확정
            terms.py      → 상품명 A/B안 검증 (통과할 때까지 반복)
            stock.py      → 목표 순위 주변 실판매 벤치마크
   ↓
listing 스킬: 폼 20개 항목 완성본 출력  (미검증 표기 없이 확정값으로)
```

probe로 값을 확보했으면 listing 출력의 `※ 미검증 항목`은 비워지고, 카테고리와 상품명은 **확정값**으로 표기한다. 반대로 probe가 실패했으면 임의로 확정 표기하지 않는다.

## 의존성

```bash
pip install curl_cffi     # 권장 (TLS 위장). 없으면 requests로 폴백
```

`requests`만 있어도 동작은 시도하지만 차단 확률이 올라간다.

## 주의

여기서 뽑는 값과 그 해석 기준(1.0 만점, 인덱스 짝맞춤, 25~30자 등)은 네이버 공식 문서가 아니라 역추적·경험칙이다. 값이 이상하면 추정으로 단정하지 말고 원본 JSON을 확인한다.
