#!/usr/bin/env python3
"""이호 네이버 SEO 규칙으로 키워드 5분류 판정 + 상품명 조립 + 태그 후보 생성.

표준 라이브러리만 사용. 인터넷·브라우저 접근 없음. F12 근거(JSON)만 입력으로 받는다.

규칙 근거: references/seo-rules.md (이호 강의 §3~§5 정리)
- §3 terms 5분류(완성형/조합형/미적용/동의어/연결형)  [2-3B]
- §4 상품명 100점 조립(완성형 좌측, 조합형 왼→오·거리 최소, 25~30자 권장, 동일단어 최소) [2-4]
- §5 검증(terms + intersectionTerms)  [2-5]
정책대조: 35자/25~30자는 강의 경험칙 → WARN(권장창)으로만. 공식 상한 100자는 별도.

입력 (둘 중 하나)
  1) --f12-dir <디렉터리>  : 그 안의 *.json 을 모두 F12 결과로 읽는다.
  2) --f12 <a.json> --f12 <b.json> ...  : 개별 지정.
각 F12 JSON 은 naver_f12_capture.js 가 내보낸 구조를 기대한다:
  { "target": {"keyword": "...", ...} 또는 문자열,
    "terms": [...], "intersectionTerms": [...],
    "categoryPackets"/"categoryLevels": [...],
    "blockedOrCaptcha": bool, "schemaNote": "..." }
  target 이 없으면 파일명(확장자 제거)을 키워드로 본다.

상품 사실 (선택)
  --facts <plan.json 또는 facts.json>   : registration_plan.json 을 주면 brand.removedFromMarketing,
      cleanedName, keywordSeeds 를 읽어 제외단어·후보 우선순위에 반영.
  --brand-removed "더이안,베스트라이너"   : 상품명/태그에서 뺄 단어.
  --search-volume <vol.json>            : {"키워드": 월검색수}. 있으면 완성형 정렬·태그 우선순위 보조(F12 근거 우선).

출력 (JSON, stdout + --out 파일)
  { judgeTable:[...], titleCandidates:[...], tagCandidates:[...], excluded:[...],
    verification:{...}, notes:[...] }
사용
  python naver_title_builder.py --f12-dir <workDir>\f12 --facts <workDir>\registration_plan.json --out <workDir>\title_build.json
  python naver_title_builder.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

# Windows PowerShell cp949 콘솔에서 한글/em-dash 출력 크래시 방지 (audit A1/A2)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

TYPE_COMPLETE = "완성형"
TYPE_LINKED = "연결형"
TYPE_COMBO = "조합형"
TYPE_INTERSECTION = "교집합"
TYPE_NOT_APPLIED = "미적용"
TYPE_SYNONYM = "동의어"
TYPE_UNKNOWN = "판정불가"

PROMOTIONAL = {"최저가", "할인", "특가", "세일", "쿠폰", "무료배송", "당일발송", "이벤트", "한정수량",
               "품절임박", "1+1", "2+1", "사은품", "정품", "추천", "인기", "신형", "고급", "베스트", "필수템"}


def nfc(s):
    return unicodedata.normalize("NFC", str(s or "")).strip()


def compact(s):
    return re.sub(r"\s+", "", nfc(s)).lower()


def nlen(s):
    return len(nfc(s))


# ---------------------------------------------------------------- F12 파싱

def _words_from(seq):
    """terms/intersectionTerms 리스트를 단어 문자열 리스트로 정규화."""
    out = []
    if isinstance(seq, str):
        seq = re.split(r"[\s,|]+", seq)
    for x in seq or []:
        if isinstance(x, str):
            w = nfc(x)
            if w:
                out.append(w)
        elif isinstance(x, dict):
            w = nfc(x.get("word") or x.get("term") or x.get("keyword") or x.get("text")
                    or x.get("value") or x.get("name") or x.get("query"))
            if w:
                out.append(w)
    return out


def merge_same_keyword(results):
    """같은 키워드의 결과(F12 캡처 + 검색 추출 등)를 하나로 합친다.

    - terms 가 있는 결과를 기준으로 삼고, 없는 결과(검색 추출 JSON 등)는 카테고리만 보탠다.
    - 같은 키워드가 '판정불가' 로 한 번 더 판정표에 들어가는 중복을 막는다.
    - 모든 결과에 terms 가 없으면 하나만 남겨 판정불가로 둔다.
    """
    order, groups = [], {}
    for r in results:
        # 띄어쓰기까지 같은 키워드만 합친다. '생유산균'과 '생 유산균'은 연결형 판정에 쓰이므로 따로 둔다.
        key = " ".join(nfc(r.get("keyword") or "").split())
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)
    merged = []
    for key in order:
        items = groups[key]
        base = next((r for r in items if r.get("ok")), None) or next((r for r in items if r.get("terms") or r.get("intersection")), None) or items[0]
        base = dict(base)
        cats, seen = [], set()
        for r in [base] + [x for x in items if x is not base]:
            for c in r.get("categories") or []:
                sig = (c.get("level"), c.get("id"), c.get("name"))
                if sig not in seen:
                    seen.add(sig)
                    cats.append(c)
        base["categories"] = cats
        base["blocked"] = base.get("blocked") and not base.get("ok")
        merged.append(base)
    return merged


def load_f12(path: Path):
    """F12 결과 JSON 하나 → {keyword, terms[], intersection[], categories[], blocked, note}."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"keyword": path.stem, "terms": [], "intersection": [], "categories": [],
                "blocked": False, "note": f"JSON 파싱 실패: {e}", "ok": False}
    if not isinstance(data, dict):
        data = {}
    # 키워드
    tgt = data.get("target")
    if isinstance(tgt, dict):
        kw = nfc(tgt.get("keyword") or tgt.get("query") or "")
    elif isinstance(tgt, str):
        kw = nfc(tgt)
    else:
        kw = ""
    if not kw:
        kw = nfc(data.get("query") or data.get("keyword") or path.stem)

    terms = _words_from(data.get("terms"))
    inter = _words_from(data.get("intersectionTerms") or data.get("intersection"))
    # 폴백: termsPackets / intersectionPackets (naver_f12_capture.js 상세 구조)
    if not terms:
        for pk in data.get("termsPackets") or []:
            terms += _words_from(pk.get("words"))
    if not inter:
        for pk in data.get("intersectionPackets") or []:
            inter += _words_from(pk.get("words"))
    terms = list(dict.fromkeys(terms))
    inter = list(dict.fromkeys(inter))

    # 카테고리 relevance: categoryPackets(캡처기) 또는 categoryLevels(추출기)
    cats = []
    for pk in data.get("categoryPackets") or []:
        for c in pk.get("categories") or []:
            cats.append({"level": pk.get("level"), "name": nfc(c.get("name")),
                         "id": nfc(c.get("id")), "relevance": c.get("relevance")})
    for lv in data.get("categoryLevels") or []:
        for c in lv.get("categories") or []:
            cats.append({"level": lv.get("level"), "name": nfc(c.get("name")),
                         "id": nfc(c.get("id")), "relevance": c.get("relevance")})

    blocked = bool(data.get("blockedOrCaptcha"))
    note = data.get("schemaNote") or data.get("note") or ""
    ok = bool(terms) and not blocked
    return {"keyword": kw, "terms": terms, "intersection": inter, "categories": cats,
            "blocked": blocked, "note": note, "ok": ok, "totalCount": data.get("totalCount")}


