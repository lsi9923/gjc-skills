#!/usr/bin/env python3
"""이호 강의 2-1 규칙으로 카테고리 relevance 를 합쳐 말단(leaf) 카테고리 후보를 낸다.

표준 라이브러리만. 인터넷·브라우저 접근 없음. F12 근거(JSON)만 입력으로 받는다.

규칙 근거: references/seo-rules.md 2번(카테고리 relevance 1.0 판단, 이호 강의 §1 정리).
- §1-2: 각 category 항목의 relevance 가 카테고리 가점. **1에 가까울수록 만점**(실측 0.994401 등). [2-1:12:44]
- §1-3: 상위 depth 가 같으면 볼 필요 없고 **갈라지는 depth** 에서 relevance 를 비교. [2-1:13:32]
- §1-4: 최종 가점은 최하위 leaf 에서 확정. 부모-자식이 실제로 이어지는 경로만.
        임의 조합 금지("절대 건강분말로 접근 금지" 류). [2-1:20:01]
- §1-6: 솔루션 "%" 는 공식 가점 아님. 항상 F12 로 검증.
- 데이터가 없으면 '판정불가'(추측 금지).

입력 (naver_search_extract.js / naver_f12_capture.js 가 낸 JSON):
  - naver_f12_capture.js: {"target":{"keyword":..}, "categoryPackets":[{"level":1..4,"categories":[{name,id,relevance}]}]}
  - naver_search_extract.js: {"query":.., "categoryLevels":[{"level":1..4,"categories":[{name,id,relevance}]}]}
  둘 다 지원. 파일당 키워드 1개(파일명/target/query 로 식별).

사용
  python naver_category_pick.py --in-dir <검색결과 JSON 폴더> --out out.json
  python naver_category_pick.py --in a.json --in b.json --out out.json
  python naver_category_pick.py --product-use "유산균 건강식품" --out out.json   # 용도 불일치 경고 힌트
  python naver_category_pick.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

# Windows PowerShell cp949 콘솔에서 한글/em-dash 출력 크래시 방지
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

# 강의 실측 relevance 1.0 근처 기준값(그대로 사용).
# [2-1:13:04] 트레이닝복 1차 패션의류 0.994401 을 "만점(1.0 근처)"으로 봄.
NEAR_ONE = 0.99        # 이 값 이상이면 "1.0 근처(만점급)"
# 강의 [2-1:16:46]: 트레이닝복 2차 여성의류 0.529709 vs 남성의류 0.460538(격차 ~0.069)을
# "크지 않아 인기도로 커버 가능"이라 함 → 그 이상 벌어져야 우열이 분명하다고 본다.
DECISIVE_GAP = 0.10    # 갈라지는 depth 에서 이 이상 벌어지면 우열이 분명


def nfc(s):
    return unicodedata.normalize("NFC", str(s or "")).strip()


def compact(s):
    return re.sub(r"\s+", "", nfc(s)).lower()


def _to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- 입력 로딩

def load_result(path: Path):
    """검색결과 JSON 하나 → {keyword, levels:{1:[{name,id,relevance}],...}, blocked, note, ok}."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"keyword": path.stem, "levels": {}, "blocked": False,
                "note": f"JSON 파싱 실패: {e}", "ok": False, "source": str(path)}
    if not isinstance(data, dict):
        data = {}

    tgt = data.get("target")
    if isinstance(tgt, dict):
        kw = nfc(tgt.get("keyword") or tgt.get("query"))
    elif isinstance(tgt, str):
        kw = nfc(tgt)
    else:
        kw = ""
    if not kw:
        kw = nfc(data.get("query") or data.get("keyword") or _strip_prefix(path.stem))

    levels = {}

    def add_level(level, cats):
        lv = level if isinstance(level, int) else None
        rows = []
        for c in cats or []:
            name = nfc(c.get("name") or c.get("categoryName"))
            if not name:
                continue
            rows.append({"name": name, "id": nfc(c.get("id") or c.get("categoryId")),
                         "relevance": _to_float(c.get("relevance") if c.get("relevance") is not None else c.get("score"))})
        if rows:
            levels.setdefault(lv, [])
            # 병합(같은 이름은 relevance 최댓값 유지)
            by_name = {compact(r["name"]): r for r in levels[lv]}
            for r in rows:
                k = compact(r["name"])
                if k in by_name:
                    old = by_name[k]
                    if (r["relevance"] or -1) > (old["relevance"] or -1):
                        by_name[k] = r
                else:
                    by_name[k] = r
            levels[lv] = list(by_name.values())

    # naver_f12_capture.js: categoryPackets
    for pk in data.get("categoryPackets") or []:
        add_level(pk.get("level"), pk.get("categories"))
    # naver_search_extract.js: categoryLevels
    for lv in data.get("categoryLevels") or []:
        add_level(lv.get("level"), lv.get("categories"))

    blocked = bool(data.get("blockedOrCaptcha") or data.get("httpBlocked"))
    note = data.get("schemaNote") or data.get("note") or ""
    ok = bool(levels) and not blocked
    return {"keyword": kw, "levels": levels, "blocked": blocked,
            "note": note, "ok": ok, "source": str(path)}


