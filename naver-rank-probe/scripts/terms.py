#!/usr/bin/env python3
"""
terms / intersectionTerms 실측 + 상품명 매칭 검증.

사용:
  python3 terms.py "햇완두콩"
  python3 terms.py "질유산균" --title "여성 질유산균 30포 프리미엄 유산균"

--title 을 주면:
  - terms 중 상품명에 빠진 게 있는지
  - 조합형 키워드의 좌→우 순서가 맞는지
  - 글자 수(공백 포함)가 25~30자(최대 35자) 안인지
를 판정한다.
"""
import argparse
import json
import sys

from nfetch import fetch_search_json, deep_find


def flatten_terms(vals):
    out = []
    for v in vals:
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            for x in v:
                if isinstance(x, str):
                    out.append(x)
                elif isinstance(x, dict):
                    for k in ("term", "value", "name", "text"):
                        if isinstance(x.get(k), str):
                            out.append(x[k])
                            break
        elif isinstance(v, dict):
            for k in ("term", "value", "name", "text"):
                if isinstance(v.get(k), str):
                    out.append(v[k])
                    break
    seen, res = set(), []
    for t in out:
        t = t.strip()
        if t and t not in seen:
            seen.add(t)
            res.append(t)
    return res


def check_title(title, terms, inter):
    norm = title.replace(" ", "")
    report = {"title": title, "length_with_space": len(title), "missing": [], "order": [], "warn": []}

    for t in terms + inter:
        if t.replace(" ", "") not in norm:
            report["missing"].append(t)

    # 좌→우 순서: terms가 상품명에 등장하는 위치 순서를 확인
    pos = [(t, norm.find(t.replace(" ", ""))) for t in terms if t.replace(" ", "") in norm]
    report["order"] = pos
    ordered = [p for _, p in pos]
    if ordered != sorted(ordered):
        report["warn"].append("terms 등장 순서가 검색엔진 형태소 순서와 어긋납니다 (조합 가점 누락 위험).")

    n = len(title)
    if n > 35:
        report["warn"].append(f"{n}자 — 35자 초과. 감점 구간.")
    elif n > 30:
        report["warn"].append(f"{n}자 — 권장(25~30자) 초과, 35자 이내라 허용 범위.")
    elif n < 25:
        report["warn"].append(f"{n}자 — 25자 미만. 서브 키워드를 더 담을 여지가 있습니다.")

    # 중복 단어
    words = title.split()
    dup = {w for w in words if words.count(w) > 1}
    if dup:
        report["warn"].append(f"중복 단어 {sorted(dup)} — 예외적 1회만 허용, 검색품질 체크 감점 위험.")
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--title", default=None, help="검증할 상품명")
    ap.add_argument("--dump", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    data, meta = fetch_search_json(a.keyword, want_keys=("terms", "intersectionTerms", "compositeList", "cmp"), dump_dir=a.dump)
    if data is None:
        sys.exit(1)

    terms = flatten_terms(deep_find(data, "terms"))
    inter = flatten_terms(deep_find(data, "intersectionTerms"))
    if not terms and not inter:
        extracted = []
        for key in ("category1NameIdxTerm", "category2NameIdxTerm", "category3NameIdxTerm", "category4NameIdxTerm"):
            for val in deep_find(data, key):
                if isinstance(val, str):
                    extracted.extend(val.split(","))
        for item in deep_find(data, "relatedQueries") or []:
            if isinstance(item, str):
                extracted.append(item)
            elif isinstance(item, dict) and "query" in item:
                extracted.append(item["query"])
        terms = flatten_terms(extracted)
        if a.keyword not in terms:
            terms.insert(0, a.keyword)
    result = {"keyword": a.keyword, "terms": terms, "intersectionTerms": inter}
    if a.title:
        result["check"] = check_title(a.title, terms, inter)

    if a.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"\n■ 키워드: {a.keyword}   (transport: {meta['transport']})")
    print(f"\n[terms]              {terms if terms else '- 없음'}")
    print(f"[intersectionTerms]  {inter if inter else '- 없음'}")

    if not terms and not inter:
        print("\n구조를 못 찾았습니다. --dump 로 원본 저장 후 키 이름 확인 필요.", file=sys.stderr)
        sys.exit(2)

    if a.title:
        c = result["check"]
        print(f"\n■ 상품명 검증: \"{a.title}\"  ({c['length_with_space']}자, 공백 포함)")
        if c["missing"]:
            print(f"  ✗ 상품명에 빠진 term: {c['missing']}")
        else:
            print("  ✓ terms / intersectionTerms 전부 상품명에 포함됨")
        if c["order"]:
            print("  · 등장 위치: " + ", ".join(f"{t}@{p}" for t, p in c["order"]))
        for w in c["warn"]:
            print(f"  ⚠ {w}")
    print()


if __name__ == "__main__":
    main()