# ---------------------------------------------------------------- 이호 5분류 판정

def classify(keyword, terms, intersection, *, spaced_result=None, synonym_pool=None):
    """단일 키워드를 이호 규칙으로 판정. 근거(reason)를 함께 반환.

    - 완성형(§3-2): terms 에 그대로 한 덩어리(단일 토큰) 로 존재.
    - 연결형(§3-6): 붙여 검색하면 한 덩어리지만 "띄어서" 재검색해도 여전히 한 덩어리(생유산균).
                     spaced_result(띄어 검색한 F12)의 terms 로 판별. 완성형과 동일 취급.
    - 조합형(§3-3): terms 에서 여러 단어로 쪼개져 나옴.
    - 미적용(§3-4): 일부 수식어가 terms 에서 사라짐(유산균추천→유산균).
    - 교집합(§5-2): terms 엔 없지만 intersectionTerms 로 이동.
    - 동의어(§3-5): synonym_pool 로 총상품수 근사 판정.
    """
    kw = nfc(keyword)
    ckw = compact(kw)
    tokens = kw.split()
    ct = [compact(t) for t in terms]
    ci = [compact(t) for t in intersection]
    reason = []

    if not terms and not intersection:
        return {"keyword": kw, "type": TYPE_UNKNOWN,
                "reason": "terms 패킷 없음(차단/스키마변경) — 추측 금지", "matchedTerms": [],
                "confidence": "none"}

    whole = ckw in ct
    in_inter = ckw in ci
    # 이 키워드를 구성하는 terms 조각들 (부분 일치)
    parts = [t for t in terms if compact(t) and compact(t) in ckw]
    parts_cover = sum(len(compact(t)) for t in parts)

    # 동의어 (수치 근사)
    if synonym_pool and kw in synonym_pool:
        peer, my_cnt, peer_cnt = synonym_pool[kw]
        if peer_cnt and my_cnt and abs(my_cnt - peer_cnt) / max(my_cnt, peer_cnt) < 0.001:
            return {"keyword": kw, "type": TYPE_SYNONYM,
                    "reason": f"'{peer}' 와 총상품수 거의 동일({my_cnt} vs {peer_cnt}) — 둘 중 하나만 사용",
                    "matchedTerms": [peer], "confidence": "high"}

    # 완성형 / 연결형
    if whole and len(tokens) == 1:
        # 띄어 검색 결과가 있으면 연결형 여부 확인
        if spaced_result is not None:
            spaced_terms = [compact(t) for t in spaced_result]
            if ckw in spaced_terms:
                return {"keyword": kw, "type": TYPE_LINKED,
                        "reason": "띄어서 재검색해도 한 덩어리로 인식(생유산균형). 사이에 단어 넣지 말고 붙여쓰기, 완성형처럼 취급",
                        "matchedTerms": [kw], "confidence": "high"}
            return {"keyword": kw, "type": TYPE_COMPLETE,
                    "reason": "terms 에 통째로 존재. 띄어 검색 시 분해됨(생들기름형) → 완성형",
                    "matchedTerms": [kw], "confidence": "high"}
        return {"keyword": kw, "type": TYPE_COMPLETE,
                "reason": "terms 에 검색어가 그대로 한 덩어리로 존재",
                "matchedTerms": [kw], "confidence": "high"}

    # 조합형: terms 에 여러 조각으로 쪼개져 나옴 (조각 합이 검색어 대부분을 덮음)
    if len(parts) >= 2 and parts_cover >= len(ckw) * 0.8:
        # 순서 근거 (terms 등장 순서)
        order = [p for p in terms if compact(p) in ckw]
        return {"keyword": kw, "type": TYPE_COMBO,
                "reason": f"terms 에서 {' / '.join(order)} 로 쪼개져 인식 → 조합형(왼→오·거리 최소 배치)",
                "matchedTerms": order, "confidence": "high"}

    # 교집합
    if in_inter:
        return {"keyword": kw, "type": TYPE_INTERSECTION,
                "reason": "terms 에 없고 intersectionTerms 로 이동 — 적합도는 반영됨(공통 필터)",
                "matchedTerms": [kw], "confidence": "medium"}

    # 미적용: 여러 토큰인데 일부만 term 으로 남음(수식어 소멸)
    if len(tokens) >= 2:
        survived = [t for t in tokens if compact(t) in ct]
        dropped = [t for t in tokens if compact(t) not in ct and compact(t) not in ci]
        if survived and dropped:
            return {"keyword": kw, "type": TYPE_NOT_APPLIED,
                    "reason": f"수식어 {'/'.join(dropped)} 가 terms 에서 사라짐 → 상품명에서 제거(살아남음: {'/'.join(survived)})",
                    "matchedTerms": survived, "confidence": "high"}

    # 단일 토큰(붙은 검색어)인데 term 조각이 검색어 일부만 덮음 → 수식어 소멸 = 미적용
    # (예: 유산균추천 → terms[유산균], '추천' 소멸 → 미적용. §3-4)
    if parts and parts_cover < len(ckw) * 0.8:
        dropped = ckw
        for p in sorted(parts, key=lambda x: -len(compact(x))):
            dropped = dropped.replace(compact(p), "", 1)
        return {"keyword": kw, "type": TYPE_NOT_APPLIED,
                "reason": f"수식어(약 '{dropped}')가 terms 에서 사라짐 → 상품명에서 제거(살아남음: {'/'.join(parts)})",
                "matchedTerms": parts, "confidence": "medium"}
    if parts:
        return {"keyword": kw, "type": TYPE_COMBO,
                "reason": f"terms 조각 {' / '.join(parts)} 로 부분 인식",
                "matchedTerms": parts, "confidence": "medium"}
    return {"keyword": kw, "type": TYPE_NOT_APPLIED,
            "reason": "terms 에 대응 조각이 없음 → 상품명 앞자리에 쓰지 않음",
            "matchedTerms": [], "confidence": "medium"}