def _strip_prefix(stem):
    # "00_유산균" → "유산균", "f12_유산균" → "유산균"
    return re.sub(r"^(\d+[_-]|f12[_-]|search[_-])", "", stem)


# ---------------------------------------------------------------- 경로(부모-자식) 재구성

def build_paths(levels):
    """단일 키워드 패킷의 레벨별 카테고리(CMP_ORG category1~4)에서 leaf 경로를 만든다.

    강의 §1-3/§1-4: 상위 depth 는 최우세(relevance 최대) 카테고리를 따라 내려가고,
    최종 가점은 최하위 leaf 에서 확정한다. **임의 조합 금지** = 서로 다른 키워드/패킷의
    카테고리를 섞지 않는다는 뜻이다. 한 패킷의 category1→2→3→4 는 그 검색어의 실제
    카테고리 계층이므로(엔프론트 CMP_ORG), 상위 depth 의 '최우세 가지'를 따라 내려간
    경로만 연결로 본다(강의가 실제로 그 가지를 따라간다, [2-1:13:32]/[2-1:20:01]).

    네이버 카테고리 id 는 문자열 접두가 계층을 뜻하지 않으므로 id 접두 매칭은 쓰지 않는다.
    같은 depth 에서 갈리는 하위 후보는 divergingByKeyword 로 따로 비교한다.

    반환: [{path:[{level,name,id,relevance}], leafRelevance, minRelevance, connected:bool}]
    """
    if not levels:
        return []
    depths = sorted(l for l in levels.keys() if isinstance(l, int))
    if not depths:
        # 레벨 미상 → 단일 묶음 처리(각 항목이 곧 leaf)
        rows = []
        for cats in levels.values():
            rows += cats
        return [{"path": [{"level": None, **c}], "leafRelevance": c.get("relevance"),
                 "minRelevance": c.get("relevance"), "connected": False} for c in rows]

    def rel(c):
        return c.get("relevance") if c.get("relevance") is not None else -1

    # 상위 depth 최우세 가지를 따라 내려간 '주 경로'(연결로 표시)
    main = []
    for d in depths:
        best = max(levels[d], key=rel)
        main.append({"level": d, **best})
    main_rels = [c["relevance"] for c in main if c.get("relevance") is not None]
    out = [{"path": main, "leafRelevance": main[-1].get("relevance"),
            "minRelevance": min(main_rels) if main_rels else None, "connected": True}]

    # 최하위(leaf) depth 의 나머지 후보들은 단일 depth 후보로 별도 노출(임의 조합 아님)
    leaf_depth = depths[-1]
    main_leaf_key = compact(main[-1]["name"])
    for c in levels[leaf_depth]:
        if compact(c["name"]) == main_leaf_key:
            continue
        out.append({"path": [{"level": leaf_depth, **c}], "leafRelevance": c.get("relevance"),
                    "minRelevance": c.get("relevance"), "connected": False})
    return out


# ---------------------------------------------------------------- 갈라지는 depth 비교

