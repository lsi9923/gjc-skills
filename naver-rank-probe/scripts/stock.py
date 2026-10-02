#!/usr/bin/env python3
"""
경쟁 상품 재고 스냅샷 → 차감분으로 실판매 개수 추정.

사용:
  python3 stock.py "https://smartstore.naver.com/xxx/products/123456"        # 1회 스냅샷
  python3 stock.py <URL> --log ./stock.csv                                   # CSV 누적
  python3 stock.py --report ./stock.csv                                      # 구간별 차감량 리포트

주의: ERP/통합솔루션 셀러는 타 채널 판매·도매 출고·임의 수정으로 재고가 급변한다.
      차감분을 곧바로 판매량으로 단정하지 말 것.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys

from nfetch import _session, deep_find, deep_find_dicts


def snapshot(url):
    s, transport = _session()
    r = s.get(url, timeout=20)
    html = r.text

    # 페이지에 임베드된 JSON(__PRELOADED_STATE__ 등)에서 재고 키를 찾는다
    blobs = re.findall(r"=\s*(\{.*?\})\s*;?\s*</script>", html, re.S)
    blobs += re.findall(r'"stockQuantity"\s*:\s*\d+', html)
    total, options = None, []

    for b in blobs:
        if "stockQuantity" not in b:
            continue
        try:
            data = json.loads(b)
        except Exception:
            m = re.findall(r'"stockQuantity"\s*:\s*(\d+)', b)
            if m:
                nums = [int(x) for x in m]
                total = total or max(nums)
                options = nums
            continue
        vals = deep_find(data, "stockQuantity")
        nums = [v for v in vals if isinstance(v, int)]
        if nums:
            total = max(nums)
            options = nums
            # 옵션명까지 붙일 수 있으면 붙인다
            opt_dicts = deep_find_dicts(
                data, lambda d: "stockQuantity" in d and any(
                    k in d for k in ("optionName1", "optionName", "name")))
            if opt_dicts:
                options = [(d.get("optionName1") or d.get("optionName") or d.get("name"),
                            d.get("stockQuantity")) for d in opt_dicts]
            break

    if total is None:
        print("[FAIL] stockQuantity를 찾지 못했습니다. 페이지 구조 변경 또는 차단.", file=sys.stderr)
        sys.exit(1)
    return {"ts": dt.datetime.now().isoformat(timespec="seconds"),
            "url": url, "total": total, "options": options, "transport": transport}


def report(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    if len(rows) < 2:
        print("스냅샷이 2개 이상 있어야 차감량을 계산합니다.")
        return
    print(f"\n■ 재고 차감 리포트 ({len(rows)}개 스냅샷)\n")
    prev = None
    total_sold = 0
    for r in rows:
        cur = int(r["total"])
        if prev is not None:
            d = prev - cur
            flag = "" if d >= 0 else "   ← 재고 증가(입고/수정 추정, 판매량 아님)"
            if d > 0:
                total_sold += d
            print(f"  {r['ts']}   재고 {cur:>6}   차감 {d:>+6}{flag}")
        else:
            print(f"  {r['ts']}   재고 {cur:>6}   (기준점)")
        prev = cur
    span = f"{rows[0]['ts']} ~ {rows[-1]['ts']}"
    print(f"\n  구간: {span}")
    print(f"  누적 차감(추정 판매 개수): {total_sold}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--log", default=None, help="CSV에 누적 기록")
    ap.add_argument("--report", default=None, help="CSV로 차감량 리포트 출력")
    a = ap.parse_args()

    if a.report:
        report(a.report)
        return
    if not a.url:
        ap.error("URL 또는 --report 필요")

    snap = snapshot(a.url)
    print(f"\n{snap['ts']}  총 재고: {snap['total']}")
    if snap["options"]:
        print(f"  옵션별: {snap['options']}")

    if a.log:
        new = not os.path.exists(a.log)
        with open(a.log, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["ts", "url", "total"])
            w.writerow([snap["ts"], snap["url"], snap["total"]])
        print(f"  → {a.log} 기록됨")
    print()


if __name__ == "__main__":
    main()
