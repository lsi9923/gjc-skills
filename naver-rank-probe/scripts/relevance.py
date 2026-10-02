#!/usr/bin/env python3
"""
카테고리 relevance 실측.

사용:
  python3 relevance.py "트레이닝복"
  python3 relevance.py "트레이닝복" --dump ./raw --json

출력: category1~4 각 후보의 relevance, 그리고 인덱스 짝맞춤 기반 추천 경로.
"""
import argparse
import json
import re
import sys

from nfetch import fetch_search_json, deep_find, deep_find_dicts

CAT_KEY = re.compile(r"^category([1-9])$")


def pick_label(item):
    """카테고리 항목에서 이름으로 보이는 값을 찾는다."""
    if isinstance(item, str):
        return item
    if not isinstance(item, dict):
        return str(item)
    for k in ("value", "name", "categoryName", "text", "title", "label", "cat"):
        if k in item and isinstance(item[k], str):
            return item[k]
    for v in item.values():
        if isinstance(v, str) and not v.replace(".", "").isdigit():
            return v
    return "?"


def pick_relevance(item):
    if not isinstance(item, dict):
        return None
    for k in ("relevance", "score", "weight", "rel"):
        if k in item:
            try:
                return float(item[k])
            except (TypeError, ValueError):
                pass
    return None


def extract_levels(data):
    """
    category1..N 구조를 담은 dict를 찾아 레벨별 (label, relevance) 리스트로 정규화.
    cmpOrg 안에 있는 걸 우선하되, 없으면 문서 전체에서 찾는다.
    """
    scopes = deep_find(data, "cmpOrg") or [data]
    for scope in scopes:
        holders = deep_find_dicts(
            scope, lambda d: any(CAT_KEY.match(k) for k in d.keys())
        )
        for h in holders:
            levels = {}
            for k, v in h.items():
                m = CAT_KEY.match(k)
                if not m:
                    continue
                lv = int(m.group(1))
                if isinstance(v, dict) and "categories" in v and isinstance(v["categories"], list):
                    items = v["categories"]
                elif isinstance(v, list):
                    items = v
                else:
                    items = [v]
                rows = []
                for it in items:
                    rows.append((pick_label(it), pick_relevance(it)))
                if rows:
                    levels[lv] = rows
            if levels and any(r for lv in levels.values() for _, r in lv if r is not None):
                return levels
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keyword")
    ap.add_argument("--dump", default=None, help="원본 JSON 저장 폴더")
    ap.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    a = ap.parse_args()

    data, meta = fetch_search_json(a.keyword, want_keys=("cmpOrg", "category1"), dump_dir=a.dump)
    if data is None:
        sys.exit(1)

    levels = extract_levels(data)
    if not levels:
        print("[FAIL] categoryN/relevance 구조를 찾지 못했습니다. --dump 로 원본 저장 후 구조 확인 필요.",
              file=sys.stderr)
        sys.exit(2)

    if a.json:
        print(json.dumps({"keyword": a.keyword, "levels": {str(k): v for k, v in levels.items()}},
                         ensure_ascii=False, indent=2))
        return

    print(f"\n■ 키워드: {a.keyword}   (transport: {meta['transport']})\n")
    for lv in sorted(levels):
        print(f"[category{lv}]")
        rows = levels[lv]
        for idx, (label, rel) in enumerate(rows):
            bar = ""
            if rel is not None:
                bar = "█" * max(1, int(rel * 20))
            mark = "  ← 1.0 만점" if rel == 1.0 else ""
            print(f"  {idx:>2}. {label:<24} {rel if rel is not None else '-':<6} {bar}{mark}")
        print()

    # 인덱스 짝맞춤 추천 경로
    print("■ 추천 경로 (각 레벨 최고 relevance의 인덱스 정렬 기준)")
    best_idx = {}
    for lv in sorted(levels):
        rows = levels[lv]
        scored = [(i, l, r) for i, (l, r) in enumerate(rows) if r is not None]
        if scored:
            best_idx[lv] = max(scored, key=lambda t: t[2])
    if best_idx:
        top_lv = min(best_idx)
        anchor = best_idx[top_lv][0]
        path = []
        for lv in sorted(levels):
            rows = levels[lv]
            # 상위 레벨의 인덱스와 짝을 맞춘다 (category2의 n번 ↔ category3의 n번)
            i = anchor if lv > top_lv and anchor < len(rows) else best_idx.get(lv, (0,))[0]
            if i < len(rows):
                path.append(f"{rows[i][0]}({rows[i][1]})")
        print("  " + " > ".join(path))
    print("\n※ relevance는 학습으로 갱신되는 변동값. 등록 직전에 다시 확인할 것.")
    print("※ 최저 수준(0.0x)의 카테고리는 사실상 노출 불가.\n")


if __name__ == "__main__":
    main()
