#!/usr/bin/env python3
"""중간 산출물(JSON)을 registration_plan.json 에 병합하는 헬퍼 (표준 라이브러리만).

인터넷·브라우저 접근 없음. 근거 있는 값만 옮기고, 없는 값은 지어내지 않는다.
seo_audit.py --plan / build_confirm_table.py --plan 이 읽는 plan 필드를 한 번에 채운다.

옮기는 값(모두 F12/화면 근거 산출물에서만):
  --title-build  naver_title_builder.py 출력
      naver.productName      = titleCandidates[--title-index].title   (기본 0번; 없으면 건드리지 않음)
      naver.tags             = tagCandidates[*].tag (최대 10)
      naver.keywordJudgements= judgeTable
  --naver-category naver_category_pick.py 출력
      naver.categoryPath     = leafCandidates[--leaf-index].path 를 '>' 로 연결 (기본 0번)
      naver.categoryEvidence = {verdict, leaf, relevance, connected, nearOne, keywordAgreement, warnings}
  --coupang       coupang_helper.py 출력
      coupang.productName    = exposureName
      coupang.tags           = searchTerms[*].term
  --coupang-category coupang_category_pick.py 출력
      coupang.categoryPath   = categoryCandidates[--coupang-cat-index].path (기본 0번)
      coupang.attributes     = {filled, empty}
  --run-audit    병합 후 seo_audit.audit_plan 을 실행해 plan.seoAudit 에 기록(네이버/쿠팡).
  --seo-audit    이미 저장한 seo_audit --plan 결과 JSON 을 plan.seoAudit 에 그대로 넣음(--run-audit 대안).

기본 동작은 plan 을 제자리(in-place)로 갱신한다. --out 을 주면 그 경로로 저장한다.

사용
  python apply_to_plan.py --plan reg.json --title-build tb.json --naver-category nc.json \
         --coupang cp.json --coupang-category cc.json --run-audit
  python apply_to_plan.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass


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


def _at(seq, idx):
    seq = seq or []
    if 0 <= idx < len(seq):
        return seq[idx]
    return None


def merge(plan, title_build=None, naver_category=None, coupang=None,
          coupang_category=None, title_index=0, leaf_index=0, coupang_cat_index=0):
    """근거 산출물을 plan 에 병합. 값이 없으면 해당 필드를 건드리지 않는다(발명 금지)."""
    changed = []
    plan.setdefault("naver", {})
    plan.setdefault("coupang", {})

    # --- 네이버 상품명/태그/판정 (title_build) ---
    if title_build:
        cand = _at(title_build.get("titleCandidates"), title_index)
        if cand and cand.get("title"):
            plan["naver"]["productName"] = cand["title"]
            changed.append(f"naver.productName <- titleCandidates[{title_index}]")
        tags = [t.get("tag") for t in (title_build.get("tagCandidates") or []) if t.get("tag")]
        if tags:
            plan["naver"]["tags"] = tags[:10]
            changed.append(f"naver.tags <- tagCandidates ({len(tags[:10])})")
        if title_build.get("judgeTable") is not None:
            plan["naver"]["keywordJudgements"] = title_build["judgeTable"]
            changed.append("naver.keywordJudgements <- judgeTable")

    # --- 네이버 카테고리 (naver_category) ---
    if naver_category:
        leaf = _at(naver_category.get("leafCandidates"), leaf_index)
        if leaf and leaf.get("path"):
            plan["naver"]["categoryPath"] = ">".join(leaf["path"])
            changed.append(f"naver.categoryPath <- leafCandidates[{leaf_index}]")
        plan["naver"]["categoryEvidence"] = {
            "verdict": naver_category.get("verdict"),
            "leaf": (leaf or {}).get("leaf") if leaf else None,
            "leafRelevance": (leaf or {}).get("maxLeafRelevance") if leaf else None,
            "connected": (leaf or {}).get("connected") if leaf else None,
            "keywordAgreement": naver_category.get("keywordAgreement"),
            "warnings": naver_category.get("warnings"),
        }
        changed.append("naver.categoryEvidence <- naver_category")

    # --- 쿠팡 노출상품명/검색어 (coupang) ---
    if coupang:
        if coupang.get("exposureName"):
            plan["coupang"]["productName"] = coupang["exposureName"]
            changed.append("coupang.productName <- exposureName")
        terms = [t.get("term") if isinstance(t, dict) else t
                 for t in (coupang.get("searchTerms") or [])]
        terms = [t for t in terms if t]
        if terms:
            plan["coupang"]["tags"] = terms
            changed.append(f"coupang.tags <- searchTerms ({len(terms)})")

    # --- 쿠팡 카테고리/속성 (coupang_category) ---
    if coupang_category:
        cat = _at(coupang_category.get("categoryCandidates"), coupang_cat_index)
        if cat and cat.get("path"):
            plan["coupang"]["categoryPath"] = cat["path"]
            changed.append(f"coupang.categoryPath <- categoryCandidates[{coupang_cat_index}]")
        if coupang_category.get("attributes") is not None:
            plan["coupang"]["attributes"] = coupang_category["attributes"]
            changed.append("coupang.attributes <- coupang_category")

    return changed


def _run_audit(plan):
    """seo_audit.audit_plan 을 같은 폴더에서 import 해 실행하고 plan.seoAudit 에 기록."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import seo_audit  # noqa: E402
    res = seo_audit.audit_plan(plan)
    seo = {}
    if "naver" in res:
        seo["naver"] = res["naver"]
    if "coupang" in res:
        seo["coupang"] = res["coupang"]
    plan["seoAudit"] = seo
    return seo