# ---------------------------------------------------------------- 상품명 조립

def _order_key(word, volume):
    return (-int(volume.get(word, 0)), len(compact(word)))


def build_title(judgements, volume=None, brand_removed=None, max_hard=100, warn_lo=25, warn_hi=30):
    """이호 §4 규칙으로 상품명 후보 조립.

    전략:
    - 완성형/연결형: 검색수 높은 순(없으면 등장 순)으로 앞쪽(왼쪽 가점). 연결형은 붙여쓰기 보존.
    - 조합형: matchedTerms 를 왼→오로, 서로 인접하게 배치(거리 최소). 힘 줄 조합형을 먼저.
    - 미적용/판정불가/제외단어: 제외.
    - 동일 단어(term) 중복은 조합형 왼→오 성립에 꼭 필요할 때만 1회 허용(§4-3).
    """
    volume = volume or {}
    brand_removed = set(compact(b) for b in (brand_removed or []) if b)

    completes, linkeds, combos = [], [], []
    for j in judgements:
        if compact(j["keyword"]) in brand_removed:
            continue
        t = j["type"]
        if t == TYPE_COMPLETE:
            completes.append(j["keyword"])
        elif t == TYPE_LINKED:
            linkeds.append(j["keyword"])
        elif t == TYPE_COMBO:
            combos.append(j)

    completes = list(dict.fromkeys(completes))
    linkeds = list(dict.fromkeys(linkeds))
    completes.sort(key=lambda w: _order_key(w, volume))

    # 상품명에 절대 넣지 않을 조각(브랜드 제거대상 · 홍보어).
    # 조합형 matchedTerms 로 브랜드/홍보어가 새어들어가는 것을 push() 단일 관문에서 차단(절대 규칙·§8.1).
    promo_compact = set(compact(p) for p in PROMOTIONAL)

    def _is_forbidden_segment(tok):
        ct = compact(tok)
        if not ct:
            return True
        if ct in brand_removed:
            return True
        if ct in promo_compact:
            return True
        return False

    def assemble(order_strategy):
        used_tokens = []  # 순서 보존
        parts = []
        token_count = {}

        def push(tok):
            tok = nfc(tok)
            if not tok:
                return
            if _is_forbidden_segment(tok):  # 브랜드/홍보어는 상품명 진입 금지
                return
            parts.append(tok)
            token_count[compact(tok)] = token_count.get(compact(tok), 0) + 1

        # 1) 완성형 (좌측)
        for w in completes:
            push(w)
        # 2) 조합형 (힘 순서 = order_strategy). matchedTerms 를 왼→오, 인접 배치.
        #    §4-2/§4-3: 공통 꼬리 term(예: 유산균)을 공유하는 조합형들은
        #    [접두어들...] + [공통꼬리 1회] 로 묶어 거리·중복을 최소화한다.
        #    힘을 줄(우선순위 높은) 조합형이 공통꼬리에 가장 가깝게(오른쪽 끝) 오도록 접두어를 역순 배치.
        combo_order = order_strategy(combos)  # 앞쪽 = 힘 강함
        two_part = [j for j in combo_order if len(j.get("matchedTerms") or []) == 2]
        other = [j for j in combo_order if len(j.get("matchedTerms") or []) != 2]

        # 공통 꼬리별로 그룹화
        from collections import OrderedDict
        groups = OrderedDict()
        for j in two_part:
            head, tail = j["matchedTerms"][0], j["matchedTerms"][1]
            groups.setdefault(compact(tail), {"tail": tail, "heads": []})["heads"].append(head)

        for ctail, g in groups.items():
            heads = g["heads"]  # 힘 강한 순
            # 힘 강한 조합형이 꼬리에 인접(오른쪽 끝)하도록 접두어를 역순으로 나열
            for h in reversed(heads):
                ch = compact(h)
                if parts and compact(parts[-1]) == ch:
                    continue
                push(h)
            # 공통 꼬리 1회 (이미 직전이 같은 토큰이면 생략)
            if not (parts and compact(parts[-1]) == ctail):
                push(g["tail"])

        # 3분 이상 조각 조합형은 원래 순서대로.
        # 단, 이미 상품명에 들어간 토큰(완성형 등)과 겹치는 조각은 다시 넣지 않는다
        # (원상품명 전체가 조합형으로 들어와 완성형 단어들을 통째로 중복시키는 것을 방지).
        for j in other:
            for i, seg in enumerate(j.get("matchedTerms") or [j["keyword"]]):
                cseg = compact(seg)
                if parts and compact(parts[-1]) == cseg:
                    continue
                if any(compact(p) == cseg for p in parts):
                    continue
                push(seg)
        # 4) 연결형 (뒤쪽, 붙여쓰기 보존, 검색수 낮은 편이라 후미)
        for w in sorted(linkeds, key=lambda w: _order_key(w, volume)):
            if compact(w) not in [compact(p) for p in parts]:
                push(w)
        return parts

    # 전략 A: 검색수 높은 조합형 먼저 (대형 키워드에 힘)
    def strat_big(combos):
        return sorted(combos, key=lambda j: _order_key(j["keyword"], volume))

    # 전략 B: 검색수 낮은(소형·틈새) 조합형 먼저 (인기도 자신 없을 때, §4-1)
    def strat_small(combos):
        return sorted(combos, key=lambda j: (int(volume.get(j["keyword"], 0)), -len(compact(j["keyword"]))))

    candidates = []
    seen_titles = set()
    for label, strat in (("대형키워드 우선", strat_big), ("틈새키워드 우선", strat_small)):
        parts = assemble(strat)
        title = " ".join(parts)
        title_c = compact(title)
        if not title or title_c in seen_titles:
            continue
        seen_titles.add(title_c)
        # 35자 초과 시 조합형 붙여쓰기로 절감(§4-4)
        compressed = None
        if nlen(title) > warn_hi + 5 and combos:
            merged = title
            for j in combos:
                terms_lr = j.get("matchedTerms") or []
                for a, b in zip(terms_lr, terms_lr[1:]):
                    merged = merged.replace(f"{a} {b}", f"{a}{b}")
            if compact(merged) == compact(title) and nlen(merged) < nlen(title):
                compressed = merged
        final = compressed or title
        # 공식 상한(100자) 초과 상품명은 후보로 내보내지 않는다(규칙 위반 출력 방지).
        # 이호 규칙상 최대 35자이므로 100자 초과 후보는 유효 추천이 아니다.
        if nlen(final) > max_hard:
            continue
        candidates.append({
            "strategy": label,
            "title": final,
            "length": nlen(final),
            "lengthNote": _len_note(nlen(final), warn_lo, warn_hi, max_hard),
            "words": _word_evidence(parts, judgements),
        })
    return candidates


