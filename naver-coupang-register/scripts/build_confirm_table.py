#!/usr/bin/env python3
"""registration_plan.json(+ title_build/coupang 결과) → SKILL.md §4 마켓별 최종 확인표(마크다운).

표준 라이브러리만. 인터넷·브라우저 접근 없음. plan/빌더 결과 JSON 만 읽는다.

SKILL.md §4 두 표를 생성:
  (A) 키워드 판정표  = title_build.json judgeTable (키워드/판정/근거/상품명·태그 반영)
  (B) 최종 확인표    = 카테고리, 상품명(글자수), 판매가/정상가, 옵션·재고, 대표/추가 이미지 수,
      상세 이미지 수, 브랜드/제조사/원산지, 고시 요약, 배송·반품비, 태그/검색어,
      키워드 판정표(요약), seo_audit WARN/BLOCK.

원칙:
- 비어 있는 값은 '미확정' 으로 표시하고 발명하지 않는다.
- seo_audit 는 plan 의 naver/coupang.productName 이 있을 때만 실제 검사 대상이 있다.
  "seo_audit ok" 라도 상품명이 비어 있으면 '검사 대상 없음' 으로 명시한다(live_verify 7-3).
- 근거 없는 수치·항목을 지어내지 않는다.

사용
  python build_confirm_table.py --plan registration_plan.json [--title-build title_build.json]
        [--coupang coupang_build.json] [--out confirm.md]
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
        option_desc = "단일상품(옵션 없음, 재고 999 권장)"

    # 태그/검색어
    tags = m.get("tags") or []
    if market == "coupang" and coupang_build and not tags:
        st = coupang_build.get("searchTerms") or []
        tags = [t.get("term") if isinstance(t, dict) else t for t in st]

    rows = [
        ("카테고리", _val(m.get("categoryPath"))),
        ("상품명", (f"{_md_escape(product_name)} ({nlen(product_name)}자)" if product_name else UNSET)),
        ("판매가", _num(sale)),
    ]
    if market == "coupang":
        rows.append(("정상가", _num(original)))
    rows += [
        ("옵션·재고", _md_escape(option_desc)),
        ("대표/추가 이미지 수", f"대표 {rep} / 추가 {add}" if thumbs else UNSET),
        ("상세 이미지 수", str(len(detail_imgs)) if detail_imgs else UNSET),
        ("브랜드(제거)", _val(brand.get("removedFromMarketing")) + " → 상품명·태그에서 제거"),
        ("제조사/수입자", _val(notice.get("제조자/수입자"))),
        ("원산지(제조국)", _val(notice.get("제조국"))),
        ("고시 요약", _md_escape(_notice_summary(notice))),
    ]
    if market == "naver":
        rows.append(("배송·반품비", "택배 유료 3,500원 / 반품 3,500원·교환 7,000원(등록 화면 확인)"))
    else:
        rows.append(("배송·반품비", "쿠팡 배송정책(무료배송이면 가격에 배송비 포함) 확인"))
    rows.append(("태그/검색어", _val(tags)))

    lines = [f"#### (B) 최종 확인표 — {market_label}", "",
             "| 항목 | 값 |", "|---|---|"]
    for k, val in rows:
        lines.append(f"| {k} | {val} |")

    # seo_audit
    seo = plan.get("seoAudit") or plan.get("seo_audit") or {}
    market_seo = seo.get(market) if isinstance(seo, dict) else None
    head, detail = audit_summary(market_seo, product_name)
    lines.append(f"| seo_audit | {_md_escape(head)} |")
    lines.append("")
    if head == NO_TARGET:
        lines.append(f"> seo_audit: 상품명이 비어 있어 **{NO_TARGET}**. (ok 값이 있어도 실제 검사한 상품명이 없음 — live_verify 7-3)")
    elif detail:
        lines.append("seo_audit WARN/BLOCK:")
        for d in detail:
            lines.append(f"- {_md_escape(d)}")
    elif head == UNSET:
        lines.append(f"> seo_audit 결과가 plan 에 없습니다({UNSET}). `seo_audit.py --plan` 실행 후 반영하세요.")
    else:
        lines.append("seo_audit WARN/BLOCK: 없음")
    return "\n".join(lines) + "\n"


def _notice_summary(notice):
    parts = []
    for key in ("품명", "제조국", "제조자/수입자", "인증"):
        val = nfc(notice.get(key))
        if val:
            parts.append(f"{key}={val}")
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


def build(plan, title_build=None, coupang_build=None, markets=None):
    title_build = title_build or {}
    judgements = title_build.get("judgeTable") or plan.get("naver", {}).get("keywordJudgements") or []
    label = {"naver": "네이버 스마트스토어", "coupang": "쿠팡 윙"}
    present = _markets_present(plan, markets)

    out = ["# 마켓별 최종 확인표", "",
           f"- 생성 대상 폴더: {_val(plan.get('productFolder'))}",
           f"- 작업 폴더: {_val(plan.get('workDir'))}",
           "- 값이 비면 '미확정'으로 표기했고, 없는 값을 지어내지 않았습니다.",
           "- `저장하기`/`판매요청` 은 사용자 최종 확인 후에만.", ""]

    # blockers/needsUser 알림
    blockers = plan.get("blockers") or []
    needs_user = plan.get("needsUser") or []
    if blockers:
        out.append("> **BLOCKERS (등록 전 해결 필요):**")
        for b in blockers:
            out.append(f"> - {_md_escape(b)}")
        out.append("")
    if needs_user:
        out.append("> **사용자 확인 필요:**")
        for n in needs_user:
            out.append(f"> - {_md_escape(n)}")
        out.append("")

    for mk in present:
        out.append(f"## {label.get(mk, mk)}")
        out.append("")
        # 판정표는 네이버 기준(쿠팡도 네이버 F12 판정 근거를 공유)
        out.append(judge_table_md(judgements, label.get(mk, mk)))
        out.append("")
        cb = coupang_build if mk == "coupang" else None
        out.append(final_table_md(plan, mk, label.get(mk, mk), coupang_build=cb))
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- selftest

def selftest():
    # 1) 채워진 plan → 값이 표에 반영, 미확정 최소
    plan_full = {
        "productFolder": r"C:\done\3", "workDir": r"C:\sess\reg-3",
        "brand": {"removedFromMarketing": ["더이안"]},
        "notice": {"품명": "무선청소기 YQ-669", "제조국": "중국", "제조자/수입자": "협력업체", "인증": ""},
        "source": {"optionRows": [], "optionsText": ""},
        "images": {"files": {"thumbs": [{"path": "t1"}, {"path": "t2"}, {"path": "t3"}]},
                   "naver": {"detailEditor": ["d1"]},
                   "coupang": {"detailContents": ["s1", "s2"]}},
        "naver": {"categoryPath": "생활/건강>청소기", "productName": "무선청소기 핸디 차량용 청소기",
                  "tags": ["무선청소기", "핸디청소기"], "salePrice": 39800,
                  "keywordJudgements": []},
        "coupang": {"categoryPath": "청소기", "productName": "무선청소기 핸디 차량용",
                    "tags": [], "salePrice": 39800, "originalPrice": 59000},
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
    cb = {"exposureName": "무선청소기 핸디 차량용",
          "searchTerms": [{"term": "무선청소기"}, {"term": "핸디청소기"}]}
    md = build(plan_full, title_build=tb, coupang_build=cb)
    assert "# 마켓별 최종 확인표" in md
    assert "네이버 스마트스토어" in md and "쿠팡 윙" in md
    assert "무선청소기 핸디 차량용 청소기" in md
    assert "39,800원" in md and "59,000원" in md  # 쿠팡 정상가
    assert "완성형" in md and "미적용" in md
    # 네이버 seo_audit WARN 이 표시
    assert "DUPLICATE_TOKEN" in md
    # 대표/추가 이미지 수
    assert "대표 1 / 추가 2" in md
    # 상세 이미지 수(네이버 1, 쿠팡 2)
    assert "상세 이미지 수" in md
    # 검사 대상 없음이 아닌 실제 요약
    assert NO_TARGET not in md.split("네이버 스마트스토어")[1].split("쿠팡 윙")[0]

    # 2) 상품명 비어 있는데 seo_audit ok=True → '검사 대상 없음' (live_verify 7-3)
    plan_empty = {
        "productFolder": "f", "workDir": "w",
        "brand": {"removedFromMarketing": []}, "notice": {},
        "source": {}, "images": {"files": {}},
        "naver": {"categoryPath": "", "productName": "", "tags": [], "salePrice": None,
                  "keywordJudgements": []},
        "coupang": {"productName": "", "tags": [], "salePrice": None, "originalPrice": None},
        "seoAudit": {"coupang": {"ok": True, "block": 0, "warn": 1, "violations": [
            {"field": "coupang.tags", "severity": "WARN", "rule": "TAG_SLOTS_EMPTY",
             "message": "검색어 0/20개", "evidence": ""}]}},
    }
    md2 = build(plan_empty)
    assert NO_TARGET in md2, md2
    # 상품명 미확정 표기
    assert UNSET in md2
    # ok=True 여도 검사대상없음 문구가 뜬다(제목 검사 안 됨)
    assert "실제 검사한 상품명이 없음" in md2, md2

    # 3) 판정표 없음 → 판정불가/없음 안내, 발명 안 함
    plan_min = {"naver": {"productName": "테스트상품명"}, "brand": {}, "notice": {},
                "source": {}, "images": {"files": {}}}
    md3 = build(plan_min, markets=["naver"])
    assert "판정불가" in md3 or UNSET in md3
    assert "쿠팡" not in md3  # markets=naver 만

    print(json.dumps({"selftest": "PASS"}, ensure_ascii=False))


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser(
        description="registration_plan.json → SKILL.md §4 마켓별 최종 확인표(마크다운).")
    ap.add_argument("--plan", help="registration_plan.json")
    ap.add_argument("--title-build", help="naver_title_builder.py 출력 JSON")
    ap.add_argument("--coupang", help="coupang_helper.py 출력 JSON")
    ap.add_argument("--markets", help="쉼표구분: naver,coupang (기본: plan 에 있는 것)")
    ap.add_argument("--out", help="결과 마크다운 저장 경로")
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
    markets = [m.strip() for m in a.markets.split(",")] if a.markets else None

    md = build(plan, title_build=_load(a.title_build), coupang_build=_load(a.coupang), markets=markets)
    if a.out:
        Path(a.out).write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
