#!/usr/bin/env python3
"""One or more registration plans → concise final confirmation table.

표준 라이브러리만. 인터넷·브라우저 접근 없음. plan/빌더 결과 JSON 만 읽는다.

F12/이호 분석을 요청한 경우에만 키워드 판정표를 추가한다. 기본 확인표에는 필수 6개 값,
seller form/법률상 필수 필드, 가격 근거, 태그 개수/출처, Coupang top-3 후보와 최종 승인에
필요한 값만 포함한다. 20개 미달이나 선택 SEO 필드는 blocker가 아니다.

원칙:
- 비어 있는 값은 '미확정' 으로 표시하고 발명하지 않는다.
- 근거 없는 수치·항목을 지어내지 않는다.

사용
  python build_confirm_table.py --plan registration_plan_1.json --plan registration_plan_2.json
        [--title-build title_build_1.json] [--coupang coupang_build_1.json] [--out confirm.md]
  python build_confirm_table.py --selftest
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import unicodedata
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

UNSET = "미확정"
NO_TARGET = "검사 대상 없음"


def nfc(s):
    return unicodedata.normalize("NFC", str(s or "")).strip()


def nlen(s):
    return len(nfc(s))


def _val(x):
    """빈 값이면 '미확정', 아니면 문자열로."""
    if x is None:
        return UNSET
    if isinstance(x, str):
        s = nfc(x)
        return s if s else UNSET
    if isinstance(x, (list, tuple)):
        items = [nfc(str(i)) for i in x if nfc(str(i))]
        return ", ".join(items) if items else UNSET
    return str(x)


def _num(x):
    if x is None or x == "":
        return UNSET
    try:
        return f"{int(x):,}원"
    except (TypeError, ValueError):
        return _val(x)


def _md_escape(s):
    return nfc(s).replace("|", r"\|").replace("\n", " ")


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


# ---------------------------------------------------------------- 키워드 판정표 (A)

def judge_table_md(judgements, market_label):
    """title_build judgeTable → 마크다운 표. 상품명/태그 반영 열은 판정으로 유도."""
    if not judgements:
        return f"#### (A) 키워드 판정표 — {market_label}\n\n_{UNSET}: title_build judgeTable 이 없습니다(F12 판정 전이거나 판정불가)._\n"
    lines = [f"#### (A) 키워드 판정표 — {market_label}", "",
             "| 키워드 | 판정 | 근거(terms/카테고리) | 상품명/태그 반영 |",
             "|---|---|---|---|"]
    for j in judgements:
        kw = _md_escape(j.get("keyword"))
        typ = _md_escape(j.get("type")) or UNSET
        basis = _md_escape(j.get("basis") or j.get("reason"))
        reflect = _reflect_hint(j.get("type"))
        lines.append(f"| {kw or UNSET} | {typ} | {basis or UNSET} | {reflect} |")
    return "\n".join(lines) + "\n"


def _reflect_hint(typ):
    typ = nfc(typ)
    return {
        "완성형": "상품명 앞자리(완성형)",
        "연결형": "상품명(붙여쓰기, 사이에 단어 금지)",
        "조합형": "상품명(왼→오·거리 최소) 또는 태그",
        "교집합": "상품명/태그(교집합 반영)",
        "미적용": "제외(수식어 소멸)",
        "동의어": "둘 중 하나만",
        "판정불가": "사용 안 함(추측 금지)",
    }.get(typ, UNSET)


# ---------------------------------------------------------------- seo_audit 요약

def audit_summary(market_result, product_name):
    """seo_audit 결과 요약. 상품명이 비면 '검사 대상 없음'(live_verify 7-3)."""
    if not nfc(product_name):
        return NO_TARGET, []
    if not isinstance(market_result, dict) or "violations" not in market_result:
        return UNSET, []
    viol = market_result.get("violations") or []
    lines = []
    for x in viol:
        sev = nfc(x.get("severity"))
        if sev in ("BLOCK", "WARN"):
            ev = nfc(x.get("evidence"))
            lines.append(f"[{sev}] {nfc(x.get('rule'))}: {nfc(x.get('message'))}" + (f" ({ev})" if ev else ""))
    block = market_result.get("block", sum(1 for x in viol if nfc(x.get("severity")) == "BLOCK"))
    warn = market_result.get("warn", sum(1 for x in viol if nfc(x.get("severity")) == "WARN"))
    ok = market_result.get("ok", block == 0)
    head = f"ok={ok}, BLOCK {block}, WARN {warn}"
    return head, lines


# ---------------------------------------------------------------- 최종 확인표 (B)

def final_table_md(plan, market, market_label, coupang_build=None):
    m = plan.get(market, {}) or {}
    brand = plan.get("brand", {}) or {}
    notice = plan.get("notice", {}) or {}
    images = plan.get("images", {}) or {}
    files = (images.get("files") or {})
    src = plan.get("source", {}) or {}
    pricing = plan.get("pricing", {}) or {}

    product_name = nfc(m.get("productName"))
    # 쿠팡은 coupang_build.exposureName 을 우선 반영값으로 제시(있으면)
    if market == "coupang" and coupang_build and coupang_build.get("exposureName"):
        if not product_name:
            product_name = nfc(coupang_build["exposureName"])

    # 이미지 개수
    thumbs = files.get("thumbs") or []
    rep = 1 if thumbs else 0
    add = max(0, len(thumbs) - 1)
    if market == "naver":
        detail_imgs = (images.get("naver", {}) or {}).get("detailEditor") or []
    else:
        detail_imgs = (images.get("coupang", {}) or {}).get("detailContents") or []

    # 가격
    if market == "naver":
        sale = m.get("salePrice")
        original = None
    else:
        sale = m.get("salePrice")
        original = m.get("originalPrice")

    # 옵션·재고
    opt_rows = src.get("optionRows") or []
    opt_text = nfc(src.get("optionsText"))
    if opt_rows:
        option_desc = f"옵션 {len(opt_rows)}행(원문). 선택된 옵션만 확인 후 사용"
    elif opt_text:
        option_desc = "옵션 텍스트 있음 — 사용자 선택 확인 필요"
    else:
        stock = m.get("stockQuantity")
        if stock is None:
            stock = src.get("stockQuantity")
        option_desc = f"단일상품(재고 {_val(stock)})" if stock is not None else "단일상품(재고 미확정)"

    # 태그/검색어: 쿠팡 helper 출처를 확인표에 그대로 드러낸다.
    tags = m.get("tags") or []
    search_term_count = len(tags)
    tag_display = _val(tags)
    if market == "coupang":
        sourced_terms = (coupang_build or {}).get("searchTerms") or []
        if sourced_terms:
            tags = [t.get("term") if isinstance(t, dict) else t for t in sourced_terms]
            search_term_count = len(tags)
            tag_display = ", ".join(
                f"{_md_escape(t.get('term'))} [{_md_escape(t.get('source'))}]"
                if isinstance(t, dict) and t.get("source")
                else _md_escape(t.get("term") if isinstance(t, dict) else t)
                for t in sourced_terms
            )
        else:
            search_term_count = len(tags)
            tag_display = _val(tags)

    category_candidates = m.get("categoryCandidates") or (
        (m.get("categoryEvidence") or {}).get("candidates") or []
    )
    candidate_text = "; ".join(
        f"{_md_escape(c.get('id') or c.get('code') or '')} {_md_escape(c.get('path') or '')}".strip()
        for c in category_candidates[:3] if isinstance(c, dict)
    ) or UNSET
    price_source = (m.get("salePriceSource") or pricing.get("salePriceSource")
                    or pricing.get("approvalSource")
                    or (pricing.get("suggested") or {}).get("formula") or UNSET)
    title_source = m.get("productNameSource") or m.get("evidenceSource") or UNSET
    tags_source = m.get("tagsSource") or m.get("evidenceSource") or UNSET
    rows = [
        ("카테고리", _val(m.get("categoryPath"))),
        ("상품명", (f"{_md_escape(product_name)} ({nlen(product_name)}자)" if product_name else UNSET)),
        ("상품명 출처", _val(title_source)),
        ("판매가", _num(sale)),
        ("가격 근거", _val(price_source)),
    ]
    if market == "coupang":
        rows.insert(1, ("쿠팡 상위 추천 후보 1~3", candidate_text))
        evidence = m.get("categoryEvidence") or {}
        official = evidence.get("officialLookup") or {}
        live = evidence.get("liveSelected") or {}
        evidence_text = "; ".join(
            part for part in (
                f"방식={nfc(evidence.get('method'))}" if evidence.get("method") else "",
                f"출처={nfc(evidence.get('fallbackSource'))}" if evidence.get("fallbackSource") else "",
                f"출처참조={nfc(evidence.get('sourceRef'))}" if evidence.get("sourceRef") else "",
                f"공식 말단={nfc(official.get('terminal'))}" if official else "",
                f"활성={nfc(official.get('active'))}" if official else "",
                f"live 선택={nfc(live.get('ok'))}" if live else "",
                f"범위={nfc(evidence.get('comparisonScope'))}" if evidence.get("comparisonScope") else "",
            ) if part
        ) or UNSET
        rows.insert(2, ("카테고리 검증 근거", evidence_text))
    if market == "coupang":
        rows.append(("정상가", _num(original)))
    if market == "naver" and m.get("existingItemId"):
        rows.append(("기존 등록 상태 / 상품번호",
                     f"{_val(m.get('existingStatus'))} / {_val(m.get('existingItemId'))} / {_val(m.get('registrationAction'))}"))
    elif market == "coupang" and m.get("registrationState"):
        rows.append(("현재 등록 상태", _val(m.get("registrationState"))))
    rows += [
        ("옵션·재고", _md_escape(option_desc)),
        ("대표/추가 이미지 수", f"대표 {rep} / 추가 {add}" if thumbs else UNSET),
        ("상세 이미지 수", str(len(detail_imgs)) if detail_imgs else UNSET),
        ("브랜드", _val(brand.get("ownKept") or "끄롱마제")),
        ("제조사/수입자", _val(notice.get("제조자/수입자"))),
        ("원산지(제조국)", _val(notice.get("제조국"))),
        ("고시 요약", _md_escape(_notice_summary(notice))),
        ("KIPRIS", "끄롱마제 자체 브랜드 조회 생략"),
        ("상품명/태그 근거 출처", f"상품명: {_val(title_source)} / 태그: {_val(tags_source)}"),
    ]
    if market == "naver":
        rows.append(("배송·반품비", "택배 유료 3,500원 / 반품 3,500원·교환 7,000원(등록 화면 확인)"))
    else:
        method = _val(m.get("deliveryMethod"))
        charge_type = _val(m.get("shippingChargeType"))
        fee = _num(m.get("shippingFee"))
        courier = _val(m.get("courier"))
        return_courier = _val(m.get("returnCourier"))
        initial = _num(m.get("initialReturnFee"))
        return_fee = _num(m.get("returnFee"))
        exchange = _num(m.get("exchangeFee"))
        days = _val(m.get("outboundDays"))
        jeju = _num(m.get("jejuAdditionalFee"))
        remote_island = _num(m.get("remoteIslandAdditionalFee"))
        address_status = _val(m.get("addressStatus"))
        rows.append((
            "배송·반품비",
            f"{method} / {courier} / {charge_type} {fee} / 출고 {days}일 / "
            f"반품 택배사 {return_courier}·초도 {initial}·편도 {return_fee}·교환 {exchange} / "
            f"제주 추가 {jeju}·도서산간 추가 {remote_island} / {address_status}"
        ))
    if market == "coupang":
        rows.append(("검색어 개수", f"{search_term_count}/20 (최대; 미달은 WARN)"))
        filled_attributes = ((m.get("attributes") or {}).get("filled") or [])
        required_attributes = [a for a in filled_attributes
                               if a.get("required") is True or a.get("group") == "required"]
        applied_filter_values = "; ".join(
            f"{_md_escape(a.get('name'))}={_md_escape(a.get('value'))}"
            for a in required_attributes
            if a.get("name") and a.get("value") is not None
        )
        rows.append(("필수 속성", applied_filter_values or "화면에서 필수인 값만 확인"))
    if market == "naver":
        tag_count_display = f"{len(tags)}/10 (목표; 미달은 WARN)"
    else:
        tag_count_display = f"{len(tags)}/20 (최대; 미달은 WARN)"
    rows.append(("태그/검색어", f"{tag_count_display} — {tag_display}"))

    lines = [f"#### (B) 최종 확인표 — {market_label}", "",
             "| 항목 | 값 |", "|---|---|"]
    for k, val in rows:
        lines.append(f"| {k} | {val} |")

    return "\n".join(lines) + "\n"


def _notice_summary(notice):
    parts = []
    for key, label in (
        ("품명", "품명"),
        ("제조국", "제조국"),
        ("제조자/수입자", "제조자/수입자"),
        ("인증", "인증"),
        ("A/S 책임자·전화", "A/S 책임자와 전화번호"),
    ):
        val = nfc(notice.get(key))
        if val:
            parts.append(f"{label}={val}")
    return " / ".join(parts) if parts else UNSET


# ---------------------------------------------------------------- 조립

def _markets_present(plan, requested):
    out = []
    for mk in ("naver", "coupang"):
        if requested and mk not in requested:
            continue
        if mk in plan:
            out.append(mk)
    return out or [mk for mk in ("naver", "coupang") if mk in plan]


def _missing_essentials(plan, markets):
    missing = []
    images = plan.get("images", {}) or {}
    files = images.get("files", {}) or {}
    has_thumb = bool(files.get("thumbs"))
    for market in markets:
        values = plan.get(market, {}) or {}
        label = "네이버" if market == "naver" else "쿠팡"
        if not nfc(values.get("productName")):
            missing.append(f"{label}: 상품명 미확정")
        if not nfc(values.get("categoryPath")):
            missing.append(f"{label}: 카테고리 미확정")
        if values.get("salePrice") in (None, ""):
            missing.append(f"{label}: 판매가 미확정")
        if not has_thumb:
            missing.append(f"{label}: 대표 이미지 없음")
        detail_key = "detailEditor" if market == "naver" else "detailContents"
        if not (images.get(market, {}) or {}).get(detail_key):
            missing.append(f"{label}: 상세페이지 없음")
    return missing


def build_many(plans, title_builds=None, coupang_builds=None, markets=None):
    labels = {"naver": "네이버 스마트스토어", "coupang": "쿠팡 윙"}
    title_builds = title_builds or []
    coupang_builds = coupang_builds or []
    out = ["# 등록 전 통합 확인표", "",
           "- 최종 제출은 아래 확인표의 명시적 사용자 승인 후에만 실행합니다.",
           "- 확인표 승인 뒤 값이 바뀌면 변경분을 다시 보여주고 재승인받습니다.", ""]

    for index, plan in enumerate(plans):
        out.extend([f"## 상품 {index + 1}: {_val(plan.get('productFolder'))}", ""])
        current_markets = _markets_present(plan, markets)
        unresolved = []
        for item in list(plan.get("blockers") or []) + _missing_essentials(plan, current_markets):
            unresolved.append(("BLOCKER", item))
        for item in plan.get("needsUser") or []:
            unresolved.append(("필수 확인", item))
        if unresolved:
            out.append("> **제출 불가: 필수값을 먼저 해결해야 합니다.**")
            out.extend(f"> - [{kind}] {_md_escape(value)}" for kind, value in unresolved)
            out.append("")

        title_build = title_builds[index] if index < len(title_builds) else {}
        coupang_build = coupang_builds[index] if index < len(coupang_builds) else {}
        for mk in _markets_present(plan, markets):
            out.extend([f"### {labels.get(mk, mk)}", ""])
            judgements = title_build.get("judgeTable") or plan.get("naver", {}).get("keywordJudgements") or []
            if mk == "naver" and judgements:
                out.append(judge_table_md(judgements, labels[mk]))
                out.append("")
            out.append(final_table_md(
                plan, mk, labels.get(mk, mk),
                coupang_build=coupang_build if mk == "coupang" else None,
            ))
            out.append("")
    return "\n".join(out).rstrip() + "\n"


def build(plan, title_build=None, coupang_build=None, markets=None):
    return build_many([plan], [title_build or {}], [coupang_build or {}], markets)


# ---------------------------------------------------------------- selftest

def selftest():
    # 1) 채워진 plan → 값이 표에 반영, 미확정 최소
    plan_full = {
        "productFolder": r"C:\done\3", "workDir": r"C:\sess\reg-3",
        "brand": {"removedFromMarketing": ["더이안"], "ownKept": ["끄롱마제"]},
        "notice": {"품명": "무선청소기 YQ-669", "제조국": "중국", "제조자/수입자": "협력업체",
                   "인증": "", "A/S 책임자·전화": "상세정보 참조"},
        "pricing": {"salePriceSource": "사용자 제공 판매가"},
        "source": {"optionRows": [], "optionsText": ""},
        "images": {"files": {"thumbs": [{"path": "t1"}, {"path": "t2"}, {"path": "t3"}]},
                   "naver": {"detailEditor": ["d1"]},
                   "coupang": {"detailContents": ["s1", "s2"]}},
        "naver": {"categoryPath": "생활/건강>청소기", "productName": "무선청소기 핸디 차량용 청소기",
                  "tags": ["무선청소기", "핸디청소기"], "salePrice": 39800,
                  "productNameSource": "maker_ui", "tagsSource": "maker_ui",
                  "keywordJudgements": []},
        "coupang": {"categoryPath": "청소기", "productName": "무선청소기 핸디 차량용",
                    "tags": [], "salePrice": 39800, "originalPrice": 59000,
                    "categoryCandidates": [{"id": "111", "path": "생활용품>청소용품>청소기"}],
                    "categoryEvidence": {"method": "bounded_fallback", "fallbackSource": "own_listing",
                                         "sourceRef": "기존상품-1", "officialLookup": {"terminal": True, "active": True},
                                         "liveSelected": {"ok": True}, "comparisonScope": "bounded_fallback"},
                    "tagsSource": "wing_recommendations_and_product_facts",
                    "attributes": {"filled": [{"name": "색상", "value": "화이트"}]}},
        "seoAudit": {
            "naver": {"ok": True, "block": 0, "warn": 1, "violations": [
                {"field": "naver.productName", "severity": "WARN", "rule": "DUPLICATE_TOKEN",
                 "message": "같은 단어 반복", "evidence": "청소기"}]},
            "coupang": {"ok": True, "block": 0, "warn": 0, "violations": []},
        },
        "blockers": [], "needsUser": [],
    }
    tb = {"judgeTable": [
        {"keyword": "무선청소기", "type": "완성형", "basis": "terms 통째"},
        {"keyword": "차량용청소기", "type": "조합형", "basis": "차량용/청소기 분해"},
        {"keyword": "무선청소기추천", "type": "미적용", "basis": "'추천' 소멸"}]}
    cb = {"exposureName": "무선청소기 핸디 차량용", "searchTermCount": 20,
          "searchTerms": [{"term": f"검색어{i}", "source": "쿠팡 자동완성"} for i in range(20)]}
    md = build(plan_full, title_build=tb, coupang_build=cb)
    assert "# 등록 전 통합 확인표" in md
    assert "네이버 스마트스토어" in md and "쿠팡 윙" in md
    assert "무선청소기 핸디 차량용 청소기" in md
    assert "39,800원" in md
    assert "대표 1 / 추가 2" in md
    assert "| 상세 이미지 수 | 1 |" in md and "| 상세 이미지 수 | 2 |" in md
    assert "검색어0" in md
    assert "seoAudit" not in md and "DUPLICATE_TOKEN" not in md
    assert "KIPRIS" in md and "가격 근거" in md
    assert "111 생활용품>청소용품>청소기" in md
    assert "출처=own_listing" in md and "live 선택=True" in md
    assert "사용자 제공 판매가" in md
    assert "A/S 책임자와 전화번호=상세정보 참조" in md

    # 2) Unfilled essential values remain visible; optional SEO audit is omitted.
    plan_empty = {
        "productFolder": "f", "workDir": "w",
        "brand": {"removedFromMarketing": []}, "notice": {},
        "source": {}, "images": {"files": {}},
        "naver": {"categoryPath": "", "productName": "", "tags": [], "salePrice": None,
                  "keywordJudgements": []},
        "coupang": {"productName": "", "tags": [], "salePrice": None, "originalPrice": None},
        "seoAudit": {"coupang": {"ok": True, "block": 0, "warn": 1, "violations": [
            {"field": "coupang.tags", "severity": "WARN", "rule": "TAG_COUNT_UNDER_TARGET",
             "message": "검색어 0/20개", "evidence": ""}]}},
    }
    md2 = build(plan_empty)
    assert UNSET in md2
    assert "TAG_COUNT_UNDER_TARGET" not in md2
    assert "판매가 | 미확정" in md2

    # 3) 판정표 없음 → 판정불가/없음 안내, 발명 안 함
    plan_min = {"naver": {"productName": "테스트상품명"}, "brand": {}, "notice": {},
                "source": {}, "images": {"files": {}}}
    md3 = build(plan_min, markets=["naver"])
    assert UNSET in md3
    assert "쿠팡" not in md3  # markets=naver 만
    md_many = build_many([plan_full, plan_empty])
    assert "상품 1:" in md_many and "상품 2:" in md_many
    assert "TAG_COUNT_UNDER_TARGET" not in md_many

    print(json.dumps({"selftest": "PASS"}, ensure_ascii=False))


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="registration_plan.json → SKILL.md §4 마켓별 최종 확인표(마크다운).")
    ap.add_argument("--plan", action="append", help="registration_plan.json (repeat for multiple products)")
    ap.add_argument("--title-build", action="append", help="naver_title_builder.py 출력 JSON, plan order")
    ap.add_argument("--coupang", action="append", help="coupang_helper.py 출력 JSON, plan order")
    ap.add_argument("--markets", help="쉼표구분: naver,coupang (기본: plan 에 있는 것)")
    ap.add_argument("--out", help="결과 마크다운 저장 경로")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    if not a.plan:
        ap.error("--plan 이 필요합니다")
    plans = [_load(path) for path in a.plan]
    if any(not plan for plan in plans):
        ap.error("등록 계획 중 로드에 실패한 파일이 있습니다")
    markets = [m.strip() for m in a.markets.split(",")] if a.markets else None

    title_builds = [_load(path) for path in (a.title_build or [])]
    coupang_builds = [_load(path) for path in (a.coupang or [])]
    md = build_many(plans, title_builds=title_builds, coupang_builds=coupang_builds, markets=markets)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