def _len_note(n, lo, hi, hard):
    if n > hard:
        return f"BLOCK: 공식 상한 {hard}자 초과({n}자)"
    if n > 35:
        return f"WARN: 이호 최대 35자 초과({n}자) — 조합형 붙여쓰기로 줄이기 검토"
    if lo <= n <= hi:
        return f"OK: 이호 권장창 {lo}~{hi}자({n}자)"
    if n < lo:
        return f"INFO: 권장창 {lo}~{hi}자 미만({n}자) — 근거 없는 단어로 억지로 채우지 않음"
    return f"INFO: 권장창 {lo}~{hi}자 초과, 35자 이내({n}자)"


def _word_evidence(parts, judgements):
    jmap = {}
    for j in judgements:
        for seg in [j["keyword"]] + (j.get("matchedTerms") or []):
            jmap.setdefault(compact(seg), j)
    out = []
    for p in parts:
        j = jmap.get(compact(p))
        out.append({"word": p, "type": (j or {}).get("type", "?"),
                    "basis": (j or {}).get("reason", "")})
    return out


# ---------------------------------------------------------------- 태그 후보

def build_tags(judgements, title_words, volume=None, brand_removed=None, limit=10):
    """상품명에 못 넣은 유효 키워드를 태그 후보로. 근거 없는 채우기 금지(§6).

    - 완성형/조합형/연결형/교집합 중 상품명에 없는 것 우선.
    - 미적용/판정불가/브랜드/홍보어 제외.
    - 태그는 띄어쓰기 없이(§6-1 화면 규칙) → compact 형태로 제시.
    """
    volume = volume or {}
    brand_removed = set(compact(b) for b in (brand_removed or []) if b)
    in_title = set(compact(w) for w in title_words)
    seen = set()
    cands = []
    valid_types = {TYPE_COMPLETE, TYPE_LINKED, TYPE_COMBO, TYPE_INTERSECTION}
    for j in sorted(judgements, key=lambda j: _order_key(j["keyword"], volume)):
        kw = j["keyword"]
        ckw = compact(kw)
        if j["type"] not in valid_types:
            continue
        if ckw in in_title or ckw in seen:
            continue
        # 3조각 이상 조합형(사실상 원상품명 전체)이고 모든 조각이 이미 상품명에 있으면
        # 붙여쓴 태그는 원상품명 통짜 = 검색 무의미한 쓰레기 태그이므로 제외(§6 근거 없는 채우기 금지).
        seg_terms = j.get("matchedTerms") or []
        if (j["type"] == TYPE_COMBO and len(seg_terms) >= 3
                and all(compact(s) in in_title for s in seg_terms)):
            continue
        # 브랜드 제거대상은 부분 일치도 차단(예: '더이안'이 '더이안유산균' 안에 있으면 태그 금지)
        if any(b and b in ckw for b in brand_removed):
            continue
        if kw in PROMOTIONAL or any(p in kw for p in PROMOTIONAL):
            continue
        tag = re.sub(r"\s+", "", kw)  # 태그는 붙여쓰기
        cands.append({"tag": tag, "type": j["type"], "basis": j["reason"],
                      "monthlyVolume": volume.get(kw)})
        seen.add(ckw)
        if len(cands) >= limit:
            break
    return cands