def diverging_depths(levels):
    """§1-3: 후보가 2개 이상으로 갈라지는 depth 별 relevance 비교표."""
    out = []
    for d in sorted(l for l in levels.keys() if isinstance(l, int)):
        cats = sorted(levels[d], key=lambda c: -(c.get("relevance") or -1))
        if len(cats) >= 2:
            top, second = cats[0], cats[1]
            gap = None
            if top.get("relevance") is not None and second.get("relevance") is not None:
                gap = round(top["relevance"] - second["relevance"], 6)
            out.append({
                "level": d,
                "top": {"name": top["name"], "relevance": top.get("relevance")},
                "second": {"name": second["name"], "relevance": second.get("relevance")},
                "gap": gap,
                "decisive": (gap is not None and gap >= DECISIVE_GAP),
                "note": ("우열 분명(격차 큼)" if (gap is not None and gap >= DECISIVE_GAP)
                         else "근소차 — 인기도·실제 상품 성격으로 결정(§1-3)" if gap is not None
                         else "relevance 값 없음"),
                "candidates": [{"name": c["name"], "relevance": c.get("relevance")} for c in cats[:6]],
            })
    return out


# ---------------------------------------------------------------- 키워드 간 일치도

def keyword_agreement(per_keyword_leaves):
    """여러 키워드가 같은 leaf 카테고리를 가리키는지(일치도)."""
    counter = {}
    for kw, leaves in per_keyword_leaves.items():
        for leaf in leaves:
            key = compact(leaf["name"])
            counter.setdefault(key, {"name": leaf["name"], "keywords": set(), "relevances": []})
            counter[key]["keywords"].add(kw)
            if leaf.get("relevance") is not None:
                counter[key]["relevances"].append(leaf["relevance"])
    total_kw = len([k for k, v in per_keyword_leaves.items() if v])
    out = []
    for key, info in counter.items():
        rels = info["relevances"]
        out.append({
            "category": info["name"],
            "agreeingKeywords": sorted(info["keywords"]),
            "keywordCount": len(info["keywords"]),
            "totalKeywords": total_kw,
            "maxRelevance": max(rels) if rels else None,
            "avgRelevance": round(sum(rels) / len(rels), 6) if rels else None,
        })
    out.sort(key=lambda x: (-x["keywordCount"], -(x["maxRelevance"] or -1)))
    return out


# ---------------------------------------------------------------- 상품 용도 불일치 경고

def use_mismatch(final_name, product_use):
    """상품 용도 텍스트와 최종 카테고리명이 공유 토큰이 하나도 없으면 경고(§1-4 건강분말 류)."""
    if not product_use or not final_name:
        return None
    use_tokens = set(t for t in re.findall(r"[0-9A-Za-z가-힣]{2,}", product_use))
    cat_tokens = set(t for t in re.findall(r"[0-9A-Za-z가-힣]{2,}", final_name))
    shared = use_tokens & cat_tokens
    if not shared:
        # 띄어쓰기 차이 보정: 공백 제거 후 한쪽이 다른 쪽을 부분포함하면 공유로 인정
        # (예: leaf '무선청소기' ⊇ 용도 토큰 '청소기', 또는 compact 용도 ⊇ leaf).
        cat_compact = compact(final_name)
        use_compact = compact(product_use)
        tokens = use_tokens | cat_tokens
        overlap = (cat_compact and use_compact
                   and (cat_compact in use_compact or use_compact in cat_compact))
        overlap = overlap or any(
            len(a) >= 2 and len(b) >= 2 and (a in b or b in a)
            for a in tokens for b in tokens if a != b
            and ((a in cat_tokens and b in use_tokens) or (a in use_tokens and b in cat_tokens))
        )
        if overlap:
            return None
        return (f"경고: 최종 카테고리 '{final_name}' 가 상품 용도('{product_use}')와 "
                "공유하는 단어가 없습니다. 실제 상품 성격과 맞는지 사람이 확인하세요(§1-4).")
    return None


# ---------------------------------------------------------------- 메인 파이프라인

