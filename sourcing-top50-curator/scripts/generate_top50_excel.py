#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Evidence-led v4.0 sourcing recommendation workbook generation pipeline."""
import sys
import argparse
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from data_loader import load_and_merge_candidates, DEFAULT_OUT_PATH
from scoring_engine import score_and_classify_candidate
from live_verifier import verify_and_enrich_pool, CACHE_DIR
from excel_builder import build_v3_workbook


def run_curation(input_paths, out_path: Path):
    raw_candidates = load_and_merge_candidates(input_paths)
    ranked = []
    seen_identity = set()
    for cand in raw_candidates:
        scored = score_and_classify_candidate(cand)
        if not scored:
            continue
        identity = re.sub(r"\W+", "", scored["clean_name"]).casefold()
        if not identity or identity in seen_identity:
            continue
        seen_identity.add(identity)
        scored["thumb_png"] = None
        scored["img_verified_200"] = False
        ranked.append(scored)

    # Source/price evidence is a hard quality gate before social novelty; it prevents
    # a high-virality caption with no identifiable offer from outranking a real item.
    ranked = [r for r in ranked if r.get("purchase_url") or r.get("has_exact_price")]
    ranked.sort(key=lambda x: (bool(x.get("has_exact_price")), bool(x.get("purchase_url")), x["s_v3"], x["evidence_confidence"]), reverse=True)
    agency = [r for r in ranked if r["sourcing_type"] == "해외구매대행 추천"]
    sourcing = [r for r in ranked if r["sourcing_type"] == "사입 추천"]
    # Verify all ranked candidates across both sourcing types.
    verify_pool = agency + sourcing
    verified = verify_and_enrich_pool(verify_pool, max_workers=24)
    verified_agency = [r for r in verified if r["sourcing_type"] == "해외구매대행 추천" and r.get("img_verified_200")]
    verified_sourcing = [r for r in verified if r["sourcing_type"] == "사입 추천" and r.get("img_verified_200")]
    for rows in (verified_agency, verified_sourcing):
        rows.sort(key=lambda x: (bool(x.get("has_exact_price")), bool(x.get("purchase_url")), x["s_v3"], x["evidence_confidence"]), reverse=True)

    if not verified_agency or not verified_sourcing:
        raise RuntimeError(
            f"검증 썸네일 후보 부족: 구매대행 {len(verified_agency)}개, 사입 {len(verified_sourcing)}개. "
            "네트워크 또는 입력 후보 데이터 확인이 필요합니다."
        )
    top_agency = verified_agency
    top_sourcing = verified_sourcing
    res = build_v3_workbook(top_agency, top_sourcing, out_path, CACHE_DIR)
    print(
        f"[OK v4.0] Saved {res['out_path']} ({res['file_size']:,} bytes) | "
        f"구매대행 추천: {res['agency_count']}개, 사입 추천: {res['sourcing_count']}개, "
        f"HTTP 200 또는 캐시 검증 썸네일: {res['verified_images']}/{res['total_count']}개"
    )
    print(f"통합 TOP 5: {' | '.join(r['clean_name'] for r in sorted(top_agency + top_sourcing, key=lambda x:x['s_v3'], reverse=True)[:5])}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="*", help="Input CSV/XLSX/JSON files or directories; default uses ProductIdeaRadar latest + SQLite")
    parser.add_argument("--out", default=str(DEFAULT_OUT_PATH), help="Output Excel path")
    args = parser.parse_args()
    run_curation(args.inputs, Path(args.out))