# ---------------------------------------------------------------- 제외 목록

def collect_excluded(judgements, brand_removed=None):
    brand_removed = set(compact(b) for b in (brand_removed or []) if b)
    out = []
    for j in judgements:
        if compact(j["keyword"]) in brand_removed:
            out.append({"word": j["keyword"], "reason": "제거 대상 브랜드/판매자명(상품명·태그 금지)"})
        elif j["type"] == TYPE_NOT_APPLIED:
            out.append({"word": j["keyword"], "reason": "미적용: " + j["reason"]})
        elif j["type"] == TYPE_UNKNOWN:
            out.append({"word": j["keyword"], "reason": "판정불가(terms 없음): 추측으로 쓰지 않음"})
        elif j["type"] == TYPE_SYNONYM:
            out.append({"word": j["keyword"], "reason": "동의어: " + j["reason"]})
    return out


# ---------------------------------------------------------------- 검증 (2-5)

def verify_title(title, all_terms, all_inter):
    ct = [compact(t) for t in all_terms]
    ci = [compact(t) for t in all_inter]
    words = nfc(title).split()
    res = []
    for w in words:
        cw = compact(w)
        if cw in ct:
            st = "terms"
        elif cw in ci:
            st = "intersection"
        elif any(cw in t or t in cw for t in ct):
            st = "부분"
        else:
            st = "누락"
        res.append({"word": w, "status": st})
    missing = [r["word"] for r in res if r["status"] == "누락"]
    return {"perWord": res, "missing": missing,
            "note": "누락 단어는 교체하거나 순서 재조정. intersection 은 교집합 처리로 정상 반영(§5-2)."}