def run(results, *, product_use=""):
    valid = [r for r in results if r["ok"]]
    blocked = [r for r in results if r["blocked"]]
    empty = [r for r in results if not r["ok"] and not r["blocked"]]

    if not valid:
        reason = "차단/캡차로 카테고리 데이터 없음" if blocked else "카테고리 relevance 데이터 없음"
        return {
            "verdict": "판정불가",
            "reason": reason + " — 추측하지 않음(§1-6, 데이터 없으면 판정불가)",
            "leafCandidates": [], "divergingByKeyword": {}, "keywordAgreement": [],
            "warnings": [], "inputs": {"valid": 0, "blocked": len(blocked), "empty": len(empty)},
            "notes": ["카테고리는 F12 relevance 근거로만 확정. 데이터가 없으면 상품 등록 전 재수집."],
        }

    # 전체 병합 레벨(키워드 간 relevance 합치기 — 같은 이름은 최댓값)
    merged_levels = {}
    per_keyword_leaves = {}
    diverging_by_keyword = {}
    all_leaf_paths = []

    for r in valid:
        paths = build_paths(r["levels"])
        # 이 키워드의 leaf 후보
        leaves = [{"name": p["path"][-1]["name"], "id": p["path"][-1].get("id"),
                   "relevance": p["leafRelevance"], "connected": p["connected"],
                   "path": [c["name"] for c in p["path"]]} for p in paths]
        per_keyword_leaves[r["keyword"]] = leaves
        diverging_by_keyword[r["keyword"]] = diverging_depths(r["levels"])
        for p in paths:
            all_leaf_paths.append({"keyword": r["keyword"], **p})
        # 병합 레벨
        for lv, cats in r["levels"].items():
            merged_levels.setdefault(lv, {})
            for c in cats:
                k = compact(c["name"])
                cur = merged_levels[lv].get(k)
                if cur is None or (c.get("relevance") or -1) > (cur.get("relevance") or -1):
                    merged_levels[lv][k] = dict(c)
    merged_levels = {lv: list(d.values()) for lv, d in merged_levels.items()}

    # leaf 후보 집계: 같은 leaf 이름은 최고 relevance 로 대표, 임의조합(connected=False)은 표시만
    leaf_agg = {}
    for lp in all_leaf_paths:
        leaf = lp["path"][-1]
        key = compact(leaf["name"])
        entry = leaf_agg.setdefault(key, {
            "leaf": leaf["name"], "id": leaf.get("id"),
            "path": [c["name"] for c in lp["path"]],
            "maxLeafRelevance": None, "connected": lp["connected"],
            "fromKeywords": set(),
        })
        entry["fromKeywords"].add(lp["keyword"])
        lr = lp.get("leafRelevance")
        if lr is not None and (entry["maxLeafRelevance"] is None or lr > entry["maxLeafRelevance"]):
            entry["maxLeafRelevance"] = lr
            entry["path"] = [c["name"] for c in lp["path"]]
            entry["id"] = leaf.get("id")
        entry["connected"] = entry["connected"] or lp["connected"]

    leaf_candidates = []
    for e in leaf_agg.values():
        rel = e["maxLeafRelevance"]
        leaf_candidates.append({
            "leaf": e["leaf"], "id": e["id"], "path": e["path"],
            "leafRelevance": rel,
            "nearOne": (rel is not None and rel >= NEAR_ONE),
            "relevanceNote": _rel_note(rel),
            "parentChildConnected": e["connected"],
            "connectionNote": ("부모-자식 id 로 실제 이어지는 경로" if e["connected"]
                               else "부모-자식 연결 근거 없음 — 단일 depth 후보(임의 조합 아님, 스토어 카테고리 검색창에서 실제 말단인지 확인)"),
            "fromKeywords": sorted(e["fromKeywords"]),
        })
    # relevance 1.0 근처 우선, 연결된 경로 우선
    leaf_candidates.sort(key=lambda c: (-(c["leafRelevance"] or -1), not c["parentChildConnected"]))

    agreement = keyword_agreement(per_keyword_leaves)

    # 경고 모음
    warnings = []
    if leaf_candidates:
        top = leaf_candidates[0]
        if not top["nearOne"]:
            warnings.append(f"주의: 최상위 후보 '{top['leaf']}' relevance={top['leafRelevance']} — "
                            f"1.0 근처({NEAR_ONE}+) 아님. 갈라지는 depth 를 다시 보고 인기도로 커버 가능한지 판단(§1-3).")
        if not top["parentChildConnected"]:
            warnings.append(f"주의: 최상위 후보 '{top['leaf']}' 는 부모-자식 연결 근거가 없습니다. "
                            "임의 조합 금지 — 스토어 카테고리 검색창에서 실제 선택 가능한 말단인지 확인(§1-4).")
        um = use_mismatch(top["leaf"], product_use)
        if um:
            warnings.append(um)
    # 키워드 간 불일치
    if agreement and agreement[0]["totalKeywords"] >= 2 and agreement[0]["keywordCount"] < agreement[0]["totalKeywords"]:
        warnings.append(f"키워드 간 일치도 부분적: '{agreement[0]['category']}' 에 "
                        f"{agreement[0]['keywordCount']}/{agreement[0]['totalKeywords']} 키워드만 동의. "
                        "키워드마다 카테고리가 갈리면 대표 카테고리 확정에 주의(§1-3).")

    verdict = "후보있음"
    notes = [
        f"relevance 는 1에 가까울수록 만점(강의 §1-2 실측 0.994401 류). 기준값 {NEAR_ONE} 이상을 '1.0 근처'로 표시.",
        "relevance 는 네이버 AI 학습으로 변동(§1-5) → 주기적 재확인. 리프 최종 확정은 스토어 카테고리 검색창에서.",
        "솔루션 '%' 는 공식 가점 아님(§1-6). 여기 값은 모두 F12 relevance 근거.",
    ]

    return {
        "verdict": verdict,
        "leafCandidates": leaf_candidates,
        "divergingByKeyword": diverging_by_keyword,
        "keywordAgreement": agreement,
        "warnings": warnings,
        "mergedLevels": {str(lv): sorted(cats, key=lambda c: -(c.get("relevance") or -1))
                         for lv, cats in sorted(merged_levels.items(), key=lambda x: (x[0] is None, x[0]))},
        "inputs": {"valid": len(valid), "blocked": len(blocked), "empty": len(empty),
                   "keywords": [r["keyword"] for r in valid]},
        "notes": notes,
    }


