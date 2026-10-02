"""
네이버쇼핑 검색 API 공통 fetch 모듈.

전략 순서:
  1) curl_cffi (chrome TLS 위장) — 있으면 최우선
  2) requests
  3) insane-search engine (설치돼 있으면)

엔드포인트/파라미터는 네이버가 수시로 바꾸므로 후보를 순서대로 시도하고,
JSON 파싱 + 목표 키 존재 여부로 성공을 판정한다. (HTTP 200 = 성공 아님)
"""
import json
import os
import sys
import time
import shutil
from urllib.parse import quote

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")

BASE_HEADERS = {
    "User-Agent": UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
    "Referer": "https://search.shopping.naver.com/",
    "sec-ch-ua-platform": '"macOS"',
}

# 가격비교(cmp) 탭 계열 후보. 앞에서부터 시도.
ENDPOINT_CANDIDATES = [
    "https://search.shopping.naver.com/search/all?query={q}",
    "https://search.shopping.naver.com/api/search/all?eq=&query={q}&pagingIndex=1&pagingSize=40&productSet=total&sort=rel&viewType=list",
    "https://search.shopping.naver.com/api/search/all?query={q}&pagingIndex=1&pagingSize=40&productSet=model&sort=rel&viewType=list",
    "https://search.shopping.naver.com/api/search/allWithCatalog?query={q}&pagingIndex=1&pagingSize=40&productSet=total&sort=rel",
    "https://msearch.shopping.naver.com/api/search/all?query={q}&pagingIndex=1&pagingSize=40&productSet=total&sort=rel",
]


def _session():
    """쿠키 워밍된 세션 반환. curl_cffi 우선."""
    try:
        from curl_cffi import requests as creq
        s = creq.Session(impersonate="chrome124")
        s.headers.update(BASE_HEADERS)
        try:
            s.get("https://search.shopping.naver.com/", timeout=10)
        except Exception:
            pass
        return s, "curl_cffi"
    except ImportError:
        pass
    import requests as req
    s = req.Session()
    s.headers.update(BASE_HEADERS)
    try:
        s.get("https://search.shopping.naver.com/", timeout=10)
    except Exception:
        pass
    return s, "requests"


def deep_find(obj, key, _acc=None):
    """중첩 구조 어디에 있든 key에 해당하는 값을 전부 수집."""
    if _acc is None:
        _acc = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key:
                _acc.append(v)
            deep_find(v, key, _acc)
    elif isinstance(obj, list):
        for v in obj:
            deep_find(v, key, _acc)
    return _acc


def deep_find_dicts(obj, pred, _acc=None):
    """조건(pred)을 만족하는 dict를 전부 수집."""
    if _acc is None:
        _acc = []
    if isinstance(obj, dict):
        try:
            if pred(obj):
                _acc.append(obj)
        except Exception:
            pass
        for v in obj.values():
            deep_find_dicts(v, pred, _acc)
    elif isinstance(obj, list):
        for v in obj:
            deep_find_dicts(v, pred, _acc)
    return _acc


def _ensure_chrome_running(cdp_port=9222):
    """CDP 포트에 크롬이 안 켜져 있으면 전용 자동화 프로필로 크롬을 자동 실행한다."""
    import urllib.request, subprocess
    from pathlib import Path
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/version", timeout=1.2) as r:
            return True
    except Exception:
        pass

    # OS별 전용 프로필 경로
    if sys.platform == "win32":
        profile_dir = Path(os.path.expandvars(r"%LOCALAPPDATA%\GJC\Chrome Automation"))
        chrome_candidates = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        ]
    elif sys.platform == "darwin":
        profile_dir = Path(os.path.expanduser("~/Library/Application Support/GJC/Chrome Automation"))
        chrome_candidates = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:
        profile_dir = Path(os.path.expanduser("~/.config/gjc/chrome-automation"))
        chrome_candidates = ["google-chrome", "google-chrome-stable", "chromium-browser"]

    profile_dir.mkdir(parents=True, exist_ok=True)
    for exe in chrome_candidates:
        if os.path.exists(exe) or shutil.which(exe):
            cmd = [
                exe,
                f"--remote-debugging-port={cdp_port}",
                f"--user-data-dir={profile_dir}",
                "--profile-directory=Default",
                "about:blank",
            ]
            try:
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(2.5)
                return True
            except Exception:
                pass
    return False


def _fetch_via_browser_cdp(keyword, cdp_url="http://127.0.0.1:9222"):
    """로그인된 Chrome CDP 브라우저를 통해 실측 검색 JSON을 직접 추출한다."""
    _ensure_chrome_running(9222)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            url = f"https://search.shopping.naver.com/search/all?query={quote(keyword)}"
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)
            data = page.evaluate("() => JSON.parse(document.getElementById('__NEXT_DATA__')?.textContent || '{}')")
            return data
    except Exception:
        return None


def fetch_search_json(keyword, want_keys=("cmpOrg", "category1", "terms", "cmp"), dump_dir=None, verbose=True):
    """
    키워드 검색 결과 JSON을 가져온다.
    want_keys 중 하나라도 발견되면 성공으로 본다.
    반환: (data, meta) — 실패 시 (None, meta)
    """
    import re
    s, transport = _session()
    q = quote(keyword)
    tried = []
    for i, tmpl in enumerate(ENDPOINT_CANDIDATES):
        url = tmpl.format(q=q)
        try:
            r = s.get(url, timeout=15)
            status = r.status_code
            text = r.text
        except Exception as e:
            tried.append({"url": url, "error": repr(e)})
            continue
        rec = {"url": url, "status": status, "len": len(text)}
        data = None
        try:
            data = json.loads(text)
        except Exception:
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', text, re.DOTALL)
            if m:
                try:
                    data = json.loads(m.group(1))
                except Exception:
                    pass
        if data is None:
            rec["note"] = f"status {status} - not-json (HTML/차단 페이지 가능성)"
            tried.append(rec)
            time.sleep(0.8)
            continue
        hit = [k for k in want_keys if deep_find(data, k)]
        rec["keys_found"] = hit
        tried.append(rec)
        if hit:
            if dump_dir:
                os.makedirs(dump_dir, exist_ok=True)
                p = os.path.join(dump_dir, f"raw_{keyword}_{i}.json")
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                rec["dump"] = p
            return data, {"transport": transport, "tried": tried, "ok": True}
        time.sleep(0.8)

    # WAF 차단 시 활성화된 브라우저 CDP를 통해 즉시 추출 시도
    cdp_data = _fetch_via_browser_cdp(keyword)
    if cdp_data and any(deep_find(cdp_data, k) for k in want_keys):
        if dump_dir:
            os.makedirs(dump_dir, exist_ok=True)
            p = os.path.join(dump_dir, f"raw_{keyword}_cdp.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cdp_data, f, ensure_ascii=False, indent=2)
        return cdp_data, {"transport": "chrome_cdp", "tried": tried, "ok": True}

    if verbose:
        print("[FAIL] 목표 키를 가진 JSON을 못 받았습니다.", file=sys.stderr)
        for t in tried:
            print("  -", json.dumps(t, ensure_ascii=False)[:300], file=sys.stderr)
        print("\n→ insane-search engine 폴백을 시도하거나, 브라우저에서 실제 요청 URL을 확인해\n"
              "  ENDPOINT_CANDIDATES 맨 앞에 추가하세요 (보정 1회면 이후 계속 동작).", file=sys.stderr)
    return None, {"transport": transport, "tried": tried, "ok": False}