# ---------------------------------------------------------------- 메인 파이프라인

def run(f12_results, *, brand_removed=None, volume=None, synonym_pool=None):
    brand_removed = brand_removed or []
    volume = volume or {}
    # 띄어쓰기 재검색 매칭: "생유산균" 판정 시 "생 유산균" 결과가 있으면 연결형 판별에 사용(강의 2-3).
    # 같은 글자열(공백 제거 기준)을 가진 결과를 모두 모은다.
    groups = {}
    for r in f12_results:
        groups.setdefault(compact(r["keyword"]), []).append(r)

    judgements = []
    all_terms, all_inter = [], []
    for r in f12_results:
        all_terms += r["terms"]
        all_inter += r["intersection"]
    all_terms = list(dict.fromkeys(all_terms))
    all_inter = list(dict.fromkeys(all_inter))

    for r in f12_results:
        kw = r["keyword"]
        siblings = [rr for rr in groups.get(compact(kw), []) if rr is not r]
        # 붙여 쓴 형제가 있는 '띄운 변형'은 연결형 판별용 보조 자료일 뿐 → 판정표·상품명 후보에서 제외
        if " " in kw and any(" " not in rr["keyword"] for rr in siblings):
            continue
        spaced = None
        for rr in siblings:
            if " " in rr["keyword"] and (rr["terms"] or rr["intersection"]):
                spaced = rr["terms"]
                break
        j = classify(kw, r["terms"], r["intersection"], spaced_result=spaced, synonym_pool=synonym_pool)
        j["categoryTop"] = _top_category(r["categories"])
        j["blocked"] = r["blocked"]
        judgements.append(j)

    titles = build_title(judgements, volume=volume, brand_removed=brand_removed)
    title_words = []
    if titles:
        title_words = nfc(titles[0]["title"]).split()
    tags = build_tags(judgements, title_words, volume=volume, brand_removed=brand_removed)
    excluded = collect_excluded(judgements, brand_removed=brand_removed)
    verification = verify_title(titles[0]["title"], all_terms, all_inter) if titles else {}

    notes = []
    if any(j["type"] == TYPE_UNKNOWN for j in judgements):
        notes.append("일부 키워드가 판정불가(terms 없음). F12 재수집 전까지 상품명 확정을 강행하지 말 것.")
    if not volume:
        notes.append("검색량 미제공 → 완성형/조합형 정렬은 terms 등장 순 기준(F12 근거 우선). searchad 키가 있으면 --search-volume 로 보강.")
    notes.append("35자/25~30자는 이호 경험칙(WARN). 공식 상한은 100자(seo_audit.py 가 BLOCK 판정).")

    return {
        "judgeTable": [{
            "keyword": j["keyword"], "type": j["type"], "confidence": j.get("confidence"),
            "matchedTerms": j.get("matchedTerms"), "basis": j["reason"],
            "categoryTop": j.get("categoryTop"),
        } for j in judgements],
        "titleCandidates": titles,
        "tagCandidates": tags,
        "excluded": excluded,
        "verification": verification,
        "termsUniverse": {"terms": all_terms, "intersectionTerms": all_inter},
        "notes": notes,
    }


