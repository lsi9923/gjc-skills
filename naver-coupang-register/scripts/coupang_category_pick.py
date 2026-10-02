#!/usr/bin/env python3
"""쿠팡 Wing 말단 카테고리 후보 정렬 + 필수/필터 속성 채움 판정 (표준 라이브러리만).

절대 원칙(skill_audit / 강의규칙 반영):
- 카테고리 경로를 추측으로 만들지 않는다. 에이전트가 Wing 화면에서 읽어 넘긴
  후보(candidates)만 점수·근거와 함께 정렬한다. 후보가 없으면 빈 목록을 돌려준다.
- 하드코딩 CATEGORY_PRESETS / 기본값 카테고리(구버전 58974 자전거장갑 폴백)는 이식 금지.
- 속성값은 상품 근거로만 채운다. 색상은 쿠팡 표준명으로 정규화(사실 매핑),
  수량·개당 용량/중량 등 숫자 속성에는 숫자만(단위 포함) 넣고 '상세페이지 참조' 같은
  문장은 절대 넣지 않는다. 품절/판매종료 옵션은 근거에서 제외한다.

입력(JSON, 에이전트가 화면·plan에서 모아 넘김):
  --product-json <fact.json>   상품 사실:
      { "productName": "...", "naverCategoryPath": "가구/인테리어>...>수납장",
        "keywords": ["신발정리대","현관정리대"],
        "options": [ {"name":"화이트","soldOut":false}, {"name":"블랙","soldOut":true} ],
        "attributesEvidence": { "색상":"흰색", "수량":"3개", "개당용량":"500ml" } }
  --candidates-json <cand.json>  Wing 카테고리 검색 결과(화면에서 읽음):
      { "candidates": [
          { "path":"홈인테리어>수납/정리>신발정리대", "code":"12345", "leaf":"신발정리대",
            "topSeller": true },
          ... ] }
  --attributes-json <attr.json>  Wing 필수 구매옵션/검색필터 속성 스펙(화면에서 읽음):
      { "required": [ {"name":"수량","type":"number","unit":"개"},
                      {"name":"색상","type":"enum","values":["화이트","블랙","그레이"]} ],
        "filters":  [ {"name":"주요기능","type":"enum","values":["방수","미끄럼방지"]} ] }

출력(JSON): { "categoryCandidates":[...점수·근거...], "attributes":{filled:[],empty:[]}, "notes":[] }

사용:
  python coupang_category_pick.py --product-json p.json --candidates-json c.json --attributes-json a.json --out out.json
  python coupang_category_pick.py --selftest
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

# 쿠팡 표준 색상 매핑(사실). 구버전 COUPANG_COLOR_STANDARDS 개념만 이식.
COUPANG_COLOR_STANDARDS = {
    "흰색": "화이트", "하얀색": "화이트", "하양": "화이트",
    "검정": "블랙", "검정색": "블랙", "까만색": "블랙", "까망": "블랙",
    "회색": "그레이", "쥐색": "그레이",
    "먹색": "차콜",
    "빨강": "레드", "빨간색": "레드",
    "파랑": "블루", "파란색": "블루",
    "남색": "네이비",
    "노랑": "옐로우", "노란색": "옐로우",
    "초록": "그린", "녹색": "그린",
    "분홍": "핑크", "분홍색": "핑크",
    "갈색": "브라운", "밤색": "브라운",
    "보라": "퍼플", "보라색": "퍼플",
    "주황": "오렌지", "주황색": "오렌지",
    "하늘색": "스카이블루",
}
# 숫자 속성에 넣으면 안 되는 문장/플레이스홀더
PLACEHOLDER = re.compile(r"상세\s*페이지\s*참조|상세참조|해당없음|없음|참조|기타|미상|N/?A", re.IGNORECASE)
NUMERIC_TYPES = {"number", "numeric", "int", "float", "숫자", "수량"}
COLOR_HINT = re.compile(r"색상|색깔|컬러|color")


def nfc(s):
    return unicodedata.normalize("NFC", str(s or "")).strip()


def norm_key(s):
    return re.sub(r"\s+", "", nfc(s)).lower()


def normalize_color(raw):
    """쿠팡 표준 색상명으로 정규화. 매핑에 없으면 원본(정리)만 반환."""
    clean = nfc(raw)
    for k, v in COUPANG_COLOR_STANDARDS.items():
        if k in clean:
            clean = clean.replace(k, v)
    return clean


def extract_number(raw):
    """'3개'/'500ml'/'1.5L' 처럼 숫자(+단위)만 추출. 순수 문장이면 None."""
    s = nfc(raw)
    m = re.search(r"(\d+(?:[.,]\d+)?)\s*([a-zA-Z가-힣]{0,4})", s)
    if not m:
        return None
    num = m.group(1).replace(",", "")
    unit = m.group(2).strip()
    return (num + unit) if unit else num


# ---------------- (1) 카테고리 후보 점수 ----------------

def _tokens(text):
    return [t for t in re.split(r"[\s>/,·|]+", norm_key(text)) if t]


def score_category(cand, product):
    """후보 1건을 상품 사실과 대조해 점수+근거 산출. 추측 경로 생성 없음."""
    reasons = []
    score = 0.0
    leaf = nfc(cand.get("leaf") or (cand.get("path", "").split(">")[-1] if cand.get("path") else ""))
    path = nfc(cand.get("path"))
    name_tokens = set(_tokens(product.get("productName")))
    kw_tokens = set()
    for k in product.get("keywords") or []:
        kw_tokens |= set(_tokens(k))
    nv_tokens = set(_tokens(product.get("naverCategoryPath")))
    leaf_key = norm_key(leaf)

    # 말단명이 품명/키워드에 직접 등장 → 강한 근거
    if leaf_key and leaf_key in norm_key(product.get("productName")):
        score += 3.0
        reasons.append(f"말단 '{leaf}' 가 품명에 직접 포함")
    lt = set(_tokens(leaf))
    inter_kw = lt & kw_tokens
    if inter_kw:
        score += 1.5 * len(inter_kw)
        reasons.append(f"말단 토큰이 키워드와 일치: {sorted(inter_kw)}")
    inter_name = lt & name_tokens
    if inter_name and not inter_kw:
        score += 1.0 * len(inter_name)
        reasons.append(f"말단 토큰이 품명과 일치: {sorted(inter_name)}")
    # 네이버 카테고리 경로와 상위 경로 겹침(참고 근거, 약)
    path_tokens = set(_tokens(path))
    inter_nv = path_tokens & nv_tokens
    if inter_nv:
        score += 0.5 * len(inter_nv)
        reasons.append(f"경로가 네이버 카테고리와 겹침: {sorted(inter_nv)}")
    # 상위 판매자 경로(화면 근거)면 가점
    if cand.get("topSeller"):
        score += 1.0
        reasons.append("상위 판매자 카테고리 경로(화면 대조)")
    if not reasons:
        reasons.append("상품 근거와 겹치는 신호 없음 - 화면에서 재확인 필요")
    return {
        "path": path, "code": cand.get("code"), "leaf": leaf,
        "score": round(score, 2), "reasons": reasons,
        "topSeller": bool(cand.get("topSeller")),
    }


def rank_categories(product, candidates):
    scored = [score_category(c, product) for c in candidates if (c.get("path") or c.get("leaf"))]
    scored.sort(key=lambda x: (-x["score"], x["path"]))
    return scored


# ---------------- (2) 속성 채움 판정 ----------------

def live_option_values(product):
    """품절/판매종료 아닌 옵션명만 근거로."""
    vals, dropped = [], []
    for o in product.get("options") or []:
        if isinstance(o, str):
            vals.append(nfc(o))
            continue
        name = nfc(o.get("name"))
        if not name:
            continue
        if o.get("soldOut") or o.get("soldout") or o.get("판매종료") or o.get("품절"):
            dropped.append(name)
        else:
            vals.append(name)
    return vals, dropped


def resolve_attribute(spec, evidence, opt_values):
    """속성 1건을 근거로 채울 값/비울지 판정."""
    name = nfc(spec.get("name"))
    typ = norm_key(spec.get("type"))
    key = norm_key(name)
    is_numeric = typ in NUMERIC_TYPES or (spec.get("unit") not in (None, ""))
    is_color = bool(COLOR_HINT.search(name))

    # 근거 소스: evidence[name] 우선, 색상이면 옵션값도 근거
    raw = None
    for ek, ev in (evidence or {}).items():
        if norm_key(ek) == key:
            raw = ev
            break
    if raw is None and is_color and opt_values:
        # 색상형이면 옵션값 중 색상 표준으로 잡히는 것들
        colors = [normalize_color(v) for v in opt_values]
        colors = [c for c in colors if any(std in c for std in COUPANG_COLOR_STANDARDS.values())]
        if colors:
            raw = ", ".join(dict.fromkeys(colors))

    if raw is None or nfc(raw) == "":
        return {"name": name, "status": "empty", "reason": "상품 근거 없음 - 비움(추측 금지)"}

    raw = nfc(raw)
    if is_numeric:
        if PLACEHOLDER.search(raw) and not re.search(r"\d", raw):
            return {"name": name, "status": "empty",
                    "reason": "숫자 속성에 문장/플레이스홀더는 금지 - 비움"}
        num = extract_number(raw)
        if num is None:
            return {"name": name, "status": "empty",
                    "reason": f"숫자 추출 불가('{raw}') - 비움"}
        return {"name": name, "value": num, "status": "filled",
                "source": "evidence", "reason": "숫자만 채움"}

    if is_color:
        val = normalize_color(raw)
        return {"name": name, "value": val, "status": "filled",
                "source": "color-standard", "reason": "쿠팡 표준 색상명으로 정규화"}

    # enum 이면 화면 허용값과 대조
    values = [nfc(v) for v in (spec.get("values") or [])]
    if values:
        rk = norm_key(raw)
        hit = next((v for v in values if norm_key(v) == rk), None)
        if hit is None:
            hit = next((v for v in values if rk and (rk in norm_key(v) or norm_key(v) in rk)), None)
        if hit:
            return {"name": name, "value": hit, "status": "filled",
                    "source": "enum-match", "reason": "화면 허용값과 일치"}
        return {"name": name, "status": "empty",
                "reason": f"허용값 목록에 근거값('{raw}') 없음 - 비움(임의값 금지)"}
    if PLACEHOLDER.search(raw):
        return {"name": name, "status": "empty", "reason": "플레이스홀더 문구 - 비움"}
    return {"name": name, "value": raw, "status": "filled",
            "source": "evidence", "reason": "텍스트 속성 근거값 채움"}


def resolve_attributes(product, attr_spec):
    evidence = product.get("attributesEvidence") or {}
    opt_values, dropped = live_option_values(product)
    filled, empty = [], []
    for group in ("required", "filters"):
        for spec in attr_spec.get(group) or []:
            r = resolve_attribute(spec, evidence, opt_values)
            r["group"] = group
            (filled if r["status"] == "filled" else empty).append(r)
    return filled, empty, opt_values, dropped


# ---------------- run ----------------

def run(product, candidates, attr_spec):
    cats = rank_categories(product, candidates)
    filled, empty, opt_values, dropped = resolve_attributes(product, attr_spec)
    notes = [
        "카테고리 경로는 화면에서 읽은 후보만 점수화한다(추측 생성 금지).",
        "속성은 상품 근거로만 채운다. 색상=쿠팡 표준명, 수량·용량=숫자만, 문장은 숫자 속성에 넣지 않음.",
    ]
    if dropped:
        notes.append(f"품절/판매종료 옵션 {len(dropped)}개 제외: {dropped}")
    if cats and cats[0]["score"] <= 0:
        notes.append("최상위 후보도 상품 근거와 겹침이 약함 - 카테고리 화면 재확인 권장.")
    if not candidates:
        notes.append("카테고리 후보가 입력되지 않음 - Wing 카테고리 검색 결과를 화면에서 읽어 넘겨야 함.")
    return {
        "categoryCandidates": cats,
        "attributes": {"filled": filled, "empty": empty},
        "liveOptionValues": opt_values,
        "droppedOptions": dropped,
        "notes": notes,
    }


def _load(path):
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def selftest():
    product = {
        "productName": "2in1 에어슬림 신발정리대 3단",
        "naverCategoryPath": "가구/인테리어>수납/정리>신발정리대",
        "keywords": ["신발정리대", "현관정리대", "신발장정리대"],
        "options": [{"name": "화이트", "soldOut": False},
                    {"name": "블랙", "soldOut": True}],
        "attributesEvidence": {"색상": "흰색", "수량": "3개",
                               "개당용량": "상세페이지 참조", "주요기능": "미끄럼방지"},
    }
    candidates = {"candidates": [
        {"path": "홈인테리어>수납/정리>신발정리대", "code": "111", "leaf": "신발정리대", "topSeller": True},
        {"path": "생활용품>청소용품>청소솔", "code": "222", "leaf": "청소솔"},
    ]}
    attrs = {"required": [{"name": "수량", "type": "number", "unit": "개"},
                          {"name": "색상", "type": "enum", "values": ["화이트", "블랙", "그레이"]}],
             "filters": [{"name": "개당용량", "type": "number", "unit": "ml"},
                         {"name": "주요기능", "type": "enum", "values": ["미끄럼방지", "방수"]}]}
    r = run(product, candidates["candidates"], attrs)
    # 카테고리: 신발정리대가 1위
    assert r["categoryCandidates"][0]["leaf"] == "신발정리대", r["categoryCandidates"]
    assert r["categoryCandidates"][0]["score"] > r["categoryCandidates"][1]["score"], r
    # 속성 채움
    f = {x["name"]: x for x in r["attributes"]["filled"]}
    e = {x["name"]: x for x in r["attributes"]["empty"]}
    assert f["수량"]["value"] == "3개", f  # 숫자+단위
    assert f["색상"]["value"] == "화이트", f  # 흰색->화이트, enum 일치
    assert "개당용량" in e, e  # 문장->숫자속성 비움
    assert f["주요기능"]["value"] == "미끄럼방지", f
    # 품절 블랙 제외
    assert r["droppedOptions"] == ["블랙"], r["droppedOptions"]
    print(json.dumps({"selftest": "PASS",
                      "top": r["categoryCandidates"][0]["leaf"],
                      "filled": sorted(f.keys()),
                      "empty": sorted(e.keys())}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-json")
    ap.add_argument("--candidates-json")
    ap.add_argument("--attributes-json")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0

    product = _load(a.product_json)
    cand_doc = _load(a.candidates_json)
    candidates = cand_doc.get("candidates") if isinstance(cand_doc, dict) else (cand_doc or [])
    attr_spec = _load(a.attributes_json)
    if not product:
        ap.error("--product-json 이 필요합니다(상품 사실)")

    res = run(product, candidates or [], attr_spec or {})
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