def _rel_note(rel):
    if rel is None:
        return "relevance 값 없음 — 판정 보류"
    if rel >= NEAR_ONE:
        return f"1.0 근처(만점급, {rel})"
    if rel >= 0.5:
        return f"우세({rel}) — 갈라지는 depth 확인"
    return f"낮음({rel}) — 이 카테고리로 접근 지양(§1-4)"


# ---------------------------------------------------------------- selftest

def selftest():
    # 강의 트레이닝복 실측(§1-3): 1차 패션의류 0.994401 vs 출산/육아 0.004876,
    # 2차 여성의류 0.529709 vs 남성의류 0.460538
    r1 = {
        "keyword": "트레이닝복",
        "categoryLevels": [
            {"level": 1, "categories": [
                {"name": "패션의류", "id": "50000000", "relevance": 0.994401},
                {"name": "출산/육아", "id": "50000005", "relevance": 0.004876}]},
            {"level": 2, "categories": [
                {"name": "여성의류", "id": "50000167", "relevance": 0.529709},
                {"name": "남성의류", "id": "50000168", "relevance": 0.460538}]},
        ],
        "blockedOrCaptcha": False,
    }
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "00_트레이닝복.json"
        p.write_text(json.dumps(r1, ensure_ascii=False), encoding="utf-8")
        res = run([load_result(p)])

    assert res["verdict"] == "후보있음", res
    # 주 경로 leaf 는 여성의류(2차 최우세), 부모 패션의류 가지에서 연결
    top = res["leafCandidates"][0]
    assert top["leaf"] == "여성의류", res["leafCandidates"]
    assert top["parentChildConnected"] is True, top
    assert "패션의류" in top["path"] and "여성의류" in top["path"], top
    # 갈라지는 depth 표: 1차는 격차 큼(decisive), 2차는 근소차
    dv = res["divergingByKeyword"]["트레이닝복"]
    lv1 = next(d for d in dv if d["level"] == 1)
    lv2 = next(d for d in dv if d["level"] == 2)
    assert lv1["decisive"] is True, lv1
    assert lv2["decisive"] is False, lv2   # 0.53 vs 0.46 근소차
    assert nfc(lv1["top"]["name"]) == "패션의류", lv1

    # 파바빈(§1-4): 건강분말 매우 낮음 → 접근 지양. 잡곡·혼합곡 0.61 우세.
    r2 = {"query": "파바빈", "categoryLevels": [
        {"level": 3, "categories": [
            {"name": "잡곡/혼합곡", "id": "50008201", "relevance": 0.61},
            {"name": "단백질보충제", "id": "50008202", "relevance": 0.33},
            {"name": "건강분말", "id": "50008203", "relevance": 0.05}]}]}
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "파바빈.json"
        p.write_text(json.dumps(r2, ensure_ascii=False), encoding="utf-8")
        res2 = run([load_result(p)], product_use="잡곡 콩 건강식품")
    top2 = res2["leafCandidates"][0]
    assert top2["leaf"] == "잡곡/혼합곡", top2
    assert top2["nearOne"] is False, top2   # 0.61 은 1.0 근처 아님 → 주의 경고
    assert any("1.0 근처" in w for w in res2["warnings"]), res2["warnings"]
    # 건강분말은 relevance 낮음 표기
    low = next(c for c in res2["leafCandidates"] if c["leaf"] == "건강분말")
    assert "낮음" in low["relevanceNote"], low

    # 용도 불일치 경고: 최종 후보가 상품 용도와 공유 단어 없음
    res3 = run([load_result_from_dict({"query": "무언가", "categoryLevels": [
        {"level": 1, "categories": [{"name": "주방용품", "id": "5001", "relevance": 0.97}]}]})],
        product_use="유산균 건강식품")
    assert any("용도" in w for w in res3["warnings"]), res3["warnings"]

    # 판정불가: 차단
    res4 = run([load_result_from_dict({"target": {"keyword": "x"}, "categoryPackets": [],
                                       "blockedOrCaptcha": True})])
    assert res4["verdict"] == "판정불가", res4
    assert "판정불가" in res4["reason"] or "추측" in res4["reason"], res4

    # 키워드 간 일치도: 두 키워드가 같은 leaf
    a = load_result_from_dict({"query": "유산균", "categoryLevels": [
        {"level": 4, "categories": [{"name": "프로바이오틱스", "id": "50002344", "relevance": 0.98}]}]})
    b = load_result_from_dict({"query": "질유산균", "categoryLevels": [
        {"level": 4, "categories": [{"name": "프로바이오틱스", "id": "50002344", "relevance": 0.95}]}]})
    res5 = run([a, b])
    ag = res5["keywordAgreement"][0]
    assert ag["keywordCount"] == 2 and ag["category"] == "프로바이오틱스", ag

    print(json.dumps({"selftest": "PASS",
                      "trainingLeaf": top["leaf"],
                      "pababinTop": top2["leaf"]}, ensure_ascii=False))