def _top_category(cats):
    best = None
    for c in cats or []:
        rv = c.get("relevance")
        try:
            rv = float(rv)
        except (TypeError, ValueError):
            continue
        if best is None or rv > best.get("relevance", -1):
            best = {"name": c.get("name"), "id": c.get("id"), "relevance": rv, "level": c.get("level")}
    return best


# ---------------------------------------------------------------- 입력 로딩

def load_facts(path: Path):
    brand_removed, volume = [], {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return brand_removed, volume
    if isinstance(data, dict):
        br = (data.get("brand") or {}).get("removedFromMarketing")
        if isinstance(br, list):
            brand_removed = [nfc(b) for b in br if b]
        # facts.json 형태로 직접 준 경우
        if isinstance(data.get("brandRemoved"), list):
            brand_removed += [nfc(b) for b in data["brandRemoved"]]
        if isinstance(data.get("searchVolume"), dict):
            volume = {nfc(k): int(v) for k, v in data["searchVolume"].items()}
    return list(dict.fromkeys(brand_removed)), volume


# ---------------------------------------------------------------- selftest (강의 유산균 예시)

def selftest():
    """강의 §4.2 유산균 100점 표본으로 판정·조립을 검증.

    강의 terms 관측(2-3B/2-4):
      유산균→[유산균] 완성형, 프로바이오틱스→[프로바이오틱스] 완성형,
      생유산균→[생유산균] (띄어도 한 덩어리) 연결형→완성형 취급,
      질유산균→[질,유산균] 조합형, 다이어트유산균→[다이어트,유산균] 조합형,
      갱년기유산균→[갱년기,유산균] 조합형, 여성유산균→[여성,유산균] 조합형,
      유산균추천→[유산균] 미적용.
    """
    f12 = [
        {"keyword": "유산균", "terms": ["유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "프로바이오틱스", "terms": ["프로바이오틱스"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "생유산균", "terms": ["생유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "질유산균", "terms": ["질", "유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "다이어트유산균", "terms": ["다이어트", "유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "갱년기유산균", "terms": ["갱년기", "유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "여성유산균", "terms": ["여성", "유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
        {"keyword": "유산균추천", "terms": ["유산균"], "intersection": [], "categories": [], "blocked": False, "note": "", "ok": True},
    ]
    volume = {"유산균": 500000, "프로바이오틱스": 200000, "질유산균": 90000, "다이어트유산균": 40000,
              "갱년기유산균": 30000, "여성유산균": 20000, "생유산균": 8000}
    res = run(f12, volume=volume)
    jt = {j["keyword"]: j["type"] for j in res["judgeTable"]}

    assert jt["유산균"] == TYPE_COMPLETE, jt
    assert jt["프로바이오틱스"] == TYPE_COMPLETE, jt
    assert jt["생유산균"] == TYPE_COMPLETE, jt  # 띄어검색 변형 없음 → 완성형
    assert jt["질유산균"] == TYPE_COMBO, jt
    assert jt["다이어트유산균"] == TYPE_COMBO, jt
    assert jt["갱년기유산균"] == TYPE_COMBO, jt
    assert jt["여성유산균"] == TYPE_COMBO, jt
    assert jt["유산균추천"] == TYPE_NOT_APPLIED, jt  # 추천 소멸

    # 미적용/추천은 제외 목록에
    assert any("추천" in e["word"] for e in res["excluded"]), res["excluded"]
    # 상품명 후보 존재 + 완성형이 앞에
    assert res["titleCandidates"], res
    first = res["titleCandidates"][0]["title"]
    assert first.split()[0] in ("유산균", "프로바이오틱스"), first
    # 유산균/프로바이오틱스 둘 다 상품명에 포함
    assert "유산균" in first and "프로바이오틱스" in first, first
    # 조합형 조각(질/갱년기/다이어트/여성)이 상품명에 반영
    assert "질" in first and "갱년기" in first, first
    # 강의 §4.2 100점 표본 재현: 공통꼬리 '유산균' 1회 공유, 34자 이내(권장창 근처)
    assert first.split()[-1] == "유산균", first  # 공통 꼬리로 끝남
    assert first.split().count("유산균") == 2, first  # 온전한 '유산균' 토큰은 정확히 2회(완성형+공통꼬리)
    assert first.split()[-2] == "질", first  # 힘 준 질유산균이 꼬리에 인접(강의 규칙)
    assert nlen(first) <= 35, (first, nlen(first))  # 이호 최대 35자 이내

    # 연결형 판별: "생유산균" + "생 유산균"(띄어검색) 둘 다 있으면 연결형
    f12b = list(f12) + [{"keyword": "생 유산균", "terms": ["생유산균"], "intersection": [],
                         "categories": [], "blocked": False, "note": "", "ok": True}]
    res2 = run(f12b, volume=volume)
    jt2 = {j["keyword"]: j["type"] for j in res2["judgeTable"]}
    assert jt2["생유산균"] == TYPE_LINKED, jt2  # 띄어도 한 덩어리 → 연결형

    # 판정불가 (terms 없음)
    res3 = run([{"keyword": "무언가", "terms": [], "intersection": [], "categories": [],
                 "blocked": True, "note": "차단", "ok": False}])
    assert res3["judgeTable"][0]["type"] == TYPE_UNKNOWN, res3
    assert any("판정불가" in n for n in res3["notes"]), res3["notes"]

    print(json.dumps({"selftest": "PASS",
                      "sample_title": first,
                      "length": nlen(first)}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--f12", action="append", default=[], help="F12 결과 JSON (여러 번)")
    ap.add_argument("--f12-dir", help="F12 결과 JSON 이 든 디렉터리")
    ap.add_argument("--facts", help="registration_plan.json 또는 facts.json")
    ap.add_argument("--brand-removed", default="")
    ap.add_argument("--search-volume", help='{"키워드": 월검색수} JSON')
    ap.add_argument("--out", help="결과 JSON 저장 경로")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    paths = [Path(p) for p in a.f12]
    if a.f12_dir:
        paths += sorted(Path(a.f12_dir).glob("*.json"))
    paths = [p for p in paths if p.exists()]
    if not paths:
        ap.error("--f12 또는 --f12-dir 로 F12 결과 JSON 을 주세요")

    f12_results = merge_same_keyword([load_f12(p) for p in paths])

    brand_removed = [b.strip() for b in a.brand_removed.split(",") if b.strip()]
    volume = {}
    if a.facts and Path(a.facts).exists():
        br2, vol2 = load_facts(Path(a.facts))
        brand_removed = list(dict.fromkeys(brand_removed + br2))
        volume.update(vol2)
    if a.search_volume and Path(a.search_volume).exists():
        try:
            volume.update({nfc(k): int(v) for k, v in json.loads(Path(a.search_volume).read_text(encoding="utf-8")).items()})
        except Exception:
            pass

    res = run(f12_results, brand_removed=brand_removed, volume=volume)
    res["inputs"] = {"f12Files": [str(p) for p in paths], "brandRemoved": brand_removed,
                     "hasSearchVolume": bool(volume)}
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
