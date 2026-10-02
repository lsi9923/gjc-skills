#!/usr/bin/env python3
"""쿠팡 노출상품명 + 검색어(최대 20개) 생성 보강기 (표준 라이브러리만).

skill_audit 권고 반영:
- 구버전 coupang_title_composer / coupang_tags_generator 의 '하드코딩 태그풀·카테고리 프리셋·
  F자패턴 전면배치'는 이식 금지(근거 없는 채우기).
- 살릴 개념만 이식: (1) 옵션값(색상·수량) 제거, (2) 색상 쿠팡 표준명 정규화,
  (3) 근거 있는 키워드로만 검색어 슬롯 채우기(못 채우면 20개 미만 허용).

입력 = 근거 있는 키워드 소스들. 아무 근거 없이 슬롯을 지어내지 않는다.
  --name "정제된 제품명"             (필수, prepare_product.cleanedName 사용 권장)
  --keywords "a,b,c"                네이버 F12 판정 통과 키워드(완성형/조합형/연결형/교집합) + 태그 후보
  --keyword-json <naver_title_builder 출력.json>  judgeTable/tagCandidates 에서 근거 키워드 흡수
  --sources-json <sources.json>    검색어 소스별 근거를 우선순위로 넘김(신규, 하위호환):
      { "wingRecommended": ["..."], "wingPopular": ["..."],
        "coupangAutocomplete": ["..."], "naverF12": ["..."] }
    우선순위: 윙 추천 검색어 > 윙 인기검색어 도구 > 쿠팡 자동완성 > 네이버 F12 근거.
    출력 각 검색어에 source 표시. 같은 단어가 여러 소스에 있으면 더 높은 소스로 귀속.
  --plan <registration_plan.json>  brand.removedFromMarketing 흡수
  --brand-removed "더이안"
출력 = { exposureName, exposureIssues[], searchTerms[{term,source,inName}], excluded[], notes[] } (JSON)

사용
  python coupang_helper.py --name "무선청소기 YQ-669" --keyword-json builder_out.json --out cp.json
  python coupang_helper.py --name "..." --sources-json sources.json --out cp.json
  python coupang_helper.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

COUPANG_TAG_ALLOWED = re.compile(r"^[0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ\s!@#$%^&*\-+;:'.]+$")
PROMOTIONAL = {"최저가", "할인", "특가", "세일", "쿠폰", "무료배송", "당일발송", "이벤트", "한정수량",
               "품절임박", "1+1", "2+1", "사은품", "정품", "추천", "인기", "신형", "고급", "베스트", "필수템"}
# 노출상품명 금지어(홍보/과장). 근거 없는 수식어는 노출상품명에 넣지 않는다.
EXPOSURE_BANNED = PROMOTIONAL | {"강추", "대박", "핫딜", "역대급", "최고", "국내최저"}
# 검색어 소스 우선순위(높을수록 우선). 같은 단어가 여러 소스에 있으면 더 높은 소스로 귀속.
SOURCE_PRIORITY = [
    ("wingRecommended", "윙 추천 검색어"),
    ("wingPopular", "윙 인기검색어 도구"),
    ("coupangAutocomplete", "쿠팡 자동완성"),
    ("naverF12", "네이버 F12 근거"),
    ("keywords", "직접 입력(--keywords)"),
    ("keywordJson", "title_builder 근거"),
]
SOURCE_LABEL = dict(SOURCE_PRIORITY)
OPTION_VALUE = re.compile(
    r"(^\d+\s*(개|매|장|팩|세트|입|병|캔|포|묶음|박스|p|pcs?)$"
    r"|화이트|블랙|그레이|그레이지|아이보리|베이지|네이비|카키|브라운|레드|블루|그린|핑크|퍼플|옐로우"
    r"|웜그레이|민트|라벤더|버건디|와인|카멜|크림|실버|골드|로즈골드"
    r"|흰색|검정|검은색|회색|남색|빨강|파랑|초록|분홍|보라|노랑|주황|갈색|하늘색"
    r"|색상\s*(랜덤|선택)?|랜덤|택1|옵션\s*\d*|사이즈\s*(선택)?|[SML]사이즈)",
    re.IGNORECASE,
)


def nfc(s):
    return unicodedata.normalize("NFC", str(s or "")).strip()


def nlen(s):
    return len(nfc(s))


def clean_exposure_name(name, brand_removed):
    """쿠팡 노출상품명: 옵션값(색상·수량) 제거 + 브랜드 제거 + 공백 정리. 100자 이내."""
    name = nfc(name)
    if "," in name:
        segs = [s.strip() for s in name.split(",")]
        name = " ".join([segs[0]] + [s for s in segs[1:] if s and not OPTION_VALUE.search(s)])
    for b in brand_removed:
        if b:
            name = re.sub(rf"(^|\s){re.escape(b)}(\s|$)", " ", name, flags=re.IGNORECASE)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def check_exposure_name(name):
    """노출상품명 길이(100자)·금지어(홍보/과장) 검사. 문제 목록 반환.

    name 은 아직 자르지 않은 정제 결과여야 100자 초과를 잡을 수 있다.
    """
    issues = []
    n = nfc(name)
    if nlen(n) > 100:
        issues.append({"level": "block", "reason": f"노출상품명 {nlen(n)}자 - 100자 초과(잘림)"})
    if not n:
        issues.append({"level": "block", "reason": "노출상품명이 비어 있음"})
    hit = sorted({b for b in EXPOSURE_BANNED if b in n})
    if hit:
        issues.append({"level": "warn", "reason": f"홍보/과장 금지어 포함: {hit}"})
    return issues


def build_search_terms(sourced, name, brand_removed, limit=20):
    """근거 있는 키워드로 검색어 슬롯 채우기(소스 우선순위·출처 표시).

    sourced = [(keyword, source_key), ...]  이미 우선순위 순으로 정렬돼 들어온다.
    근거 없으면 20개 미만 허용(지어내지 않음). 같은 단어는 먼저(높은 소스) 것만.
    """
    brand_removed_l = [b.lower() for b in brand_removed if b]
    name_c = re.sub(r"\s+", "", nfc(name)).lower()
    name_tokens = {t for t in re.split(r"\s+", nfc(name)) if t}
    terms, excluded, seen = [], [], set()
    for kw, src in sourced:
        kw = nfc(kw)
        if not kw:
            continue
        c = re.sub(r"\s+", "", kw).lower()
        if c in seen:
            continue
        if kw in PROMOTIONAL or any(p in kw for p in PROMOTIONAL):
            excluded.append({"word": kw, "source": SOURCE_LABEL.get(src, src),
                             "reason": "홍보성 단어(쿠팡 검색어 금지)"})
            continue
        if any(b in kw.lower() for b in brand_removed_l):
            excluded.append({"word": kw, "source": SOURCE_LABEL.get(src, src),
                             "reason": "제거 대상 브랜드/판매자명"})
            continue
        if nlen(kw) > 20:
            excluded.append({"word": kw, "source": SOURCE_LABEL.get(src, src),
                             "reason": "검색어 20자 초과"})
            continue
        if not COUPANG_TAG_ALLOWED.match(kw):
            excluded.append({"word": kw, "source": SOURCE_LABEL.get(src, src),
                             "reason": "쿠팡 허용 특수문자(!@#$%^&*-+;:'.) 외 문자 포함"})
            continue
        seen.add(c)
        # 상품명에 통째로 포함된 검색어는 중복노출 성격 → inName 표시(제외는 안 함)
        in_name = c in name_c or kw in name_tokens
        terms.append({"term": kw, "source": SOURCE_LABEL.get(src, src), "inName": in_name})
        if len(terms) >= limit:
            break
    return terms, excluded


def absorb_keyword_json(path):
    """naver_title_builder 출력에서 근거 키워드(judgeTable 유효 판정 + tagCandidates)를 순서대로."""
    out = []
    try:
        d = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return out
    valid = {"완성형", "연결형", "조합형", "교집합"}
    for j in d.get("judgeTable", []):
        if j.get("type") in valid:
            out.append(nfc(j.get("keyword")))
    for t in d.get("tagCandidates", []):
        out.append(nfc(t.get("tag")))
    return [x for x in out if x]


def merge_sources(source_lists):
    """소스별 키워드 dict → 우선순위 순 [(keyword, source_key)]. 낮은 소스의 중복은 버림."""
    ordered = []
    claimed = set()
    for src_key, _label in SOURCE_PRIORITY:
        for kw in source_lists.get(src_key) or []:
            kw = nfc(kw)
            if not kw:
                continue
            c = re.sub(r"\s+", "", kw).lower()
            if c in claimed:
                continue
            claimed.add(c)
            ordered.append((kw, src_key))
    return ordered


def run(name, sourced, brand_removed):
    exposure_full = clean_exposure_name(name, brand_removed)
    exposure_issues = check_exposure_name(exposure_full)
    exposure = exposure_full[:100]  # 화면 입력용은 100자로 자름(이슈는 위에서 이미 기록)
    terms, excluded = build_search_terms(sourced, exposure, brand_removed)
    notes = [
        "검색어는 근거 있는 키워드로만 채운다. 20개를 못 채우면 미만으로 둔다(지어내기 금지).",
        "소스 우선순위: 윙 추천 > 윙 인기검색어 > 쿠팡 자동완성 > 네이버 F12. 각 검색어에 출처 표시.",
        "F자패턴·하드코딩 태그풀은 이식하지 않음(skill_audit 권고). 색상은 쿠팡 표준명 사용.",
        "노출상품명은 옵션값(색상·수량) 제외. 브랜드칸은 '브랜드 없음' 처리(상품명은 제품명 중심).",
    ]
    if len(terms) < 20:
        notes.append(f"검색어 {len(terms)}/20 - 근거 있는 후보가 더 있으면 F12/자동완성/Wing 인기검색어로 보강.")
    # 소스별 채택 수 요약
    by_source = {}
    for t in terms:
        by_source[t["source"]] = by_source.get(t["source"], 0) + 1
    return {"exposureName": exposure, "exposureLength": nlen(exposure),
            "exposureIssues": exposure_issues,
            "searchTerms": terms, "searchTermCount": len(terms),
            "searchTermsBySource": by_source,
            "excluded": excluded, "notes": notes}


def selftest():
    # 하위호환: --keywords 만 준 경우도 동작
    sourced = merge_sources({"keywords": ["무선청소기", "핸디청소기", "차량용청소기",
                                          "최저가", "더이안청소기", "무선청소기"]})
    r = run("2in1 에어슬림 무선청소기 YQ-669, 화이트, 1개", sourced, ["더이안"])
    assert r["exposureName"] == "2in1 에어슬림 무선청소기 YQ-669", r["exposureName"]
    tset = {t["term"] for t in r["searchTerms"]}
    assert "무선청소기" in tset and "핸디청소기" in tset, tset
    assert "최저가" not in tset, r  # 홍보성 제외
    assert not any("더이안" in t for t in tset), r  # 브랜드 제외
    assert r["searchTermCount"] == 3, r  # 중복/홍보/브랜드 제거 후 3개
    ex = {e["word"] for e in r["excluded"]}
    assert "최저가" in ex, r["excluded"]

    # 소스 우선순위: 같은 단어면 높은 소스로 귀속, 출처 표시
    s2 = merge_sources({"wingRecommended": ["신발정리대"],
                        "coupangAutocomplete": ["신발정리대", "현관정리대"],
                        "naverF12": ["신발장정리대"]})
    r2 = run("신발정리대 3단", s2, [])
    by = {t["term"]: t["source"] for t in r2["searchTerms"]}
    assert by["신발정리대"] == "윙 추천 검색어", by
    assert by["현관정리대"] == "쿠팡 자동완성", by
    assert by["신발장정리대"] == "네이버 F12 근거", by

    print(json.dumps({"selftest": "PASS", "exposureName": r["exposureName"],
                      "terms": [t["term"] for t in r["searchTerms"]],
                      "sourceCheck": by}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", default="")
    ap.add_argument("--keywords", default="")
    ap.add_argument("--keyword-json")
    ap.add_argument("--sources-json")
    ap.add_argument("--plan")
    ap.add_argument("--brand-removed", default="")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0

    name = a.name
    brand_removed = [b.strip() for b in a.brand_removed.split(",") if b.strip()]

    # 소스별 키워드 수집(우선순위 순으로 merge_sources 가 정렬)
    source_lists = {}
    if a.sources_json and Path(a.sources_json).exists():
        try:
            sj = json.loads(Path(a.sources_json).read_text(encoding="utf-8"))
            for k in ("wingRecommended", "wingPopular", "coupangAutocomplete", "naverF12"):
                if sj.get(k):
                    source_lists[k] = [nfc(x) for x in sj[k] if nfc(x)]
        except Exception:
            pass
    kw = [k.strip() for k in a.keywords.split(",") if k.strip()]
    if kw:
        source_lists.setdefault("keywords", []).extend(kw)
    if a.keyword_json and Path(a.keyword_json).exists():
        kj = absorb_keyword_json(a.keyword_json)
        if kj:
            source_lists.setdefault("keywordJson", []).extend(kj)

    if a.plan and Path(a.plan).exists():
        try:
            plan = json.loads(Path(a.plan).read_text(encoding="utf-8"))
            br = (plan.get("brand") or {}).get("removedFromMarketing") or []
            brand_removed = list(dict.fromkeys(brand_removed + [nfc(b) for b in br if b]))
            if not name:
                name = plan.get("cleanedName") or (plan.get("coupang") or {}).get("productName") or ""
        except Exception:
            pass
    if not name:
        ap.error("--name 또는 --plan(cleanedName) 이 필요합니다")

    sourced = merge_sources(source_lists)
    res = run(name, sourced, brand_removed)
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
