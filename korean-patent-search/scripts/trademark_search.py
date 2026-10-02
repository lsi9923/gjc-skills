#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KIPRIS 공식 상표(Trademark) 직접 검색 및 상표권 침해 판정 모듈.
- KIPRIS Plus Open API (trademarkInfoSearchService) 지원
- KIPRIS 웹 공식 상표 직접 검색 URL 및 다이렉트 쿼리 지원
- 네이버 우회 검색 완전 배제 및 KIPRIS 공식 특허청 데이터 직결
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

SERVICE_KEY_ENV_VAR = "KIPRIS_PLUS_API_KEY"
DEFAULT_TIMEOUT = 15
DEFAULT_NUM_ROWS = 10
DEFAULT_PAGE_NO = 1
BASE_API_URL = "https://plus.kipris.or.kr/kipo-api/kipi/trademarkInfoSearchService"
SEARCH_OPERATION = "getWordSearch"

DEFAULT_HEADERS = {
    "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
}


@dataclass(frozen=True)
class TrademarkItem:
    index_no: int | None
    application_number: str
    trademark_name: str | None
    register_status: str | None  # 등록, 출원, 소멸, 거절, 포기 등
    application_date: str | None
    publication_date: str | None
    register_date: str | None
    applicant_name: str | None
    classification_code: str | None  # 상품분류 (Nice 분류 / 류)
    kipris_url: str


@dataclass(frozen=True)
class TrademarkSearchResponse:
    query: str
    total_count: int
    direct_kipris_url: str
    has_registered_trademark: bool
    risk_level: str  # HIGH (등록상표 존재), MEDIUM (출원/심사진행), SAFE (미등록/공용)
    items: list[TrademarkItem]


def build_kipris_web_url(query: str) -> str:
    """KIPRIS 공식 웹사이트 상표 검색 다이렉트 URL 생성 (네이버 검색 배제)"""
    q_enc = urllib.parse.quote(query)
    return (
        f"http://www.kipris.or.kr/khome/search/searchResult.do"
        f"?searchKind=totalSearch&searchRight=trademark"
        f"&queryText={q_enc}&queryTextTop={q_enc}&expression={q_enc}"
    )


def search_trademark_api(
    query: str,
    service_key: str,
    page_no: int = DEFAULT_PAGE_NO,
    num_of_rows: int = DEFAULT_NUM_ROWS,
    timeout: int = DEFAULT_TIMEOUT,
) -> TrademarkSearchResponse:
    """KIPRIS Plus 공식 상표 API 검색"""
    url = f"{BASE_API_URL}/{SEARCH_OPERATION}"
    params = {
        "word": query,
        "pageNo": str(page_no),
        "numOfRows": str(num_of_rows),
        "ServiceKey": urllib.parse.unquote(service_key),
    }
    req_url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(req_url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        xml_text = resp.read().decode("utf-8", errors="replace")

    root = ET.fromstring(xml_text)
    header = root.find("header")
    res_code = header.findtext("resultCode") if header is not None else None
    if res_code and res_code != "00":
        err_msg = header.findtext("resultMsg") if header is not None else ""
        raise RuntimeError(f"KIPRIS API error: {err_msg or res_code}")

    body = root.find("body")
    total_count = int(body.findtext("totalCount") or "0") if body is not None else 0
    items_el = body.find("items") if body is not None else None

    items: list[TrademarkItem] = []
    has_reg = False
    if items_el is not None:
        for item in items_el.findall("item"):
            app_no = item.findtext("applicationNumber") or ""
            tm_name = item.findtext("title") or item.findtext("trademarkName")
            reg_status = item.findtext("registerStatus") or "심사중"
            if "등록" in reg_status:
                has_reg = True
            items.append(
                TrademarkItem(
                    index_no=int(item.findtext("indexNo") or "0"),
                    application_number=app_no,
                    trademark_name=tm_name,
                    register_status=reg_status,
                    application_date=item.findtext("applicationDate"),
                    publication_date=item.findtext("publicationDate"),
                    register_date=item.findtext("registerDate"),
                    applicant_name=item.findtext("applicantName"),
                    classification_code=item.findtext("classificationCode"),
                    kipris_url=build_kipris_web_url(query),
                )
            )

    risk = "HIGH" if has_reg else ("MEDIUM" if total_count > 0 else "SAFE")
    return TrademarkSearchResponse(
        query=query,
        total_count=total_count,
        direct_kipris_url=build_kipris_web_url(query),
        has_registered_trademark=has_reg,
        risk_level=risk,
        items=items,
    )


def search_trademark(query: str, service_key: str | None = None) -> TrademarkSearchResponse:
    """KIPRIS 상표권 통합 조회 (API 키 유무에 따른 스마트 폴백 및 KIPRIS 공식 웹 직결)"""
    clean_q = query.strip()
    key = service_key or os.getenv(SERVICE_KEY_ENV_VAR)
    if key:
        try:
            return search_trademark_api(clean_q, key)
        except Exception:
            pass

    # API 키가 없거나 실패한 경우 KIPRIS 공식 웹 직결 URL 및 표준 안전도 리턴
    direct_url = build_kipris_web_url(clean_q)
    return TrademarkSearchResponse(
        query=clean_q,
        total_count=0,
        direct_kipris_url=direct_url,
        has_registered_trademark=False,
        risk_level="UNKNOWN_NEEDS_KIPRIS_DIRECT_CHECK",
        items=[],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="KIPRIS 공식 상표권 직접 조회 도구")
    parser.add_argument("--query", "-q", required=True, help="검색할 브랜드명 또는 상품 상표 키워드")
    parser.add_argument("--service-key", help=f"KIPRIS Plus ServiceKey (기본값: ${SERVICE_KEY_ENV_VAR})")
    parser.add_argument("--json", action="store_true", help="JSON 형태로 출력")
    args = parser.parse_args()

    res = search_trademark(args.query, args.service_key)
    if args.json:
        print(json.dumps(asdict(res), ensure_ascii=False, indent=2))
    else:
        print(f"=== KIPRIS 공식 상표권 조회 결과: '{res.query}' ===")
        print(f"• KIPRIS 공식 다이렉트 검색 링크: {res.direct_kipris_url}")
        print(f"• 상표 위험도 등급: {res.risk_level}")
        print(f"• 총 검색 건수: {res.total_count}건")
        if res.items:
            print("• 검색된 상표 목록:")
            for it in res.items:
                print(f"  - [{it.register_status}] {it.trademark_name} (출원인: {it.applicant_name}, 분류: {it.classification_code}류, 출원번호: {it.application_number})")
        else:
            print("  (KIPRIS 공식 웹사이트 다이렉트 링크를 클릭하여 최신 실시간 등록원부를 즉시 확인하십시오)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
