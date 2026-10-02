#!/usr/bin/env python3
"""네이버 검색광고 공식 API 키워드도구로 키워드별 월간 PC/모바일 검색수·경쟁도 조회.

표준 라이브러리만 사용. 자격증명은 환경변수로만 읽고 파일·로그에 저장하지 않는다.

근거
  - 확장 분석: C:\\tmp\\nc\\extension.md §5-1 (메이커 셀링 도우미가 api.searchad.naver.com/keywordstool 을
    HMAC-SHA256 서명 헤더 X-Timestamp/X-API-KEY/X-Customer/X-Signature 로 호출)
  - 로컬 스킬: C:\\Users\\imda0\\.kiro\\skills\\naver-ad-performance\\SKILL.md (서명 방식·응답 필드)
  - 출력 호환: naver_title_builder.py 의 --search-volume 입력 = {"키워드": 월검색수(정수)} JSON

인증 (환경변수 3개 — 이 스크립트 전용 이름)
  NAVER_SEARCHAD_API_KEY       (X-API-KEY, access license)
  NAVER_SEARCHAD_SECRET        (HMAC secret key)
  NAVER_SEARCHAD_CUSTOMER_ID   (X-Customer)
  하나라도 없으면 {"available": false, "reason": ...} 를 출력하고 exit 0
  (파이프라인을 막지 않는다). 값은 절대 출력·저장하지 않는다.

서명 (naver-ad-performance 와 동일)
  message   = "{timestamp}.{method}.{uri_path}"   # 쿼리스트링 제외, method 대문자, uri = /keywordstool
  signature = base64(HMAC_SHA256(message, SECRET))

요청
  GET https://api.searchad.naver.com/keywordstool?hintKeywords=<최대5개 콤마결합>&showDetail=1
  키워드 5개씩 청크, 청크 사이 간격(기본 0.5s)을 둔다.

응답 파싱 (keywordList[])
  relKeyword           연관/입력 키워드
  monthlyPcQcCnt       월간 PC 조회수      (정수 또는 "< 10" 같은 문자열)
  monthlyMobileQcCnt   월간 모바일 조회수  (정수 또는 문자열)
  compIdx              경쟁정도(낮음/중간/높음 등)
  "< 10" 같은 문자열 검색수는 보수적으로 정수 근사(10)로 환산. total = pc + mobile.

출력 (stdout + --out)
  기본(--format volume, title_builder 호환):
      {"유산균": 500000, "질유산균": 90000, ...}          # {키워드: 월간총검색수(정수)}
  상세(--format detail):
      {"available": true, "keywords": [{relKeyword, monthlyPcQcCnt, monthlyMobileQcCnt,
        total, compIdx, pcApprox, mobileApprox}], "requested": [...], "chunks": N}
  자격증명/네트워크 미가용:
      {"available": false, "reason": "..."} (+ --format volume 이면 {} 는 아니고 위 객체 그대로)

사용
  python naver_searchad_volume.py --keywords "유산균,질유산균,다이어트유산균"
  python naver_searchad_volume.py --keywords-file kw.txt --format detail --out vol.json
  python naver_searchad_volume.py --check           # 환경변수 존재여부만(값 미출력)
  python naver_searchad_volume.py --selftest        # 서명·파싱·폴백 오프라인 검증
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Windows PowerShell cp949 콘솔에서 한글/em-dash 출력 크래시 방지 (naver_title_builder.py 와 동일)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_URL = "https://api.searchad.naver.com"
KEYWORDSTOOL_URI = "/keywordstool"

API_KEY_ENV = "NAVER_SEARCHAD_API_KEY"
SECRET_ENV = "NAVER_SEARCHAD_SECRET"
CUSTOMER_ID_ENV = "NAVER_SEARCHAD_CUSTOMER_ID"
ENV_NAMES = (API_KEY_ENV, SECRET_ENV, CUSTOMER_ID_ENV)

CHUNK_SIZE = 5
DEFAULT_TIMEOUT = 20
DEFAULT_INTERVAL = 0.5  # 청크 사이 간격(초)


def nfc(s) -> str:
    return unicodedata.normalize("NFC", str(s or "")).strip()


# ---------------------------------------------------------------- 자격증명 (값 미노출)

def resolve_credentials():
    """환경변수에서 자격증명을 읽는다. 값은 반환만 하고 로그·파일에 남기지 않는다.

    반환: (creds_or_None, missing_names)
      모두 있으면 (dict, [])
      하나라도 없으면 (None, [빠진 환경변수 이름...])
    """
    values = {name: os.getenv(name) for name in ENV_NAMES}
    missing = [name for name, val in values.items() if not val]
    if missing:
        return None, missing
    return {
        "api_key": values[API_KEY_ENV],
        "secret": values[SECRET_ENV],
        "customer_id": values[CUSTOMER_ID_ENV],
    }, []


def env_presence():
    """환경변수 '존재 여부'만 (값은 절대 포함하지 않음)."""
    return {name: bool(os.getenv(name)) for name in ENV_NAMES}


# ---------------------------------------------------------------- 서명

def build_signature(secret: str, timestamp: str, method: str, uri: str) -> str:
    """message = '{timestamp}.{METHOD}.{uri_path}', signature = base64(HMAC_SHA256(message, secret))."""
    message = f"{timestamp}.{method.upper()}.{uri}".encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.b64encode(digest).decode("utf-8")


def build_headers(creds: dict, timestamp: str, method: str, uri: str) -> dict:
    return {
        "X-Timestamp": timestamp,
        "X-API-KEY": creds["api_key"],
        "X-Customer": str(creds["customer_id"]),
        "X-Signature": build_signature(creds["secret"], timestamp, method, uri),
        "Accept": "application/json",
    }


# ---------------------------------------------------------------- 응답 파싱

def parse_count(value):
    """검색수 셀을 정수로 환산. '< 10' / '<10' / '1,234' / 숫자 문자열 / None 처리.

    반환: (approx_int, was_approx)
      '< 10' → (10, True) : 상한을 보수적으로 근사값으로 사용
      '1,234' → (1234, False)
      None/'' → (0, False)
    """
    if value is None:
        return 0, False
    if isinstance(value, (int, float)):
        return int(value), False
    s = nfc(value)
    if not s:
        return 0, False
    # '< 10', '<10', '＜10' 형태
    m = re.search(r"[<＜]\s*([\d,]+)", s)
    if m:
        return int(m.group(1).replace(",", "")), True
    # 순수 숫자(콤마 허용)
    digits = re.sub(r"[^\d]", "", s)
    if digits:
        return int(digits), False
    return 0, False


def parse_keywordtool_response(body: str) -> list:
    """keywordstool 응답 JSON 문자열 → 정규화된 행 리스트."""
    try:
        data = json.loads(body)
    except (ValueError, TypeError):
        return []
    rows = []
    kw_list = []
    if isinstance(data, dict):
        kw_list = data.get("keywordList") or data.get("keywords") or []
    elif isinstance(data, list):
        kw_list = data
    for item in kw_list:
        if not isinstance(item, dict):
            continue
        rel = nfc(item.get("relKeyword") or item.get("keyword") or "")
        pc, pc_approx = parse_count(item.get("monthlyPcQcCnt"))
        mob, mob_approx = parse_count(item.get("monthlyMobileQcCnt"))
        rows.append({
            "relKeyword": rel,
            "monthlyPcQcCnt": item.get("monthlyPcQcCnt"),
            "monthlyMobileQcCnt": item.get("monthlyMobileQcCnt"),
            "pcApprox": pc,
            "mobileApprox": mob,
            "total": pc + mob,
            "wasApprox": bool(pc_approx or mob_approx),
            "compIdx": nfc(item.get("compIdx")) if item.get("compIdx") is not None else None,
            "plAvgDepth": item.get("plAvgDepth"),
        })
    return rows


# ---------------------------------------------------------------- HTTP

def _chunks(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def fetch_keyword_volume(keywords, creds, *, interval=DEFAULT_INTERVAL,
                         timeout=DEFAULT_TIMEOUT, opener=None):
    """키워드 리스트를 5개씩 청크로 keywordstool 호출. 정규화된 행 리스트 반환.

    opener: 테스트용 주입. (headers, url) -> 응답 본문 문자열. None 이면 실제 HTTP.
    실제 HTTP 는 creds 가 있을 때만 호출된다(호출부 책임).
    """
    hint = [nfc(k) for k in keywords if nfc(k)]
    # 입력 순서 유지하며 중복 제거
    hint = list(dict.fromkeys(hint))
    all_rows = []
    chunk_count = 0
    for idx, chunk in enumerate(_chunks(hint, CHUNK_SIZE)):
        if idx > 0 and interval:
            time.sleep(interval)  # 청크 사이 간격
        chunk_count += 1
        params = {"hintKeywords": ",".join(chunk), "showDetail": "1"}
        query = urllib.parse.urlencode(params)
        url = f"{BASE_URL}{KEYWORDSTOOL_URI}?{query}"
        timestamp = str(round(time.time() * 1000))
        headers = build_headers(creds, timestamp, "GET", KEYWORDSTOOL_URI)
        if opener is not None:
            body = opener(headers, url)
        else:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        all_rows.extend(parse_keywordtool_response(body))
    return all_rows, chunk_count


# ---------------------------------------------------------------- 출력 형태

def rows_to_volume_map(rows, requested=None):
    """title_builder --search-volume 호환: {키워드: 월간총검색수(정수)}.

    requested 가 주어지면 요청 키워드에 해당하는 행을 우선 매핑(연관키워드 잡음 축소).
    같은 키워드가 여러 번이면 total 최댓값 사용.
    """
    vol = {}
    for r in rows:
        kw = nfc(r.get("relKeyword"))
        if not kw:
            continue
        total = int(r.get("total") or 0)
        if kw not in vol or total > vol[kw]:
            vol[kw] = total
    if requested:
        req_c = {nfc(k): None for k in requested}
        # 요청 키워드(정확히 일치)만 우선 노출하되, 없으면 전체 유지
        exact = {k: v for k, v in vol.items() if k in req_c}
        if exact:
            return exact
    return vol


def build_detail(rows, requested, chunk_count):
    return {
        "available": True,
        "requested": [nfc(k) for k in requested],
        "chunks": chunk_count,
        "keywords": rows,
        "note": "월간 총검색수 total = PC + 모바일. '< 10' 등 문자열 검색수는 근사(wasApprox=true).",
    }


def unavailable(reason, missing=None):
    out = {"available": False, "reason": reason}
    if missing:
        # 값이 아니라 '빠진 환경변수 이름'만 노출
        out["missingEnv"] = missing
    return out


# ---------------------------------------------------------------- 실행 파이프라인

def run(keywords, *, fmt="volume", interval=DEFAULT_INTERVAL, timeout=DEFAULT_TIMEOUT):
    """실제 실행 진입점. 자격증명 없으면 폴백, 있으면 실제 호출."""
    keywords = [nfc(k) for k in keywords if nfc(k)]
    if not keywords:
        return unavailable("조회할 키워드가 없습니다(--keywords 또는 --keywords-file 필요).")

    creds, missing = resolve_credentials()
    if creds is None:
        return unavailable(
            "네이버 검색광고 API 자격증명 환경변수가 없어 검색량을 건너뜁니다. "
            "설정: " + ", ".join(ENV_NAMES) + " (값은 파일에 저장하지 마세요). "
            "검색량 없이도 title_builder 는 terms 근거로 동작합니다.",
            missing=missing,
        )

    try:
        rows, chunk_count = fetch_keyword_volume(
            keywords, creds, interval=interval, timeout=timeout)
    except urllib.error.HTTPError as exc:
        body = ""
        try:
            body = exc.read().decode("utf-8", errors="replace")[:200]
        except Exception:
            pass
        return unavailable(f"네이버 API HTTP {exc.code}: {body}".strip())
    except urllib.error.URLError as exc:
        return unavailable(f"네이버 API 도달 불가(egress): {exc.reason}")
    except Exception as exc:  # 파이프라인을 막지 않는다
        return unavailable(f"검색량 조회 실패: {type(exc).__name__}: {exc}")

    if fmt == "detail":
        return build_detail(rows, keywords, chunk_count)
    return rows_to_volume_map(rows, requested=keywords)


# ---------------------------------------------------------------- selftest (오프라인)

def selftest():
    """서명 생성·응답 파싱·폴백을 실제 API 없이 검증."""
    # 1) 서명: 알려진 입력 → 예상 서명 계산 방식(독립 재현)과 일치
    secret = "test-secret-key"
    ts = "1700000000000"
    sig = build_signature(secret, ts, "GET", KEYWORDSTOOL_URI)
    expected = base64.b64encode(
        hmac.new(secret.encode("utf-8"),
                 f"{ts}.GET.{KEYWORDSTOOL_URI}".encode("utf-8"),
                 hashlib.sha256).digest()).decode("utf-8")
    assert sig == expected, (sig, expected)
    # method 소문자 입력도 대문자로 서명해야 함
    assert build_signature(secret, ts, "get", KEYWORDSTOOL_URI) == expected
    # 헤더 4종 존재 + 시크릿 값이 헤더에 노출되지 않음
    creds = {"api_key": "AK", "secret": secret, "customer_id": "123"}
    hdr = build_headers(creds, ts, "GET", KEYWORDSTOOL_URI)
    assert set(["X-Timestamp", "X-API-KEY", "X-Customer", "X-Signature"]).issubset(hdr)
    assert secret not in json.dumps(hdr)  # 서명만 나가고 시크릿 원문은 안 나감
    assert hdr["X-Signature"] == expected

    # 2) parse_count: '< 10' 문자열 처리
    assert parse_count("< 10") == (10, True)
    assert parse_count("<10") == (10, True)
    assert parse_count("1,234") == (1234, False)
    assert parse_count(560) == (560, False)
    assert parse_count(None) == (0, False)
    assert parse_count("") == (0, False)

    # 3) 응답 파싱: 샘플 fixture ('< 10' 포함)
    sample = json.dumps({"keywordList": [
        {"relKeyword": "유산균", "monthlyPcQcCnt": 120000, "monthlyMobileQcCnt": 380000, "compIdx": "높음"},
        {"relKeyword": "질유산균", "monthlyPcQcCnt": "18,000", "monthlyMobileQcCnt": "72,000", "compIdx": "중간"},
        {"relKeyword": "희귀키워드", "monthlyPcQcCnt": "< 10", "monthlyMobileQcCnt": "< 10", "compIdx": "낮음"},
    ]})
    rows = parse_keywordtool_response(sample)
    by = {r["relKeyword"]: r for r in rows}
    assert by["유산균"]["total"] == 500000, by["유산균"]
    assert by["질유산균"]["total"] == 90000, by["질유산균"]
    assert by["희귀키워드"]["total"] == 20 and by["희귀키워드"]["wasApprox"], by["희귀키워드"]

    # 4) volume 맵: title_builder --search-volume 호환 (정수 값)
    vmap = rows_to_volume_map(rows, requested=["유산균", "질유산균", "희귀키워드"])
    assert vmap == {"유산균": 500000, "질유산균": 90000, "희귀키워드": 20}, vmap
    assert all(isinstance(v, int) for v in vmap.values())

    # 5) 청크 5개 + opener 주입으로 fetch 흐름 검증(실제 네트워크 없음)
    calls = []

    def fake_opener(headers, url):
        calls.append((headers, url))
        assert "X-Signature" in headers
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        kws = qs["hintKeywords"][0].split(",")
        assert len(kws) <= CHUNK_SIZE
        return json.dumps({"keywordList": [
            {"relKeyword": k, "monthlyPcQcCnt": 100, "monthlyMobileQcCnt": 200, "compIdx": "낮음"}
            for k in kws]})

    seven = [f"kw{i}" for i in range(7)]
    rows2, chunks2 = fetch_keyword_volume(seven, creds, interval=0, opener=fake_opener)
    assert chunks2 == 2, chunks2  # 7개 → 5+2 = 2청크
    assert len(rows2) == 7, len(rows2)
    assert len(calls) == 2

    # 6) 폴백: 자격증명 없을 때 available:false + exit 0 계약
    saved = {n: os.environ.pop(n, None) for n in ENV_NAMES}
    try:
        res = run(["유산균"])
        assert res["available"] is False, res
        assert "reason" in res and res.get("missingEnv"), res
    finally:
        for n, v in saved.items():
            if v is not None:
                os.environ[n] = v

    print(json.dumps({"selftest": "PASS",
                      "sample_volume": vmap,
                      "chunks_for_7_keywords": chunks2}, ensure_ascii=False))


# ---------------------------------------------------------------- CLI

def _load_keywords_file(path: Path):
    text = path.read_text(encoding="utf-8")
    return [k for k in re.split(r"[\r\n,]+", text) if k.strip()]


def main():
    ap = argparse.ArgumentParser(description="네이버 검색광고 keywordstool 월간 검색수 조회")
    ap.add_argument("--keywords", default="", help="콤마로 구분한 키워드")
    ap.add_argument("--keywords-file", help="키워드 파일(줄/콤마 구분)")
    ap.add_argument("--format", choices=["volume", "detail"], default="volume",
                    help="volume: title_builder 호환 {키워드:검색수}, detail: 전체 필드")
    ap.add_argument("--interval", type=float, default=DEFAULT_INTERVAL, help="청크 사이 간격(초)")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    ap.add_argument("--out", help="결과 JSON 저장 경로(UTF-8)")
    ap.add_argument("--check", action="store_true", help="환경변수 존재여부만 출력(값 미출력)")
    ap.add_argument("--selftest", action="store_true", help="오프라인 서명·파싱·폴백 검증")
    a = ap.parse_args()

    if a.selftest:
        selftest()
        return 0

    if a.check:
        # 값이 아니라 존재 여부만
        print(json.dumps({"envPresent": env_presence(), "allSet": all(env_presence().values())},
                         ensure_ascii=False))
        return 0

    keywords = [k.strip() for k in a.keywords.split(",") if k.strip()]
    if a.keywords_file and Path(a.keywords_file).exists():
        keywords += _load_keywords_file(Path(a.keywords_file))
    keywords = list(dict.fromkeys(keywords))

    res = run(keywords, fmt=a.format, interval=a.interval, timeout=a.timeout)
    text = json.dumps(res, ensure_ascii=False, indent=2 if a.format == "detail" else None)
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    # 계약: 자격증명/네트워크 미가용이어도 파이프라인을 막지 않도록 exit 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