def load_result_from_dict(d):
    """selftest 용: dict 를 임시 파일 없이 load_result 스키마로 변환."""
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False)
        name = fh.name
    try:
        return load_result(Path(name))
    finally:
        try:
            Path(name).unlink()
        except OSError:
            pass


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="이호 §1 규칙으로 F12/검색결과 카테고리 relevance 를 합쳐 말단 후보를 낸다.")
    ap.add_argument("--in", dest="inputs", action="append", default=[],
                    help="검색결과 JSON (naver_search_extract.js / naver_f12_capture.js 출력). 여러 번 지정 가능")
    ap.add_argument("--in-dir", help="검색결과 JSON 이 든 디렉터리(*.json)")
    ap.add_argument("--product-use", default="", help="상품 실제 용도 텍스트(용도 불일치 경고용)")
    ap.add_argument("--out", help="결과 JSON 저장 경로")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    paths = [Path(p) for p in a.inputs]
    if a.in_dir:
        paths += sorted(Path(a.in_dir).glob("*.json"))
    paths = [p for p in paths if p.exists()]
    if not paths:
        ap.error("--in 또는 --in-dir 로 검색결과 JSON 을 주세요")

    results = [load_result(p) for p in paths]
    res = run(results, product_use=a.product_use)
    res["inputs"]["files"] = [str(p) for p in paths]
    text = json.dumps(res, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
