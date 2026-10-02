#!/usr/bin/env python3
"""네이버/쿠팡 상품명·태그 사전검사 (표준 라이브러리만 사용).

규칙 출처
- 네이버: NaverSEOStudio 개발자 코드 @coupang-auto/naver-seo/seo-compliance.js 포팅
  (네이버 가격비교 상품정보 연동 가이드 14/29/36쪽) + 이호 강의 2-3~2-5 상품명 규칙.
- 쿠팡: Coupang Open API 상품 생성 스펙 (sellerProductName/displayProductName 100자,
  searchTags 20개·개당 20자·허용 특수문자 !@#$%^&*-+;:'.) + 판매자 가이드.

사용
  python seo_audit.py naver  --title "..." --tags "a,b,c" [--brand-removed "더이안"]
  python seo_audit.py coupang --title "..." --tags "a,b,c" [--brand-removed "더이안"]
  python seo_audit.py --plan <registration_plan.json>   # plan 안의 naver/coupang 값을 모두 검사
  python seo_audit.py --selftest
출력은 JSON. exit code 0 = BLOCK 없음, 2 = BLOCK 있음.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import sys
import unicodedata

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

PROMOTIONAL = [
    "최저가", "최저", "할인", "특가", "세일", "쿠폰", "적립", "사은품", "증정", "무료배송", "배송비무료",
    "당일발송", "당일출고", "오늘출발", "이벤트", "프로모션", "한정수량", "품절임박", "마감임박",
    "1+1", "2+1", "원플러스원", "덤핑", "땡처리", "폭탄세일", "공짜", "무료증정", "리뷰이벤트",
    "카드혜택", "무이자", "핫딜", "타임세일", "오픈특가", "런칭특가",
]
# 레거시 데스크톱 스킬이 25자 채우기용으로 넣던 무근거 수식어. 실제 근거 없이 쓰면 금지.
FILLER = ["추천", "인기", "신형", "고급", "실속형", "필수템", "강추", "대박", "베스트", "명품", "정품"]
OPTION_UMBRELLA = [
    "색상랜덤", "랜덤발송", "색상선택", "사이즈선택", "옵션선택", "택1", "중선택", "골라담기",
    "모음전", "다양한색상", "여러색상", "컬러선택", "size선택",
]
REGION_WORDS = ["서울", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "경기", "강원",
                "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
PHONE = re.compile(r"\d{2,4}[-.\s]\d{3,4}[-.\s]\d{4}")
ATTENTION = re.compile(r"[^\w\s\-_./()%+&,]", re.UNICODE)
CONTROL = re.compile(r"[\u0000-\u001f\u007f-\u009f\u00a0\u1680\u2000-\u200f\u2028\u2029\u202f\u205f\u3000\ufeff]")
CJK = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
COUPANG_TAG_ALLOWED = re.compile(r"^[0-9A-Za-z가-힣ㄱ-ㅎㅏ-ㅣ\s!@#$%^&*\-+;:'.]+$")


def nlen(s: str) -> int:
    return len(unicodedata.normalize("NFC", s))


def v(field, severity, rule, message, evidence=""):
    return {"field": field, "severity": severity, "rule": rule, "message": message, "evidence": evidence}


def _phrases(field, value, phrases, severity, rule, message):
    collapsed = re.sub(r"\s+", "", value)
    hits = [p for p in phrases if p.replace(" ", "") in collapsed]
    return [v(field, severity, rule, message, ", ".join(hits))] if hits else []


def _dup_token(value):
    seen = set()
    for tok in unicodedata.normalize("NFC", value).split():
        if len(tok) < 2:
            continue
        k = tok.lower()
        if k in seen:
            return tok
        seen.add(k)
    return None


def audit_title_common(field, title, brand_removed):
    out = []
    if not title.strip():
        return [v(field, "BLOCK", "EMPTY", "상품명이 비어 있습니다")]
    if CONTROL.search(title):
        out.append(v(field, "BLOCK", "CONTROL_CHARACTER", "탭·엔터·특수 공백은 무효 처리 사유입니다"))
    if nlen(title) > 100:
        out.append(v(field, "BLOCK", "LENGTH_OVER_LIMIT", f"상품명 상한 100자 초과 ({nlen(title)}자)"))
    out += _phrases(field, title, PROMOTIONAL, "BLOCK", "PROMOTIONAL_PHRASE", "홍보·혜택·배송 문구는 상품명에 넣을 수 없습니다")
    out += _phrases(field, title, OPTION_UMBRELLA, "BLOCK", "OPTION_UMBRELLA", "옵션 포괄 표현은 상품명에 넣을 수 없습니다")
    out += _phrases(field, title, FILLER, "WARN", "UNSUPPORTED_FILLER", "원상품 근거 없는 수식어입니다. 근거가 없으면 제거하세요")
    if PHONE.search(title):
        out.append(v(field, "BLOCK", "PHONE_IN_NAME", "전화번호는 상품명에 넣을 수 없습니다", PHONE.search(title).group(0)))
    att = ATTENTION.findall(title)
    if len(att) > 2:
        out.append(v(field, "BLOCK", "EXCESSIVE_SPECIAL_CHARS", "주목용 특수문자 과다", " ".join(sorted(set(att)))))
    if CJK.search(title):
        out.append(v(field, "BLOCK", "UNTRANSLATED_TEXT", "번역되지 않은 한자가 남아 있습니다", "".join(CJK.findall(title))))
    for b in brand_removed:
        if b and b.lower() in title.lower():
            out.append(v(field, "BLOCK", "REMOVED_BRAND_LEAK", "제거 대상 판매자/브랜드명이 상품명에 남아 있습니다", b))
    region = next((r for r in REGION_WORDS if r in title), None)
    if region:
        out.append(v(field, "WARN", "REGION_IN_NAME", "상품 실제 정보가 아니면 지역명은 저품질 사유입니다", region))
    dup = _dup_token(title)
    if dup:
        out.append(v(field, "WARN", "DUPLICATE_TOKEN", "같은 단어 반복(이호: 동일 키워드 1회 원칙)", dup))
    return out


def audit_naver(title, tags, brand_removed):
    out = audit_title_common("naver.productName", title, brand_removed)
    n = nlen(title)
    if n and not (25 <= n <= 35):
        out.append(v("naver.productName", "INFO", "IHO_LENGTH_WINDOW",
                     f"이호 강의 권장창 25~30자(최대 35자) 밖입니다({n}자). 공식 규칙은 아니므로 근거 없는 단어로 억지로 채우지 않습니다"))
    cleaned = [t.strip() for t in tags if t.strip()]
    if len(cleaned) > 10:
        out.append(v("naver.tags", "BLOCK", "TAG_COUNT_OVER_LIMIT", f"네이버 태그는 10개까지 ({len(cleaned)}개)"))
    kept = cleaned[:10]
    total = sum(nlen(t) for t in kept)
    if total > 100:
        out.append(v("naver.tags", "WARN", "TAG_TOTAL_LENGTH", f"태그 총 {total}자 > 100자"))
    seen = set()
    for t in kept:
        if t in seen:
            out.append(v("naver.tags", "WARN", "TAG_DUPLICATE", "중복 태그", t))
        seen.add(t)
        if " " in t:
            out.append(v("naver.tags", "WARN", "TAG_HAS_SPACE", "태그는 띄어쓰기 없이 입력", t))
        if CJK.search(t) or CONTROL.search(t):
            out.append(v("naver.tags", "BLOCK", "TAG_INVALID_CHARS", "한자/제어문자 태그", t))
        for b in brand_removed:
            if b and b in t:
                out.append(v("naver.tags", "BLOCK", "REMOVED_BRAND_LEAK", "제거 대상 브랜드가 태그에 남음", t))
    out += _phrases("naver.tags", "".join(kept), PROMOTIONAL, "WARN", "PROMOTIONAL_TAG", "홍보성 태그는 노출 중단될 수 있습니다")
    return out


def audit_coupang(title, tags, brand_removed):
    out = audit_title_common("coupang.productName", title, brand_removed)
    cleaned = [t.strip() for t in tags if t.strip()]
    if len(cleaned) > 20:
        out.append(v("coupang.tags", "BLOCK", "TAG_COUNT_OVER_LIMIT", f"쿠팡 검색어는 최대 20개 ({len(cleaned)}개)"))
    elif len(cleaned) < 20:
        out.append(v("coupang.tags", "WARN", "TAG_SLOTS_EMPTY", f"검색어 {len(cleaned)}/20개. 상품 근거 있는 키워드로 채울 수 있으면 채웁니다"))
    seen = set()
    for t in cleaned:
        if nlen(t) > 20:
            out.append(v("coupang.tags", "BLOCK", "TAG_TOO_LONG", "검색어 1개당 20자 이내", t))
        if not COUPANG_TAG_ALLOWED.match(t):
            out.append(v("coupang.tags", "BLOCK", "TAG_INVALID_CHARS", "허용 특수문자(!@#$%^&*-+;:'.) 외 문자", t))
        if t.lower() in seen:
            out.append(v("coupang.tags", "WARN", "TAG_DUPLICATE", "중복 검색어", t))
        seen.add(t.lower())
        for b in brand_removed:
            if b and b in t:
                out.append(v("coupang.tags", "BLOCK", "REMOVED_BRAND_LEAK", "제거 대상 브랜드가 검색어에 남음", t))
        if t.replace(" ", "") in title.replace(" ", ""):
            out.append(v("coupang.tags", "INFO", "TAG_IN_TITLE", "상품명에 이미 있는 단어입니다(슬롯 낭비 여부 확인)", t))
    out += _phrases("coupang.tags", "".join(cleaned), PROMOTIONAL, "BLOCK", "PROMOTIONAL_TAG", "홍보성 검색어 금지")
    return out


def summarize(violations):
    return {
        "ok": not any(x["severity"] == "BLOCK" for x in violations),
        "block": sum(x["severity"] == "BLOCK" for x in violations),
        "warn": sum(x["severity"] == "WARN" for x in violations),
        "violations": violations,
    }


def audit_iho_order(title, judgements):
    """이호 §4 배치 규칙 자동 게이트 (구버전 terms.py order 로직 이식).

    judgements = plan.naver.keywordJudgements = naver_title_builder judgeTable.
    - IHO_HEAD_COMPLETE: 상품명 첫 토큰이 완성형인가(왼쪽 0번은 완성형 가점).
    - IHO_COMBO_ORDER: 조합형 matchedTerms 가 상품명에서 왼→오 순서로 등장하는가(뒤집히면 감점).
    """
    out = []
    if not title or not judgements:
        return out
    toks = unicodedata.normalize("NFC", title).split()
    ctoks = [re.sub(r"\s+", "", t).lower() for t in toks]
    if not ctoks:
        return out

    def cc(s):
        return re.sub(r"\s+", "", unicodedata.normalize("NFC", str(s or ""))).lower()

    # 완성형/연결형 집합
    complete = [j for j in judgements if j.get("type") in ("완성형", "연결형")]
    head_ok = any(cc(j.get("keyword")) == ctoks[0]
                  or (j.get("matchedTerms") and cc(j["matchedTerms"][0]) == ctoks[0])
                  for j in complete)
    if complete and not head_ok:
        out.append(v("naver.productName", "WARN", "IHO_HEAD_COMPLETE",
                     "상품명 0번(맨 앞)이 완성형이 아닙니다. 완성형을 앞에 두면 좌측 가점을 받습니다",
                     toks[0]))
    # 조합형 왼→오 순서: matchedTerms 가 상품명 토큰에서 순서대로(부분수열) 나타나는가.
    # 공통 꼬리(유산균)가 여러 번 나와도 왼→오 부분수열이 존재하면 OK.
    for j in judgements:
        if j.get("type") != "조합형":
            continue
        segs = [cc(s) for s in (j.get("matchedTerms") or [])]
        segs = [s for s in segs if s in ctoks]
        if len(segs) < 2:
            continue
        # 부분수열 매칭: 각 seg 를 이전 위치 이후에서 찾을 수 있으면 왼→오 성립
        pos = -1
        ok = True
        for s in segs:
            nxt = next((i for i in range(pos + 1, len(ctoks)) if ctoks[i] == s), None)
            if nxt is None:
                ok = False
                break
            pos = nxt
        if not ok:
            out.append(v("naver.productName", "WARN", "IHO_COMBO_ORDER",
                         f"조합형 '{j.get('keyword')}' 조각이 상품명에서 왼→오 순서가 아닙니다(순서 뒤집히면 가점↓)",
                         " ".join(j.get("matchedTerms") or [])))
    return out


def audit_plan(plan):
    br = plan.get("brand", {}).get("removedFromMarketing", [])
    res = {}
    nv = plan.get("naver", {})
    if nv.get("productName"):
        viol = audit_naver(nv["productName"], nv.get("tags", []), br)
        viol += audit_iho_order(nv["productName"], nv.get("keywordJudgements", []))
        res["naver"] = summarize(viol)
    cp = plan.get("coupang", {})
    if cp.get("productName"):
        res["coupang"] = summarize(audit_coupang(cp["productName"], cp.get("tags", []), br))
    res["ok"] = all(r["ok"] for r in res.values() if isinstance(r, dict))
    return res


def selftest():
    bad = audit_naver("더이안 퍼즐펀치 최저가 무료배송 퍼즐펀치 추천", ["퍼즐 펀치", "더이안"], ["더이안"])
    rules = {x["rule"] for x in bad}
    assert {"PROMOTIONAL_PHRASE", "REMOVED_BRAND_LEAK", "DUPLICATE_TOKEN", "UNSUPPORTED_FILLER", "TAG_HAS_SPACE"} <= rules, rules
    good = audit_naver("퍼즐펀치 모양펀치 퍼즐 만들기 DIY 종이 펀칭기", ["퍼즐펀치", "모양펀치", "펀칭기"], ["더이안"])
    assert summarize(good)["ok"], good
    cp_bad = audit_coupang("x" * 101, ["a" * 21, "특가", "태그<>"] + [f"t{i}" for i in range(19)], [])
    r2 = {x["rule"] for x in cp_bad}
    assert {"LENGTH_OVER_LIMIT", "TAG_TOO_LONG", "TAG_COUNT_OVER_LIMIT", "TAG_INVALID_CHARS", "PROMOTIONAL_TAG"} <= r2, r2
    cp_good = audit_coupang("퍼즐펀치 모양펀치 종이 퍼즐 만들기 펀칭기 어린이 DIY 공예 도구",
                            [f"퍼즐키워드{i}" for i in range(20)], ["더이안"])
    assert summarize(cp_good)["ok"], cp_good
    assert summarize(audit_naver("퍼즐펀치\t모양", [], []))["ok"] is False
    # 이호 배치 규칙: 완성형이 0번이 아니면 WARN, 조합형 순서 뒤집히면 WARN
    judg = [{"keyword": "유산균", "type": "완성형", "matchedTerms": ["유산균"]},
            {"keyword": "질유산균", "type": "조합형", "matchedTerms": ["질", "유산균"]}]
    ord_ok = {x["rule"] for x in audit_iho_order("유산균 질 유산균", judg)}
    assert "IHO_HEAD_COMPLETE" not in ord_ok and "IHO_COMBO_ORDER" not in ord_ok, ord_ok
    ord_bad = {x["rule"] for x in audit_iho_order("질 유산균", [
        {"keyword": "질유산균", "type": "조합형", "matchedTerms": ["질", "유산균"]},
        {"keyword": "유산균", "type": "완성형", "matchedTerms": ["유산균"]}])}
    # '질'이 0번 → 완성형 아님 → HEAD 경고
    assert "IHO_HEAD_COMPLETE" in ord_bad, ord_bad
    rev = {x["rule"] for x in audit_iho_order("유산균 질", [
        {"keyword": "질유산균", "type": "조합형", "matchedTerms": ["질", "유산균"]},
        {"keyword": "유산균", "type": "완성형", "matchedTerms": ["유산균"]}])}
    assert "IHO_COMBO_ORDER" in rev, rev  # 유산균(1) 질(0) → 왼→오 위배
    print(json.dumps({"selftest": "PASS"}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("market", nargs="?", choices=["naver", "coupang"])
    ap.add_argument("--title", default="")
    ap.add_argument("--tags", default="")
    ap.add_argument("--brand-removed", default="")
    ap.add_argument("--plan")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if a.plan:
        with open(a.plan, encoding="utf-8") as fh:
            res = audit_plan(json.load(fh))
    else:
        if not a.market:
            ap.error("market 또는 --plan 필요")
        tags = [t for t in a.tags.split(",")] if a.tags else []
        br = [b.strip() for b in a.brand_removed.split(",") if b.strip()]
        fn = audit_naver if a.market == "naver" else audit_coupang
        res = summarize(fn(a.title, tags, br))
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0 if res.get("ok") else 2


if __name__ == "__main__":
    sys.exit(main())
