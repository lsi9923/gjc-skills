#!/usr/bin/env python3
"""
naver-seo-sudong-skill 자동 실측 파이프라인.

사용:
  python run_pipeline.py "자전거장갑" --title "자전거장갑 겨울 방한 라이딩 터치스크린 킥보드"
  python run_pipeline.py "방한장갑" --json
"""
import argparse
import json
import sys
from pathlib import Path

from nfetch import fetch_search_json, deep_find, _ensure_chrome_running
from relevance import extract_levels
from terms import flatten_terms, check_title


def run_seo_probe(keyword: str, title: str | None = None) -> dict:
    # 1. 크롬 CDP 자동 실행 보장
    _ensure_chrome_running(9222)

    # 2. 실측 검색 데이터 가져오기
    data, meta = fetch_search_json(
        keyword,
        want_keys=("cmpOrg", "category1", "terms", "cmp", "compositeList", "relatedQueries"),
        verbose=False,
    )
    if not data:
        return {"error": "네이버쇼핑 실측 데이터를 가져오지 못했습니다. 크롬 로그인 상태를 확인하세요."}

    # 3. 카테고리 relevance 추출
    levels = extract_levels(data)
    best_path = []
    best_relevance = 0.0
    if levels:
        path_items = []
        for lv in sorted(levels):
            rows = levels[lv]
            scored = [(idx, name, rel) for idx, (name, rel) in enumerate(rows) if rel is not None]
            if scored:
                top = max(scored, key=lambda x: x[2])
                path_items.append(f"{top[1]}({top[2]:.4f})")
                if lv == 1:
                    best_relevance = top[2]
        best_path = " > ".join(path_items)

    # 4. terms 및 공식 연관검색어 추출
    raw_terms = flatten_terms(deep_find(data, "terms"))
    inter = flatten_terms(deep_find(data, "intersectionTerms"))

    # 연관검색어
    related_queries = []
    for rq_key in ("relatedQueries", "relatedQueriesBottom"):
        for rq_block in deep_find(data, rq_key) or []:
            items = rq_block if isinstance(rq_block, list) else [rq_block]
            for it in items:
                if isinstance(it, dict) and "query" in it and isinstance(it["query"], str):
                    related_queries.append(it["query"])
                elif isinstance(it, str):
                    related_queries.append(it)
    related_queries = flatten_terms(related_queries)

    # terms 보강
    if not raw_terms and not inter:
        extracted = []
        for k in ("category1NameIdxTerm", "category2NameIdxTerm", "category3NameIdxTerm", "category4NameIdxTerm"):
            for v in deep_find(data, k):
                if isinstance(v, str):
                    extracted.extend(v.split(","))
        extracted.extend(related_queries)
        raw_terms = flatten_terms(extracted)
        if keyword not in raw_terms:
            raw_terms.insert(0, keyword)

    # 5. 추천 태그 10개 선정
    tag_candidates = [keyword] + related_queries
    final_tags = []
    seen = set()
    for t in tag_candidates:
        clean = t.replace(" ", "")
        if clean and clean not in seen:
            seen.add(clean)
            final_tags.append(clean)
        if len(final_tags) >= 10:
            break

    result = {
        "keyword": keyword,
        "transport": meta.get("transport"),
        "best_category_path": best_path,
        "best_relevance": best_relevance,
        "levels": {str(k): v for k, v in levels.items()},
        "terms": raw_terms[:15],
        "related_queries": related_queries[:15],
        "recommended_tags": final_tags,
    }

    # 6. 상품명 검증
    if title:
        result["title_check"] = check_title(title, raw_terms, inter)

    return result


def main():
    ap = argparse.ArgumentParser(description="네이버 SEO 수동등록 실측 파이프라인")
    ap.add_argument("keyword", help="분석할 타깃 메인 키워드")
    ap.add_argument("--title", default=None, help="검증할 상품명 후보")
    ap.add_argument("--json", action="store_true", help="JSON 형태로 출력")
    args = ap.parse_args()

    res = run_seo_probe(args.keyword, title=args.title)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return

    print(f"\n==================================================")
    print(f"■ 네이버 SEO 실측 결과: {res['keyword']}")
    print(f"==================================================")
    print(f"• 데이터 소스: {res.get('transport')}")
    print(f"• 카테고리 1위 경로: {res.get('best_category_path')}")
    print(f"\n[공식 연관검색어 ({len(res.get('related_queries', []))}개)]")
    print("  " + ", ".join(res.get('related_queries', [])[:10]))

    print(f"\n[형태소 색인어 Terms ({len(res.get('terms', []))}개)]")
    print("  " + ", ".join(res.get('terms', [])[:10]))

    print(f"\n[스마트스토어 추천 태그 10개]")
    print("  " + ", ".join(res.get('recommended_tags', [])))

    if "title_check" in res:
        tc = res["title_check"]
        print(f"\n[상품명 검증] \"{tc['title']}\" ({tc['length_with_space']}자)")
        if tc["missing"]:
            print(f"  ✗ 누락된 term: {tc['missing']}")
        else:
            print("  ✓ 필수 terms 전부 포함됨")
        for w in tc.get("warn", []):
            print(f"  ⚠ {w}")
    print(f"==================================================\n")


if __name__ == "__main__":
    main()