def main():
    ap = argparse.ArgumentParser(description="중간 산출물 → registration_plan.json 병합 헬퍼")
    ap.add_argument("--plan")
    ap.add_argument("--title-build")
    ap.add_argument("--naver-category")
    ap.add_argument("--coupang")
    ap.add_argument("--coupang-category")
    ap.add_argument("--seo-audit", help="seo_audit --plan 결과 JSON 을 plan.seoAudit 에 그대로 기록")
    ap.add_argument("--run-audit", action="store_true", help="병합 후 seo_audit 를 실행해 plan.seoAudit 기록")
    ap.add_argument("--title-index", type=int, default=0)
    ap.add_argument("--leaf-index", type=int, default=0)
    ap.add_argument("--coupang-cat-index", type=int, default=0)
    ap.add_argument("--out", help="저장 경로(기본: --plan 제자리 갱신)")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    if not a.plan:
        ap.error("--plan 이 필요합니다")
    plan = _load(a.plan)
    if not plan:
        ap.error(f"plan 로드 실패: {a.plan}")

    changed = merge(
        plan,
        title_build=_load(a.title_build),
        naver_category=_load(a.naver_category),
        coupang=_load(a.coupang),
        coupang_category=_load(a.coupang_category),
        title_index=a.title_index, leaf_index=a.leaf_index, coupang_cat_index=a.coupang_cat_index,
    )

    audited = None
    if a.seo_audit:
        sa = _load(a.seo_audit)
        seo = {}
        for mk in ("naver", "coupang"):
            if isinstance(sa.get(mk), dict):
                seo[mk] = sa[mk]
        if seo:
            plan["seoAudit"] = seo
            changed.append("seoAudit <- --seo-audit")
            audited = seo
    if a.run_audit:
        audited = _run_audit(plan)
        changed.append("seoAudit <- seo_audit.audit_plan")

    out = Path(a.out) if a.out else Path(a.plan)
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"plan": str(out), "changed": changed,
                      "seoAudit": {mk: {"ok": v.get("ok"), "block": v.get("block"), "warn": v.get("warn")}
                                   for mk, v in (audited or {}).items()} if audited else None},
                     ensure_ascii=False, indent=2))
    return 0


def selftest():
    plan = {
        "naver": {"categoryPath": "", "categoryEvidence": {}, "keywordJudgements": [],
                  "productName": "", "tags": [], "salePrice": None},
        "coupang": {"categoryPath": "", "productName": "", "tags": [], "salePrice": None},
        "brand": {"removedFromMarketing": ["더이안"]},
    }
    tb = {
        "titleCandidates": [{"title": "무선청소기 차량용 핸디 청소기", "length": 16},
                            {"title": "핸디 무선청소기 차량용 청소기", "length": 16}],
        "tagCandidates": [{"tag": "무선청소기"}, {"tag": "핸디청소기"}, {"tag": "차량용청소기"}],
        "judgeTable": [{"keyword": "무선청소기", "type": "완성형", "matchedTerms": ["무선청소기"]}],
    }
    nc = {"verdict": "ok",
          "leafCandidates": [{"leaf": "무선청소기", "path": ["생활/건강", "청소기", "무선청소기"],
                              "maxLeafRelevance": 0.9951, "connected": True}],
          "keywordAgreement": [], "warnings": []}
    cp = {"exposureName": "무선청소기 차량용 핸디", "searchTerms": [{"term": "무선청소기"}, {"term": "핸디청소기"}]}
    cc = {"categoryCandidates": [{"path": "생활용품>청소용품>진공청소기", "code": "111", "leaf": "진공청소기"}],
          "attributes": {"filled": [{"name": "수량", "value": "1개"}], "empty": []}}

    changed = merge(plan, title_build=tb, naver_category=nc, coupang=cp, coupang_category=cc)
    assert plan["naver"]["productName"] == "무선청소기 차량용 핸디 청소기", plan["naver"]["productName"]
    assert plan["naver"]["tags"] == ["무선청소기", "핸디청소기", "차량용청소기"], plan["naver"]["tags"]
    assert plan["naver"]["keywordJudgements"] == tb["judgeTable"]
    assert plan["naver"]["categoryPath"] == "생활/건강>청소기>무선청소기", plan["naver"]["categoryPath"]
    assert plan["naver"]["categoryEvidence"]["leaf"] == "무선청소기"
    assert plan["coupang"]["productName"] == "무선청소기 차량용 핸디"
    assert plan["coupang"]["tags"] == ["무선청소기", "핸디청소기"]
    assert plan["coupang"]["categoryPath"] == "생활용품>청소용품>진공청소기"
    assert plan["coupang"]["attributes"]["filled"][0]["name"] == "수량"
    assert changed, changed

    # title-index 선택
    plan2 = {"naver": {}, "coupang": {}}
    merge(plan2, title_build=tb, title_index=1)
    assert plan2["naver"]["productName"] == "핸디 무선청소기 차량용 청소기"

    # 빈 산출물 → 발명 금지(필드 안 건드림)
    plan3 = {"naver": {"productName": "기존"}, "coupang": {}}
    merge(plan3, title_build={})
    assert plan3["naver"]["productName"] == "기존"

    # run_audit 로 plan.seoAudit 채움
    seo = _run_audit(plan)
    assert "naver" in seo and "ok" in seo["naver"], seo
    assert "coupang" in seo, seo

    print(json.dumps({"selftest": "PASS"}, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
