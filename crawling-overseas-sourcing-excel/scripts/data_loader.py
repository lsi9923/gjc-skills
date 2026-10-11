#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v4.0 Data Loader & True Store Link Resolver (data_loader.py)
- Joins ideas.sqlite (2,392 durable items, rescored to 786+ Korean physical products),
  ideas.json, cycle_ideas.json, catalog_ideas.json, raw_items.jsonl, and coupang_product_cache.json.
- Resolves true store URLs from purchase_urls[], purchase_evidence[].resolver.final_url,
  resolved_purchase_url, and commerce_url.
- Joins root Threads/Instagram posts (holding media_urls) with sibling reply posts
  (holding '<Product> - <Category>' title) by commerce_url / root_post_url.
- Extracts cached Coupang, Naver SmartStore, and Toss Shopping prices.
"""
import json
import re
import sqlite3
import urllib.parse
from pathlib import Path

DEFAULT_RADAR_ROOT = Path(r"C:\Users\imda0\AppData\Local\ProductIdeaRadar")
DEFAULT_INPUT_DIR = DEFAULT_RADAR_ROOT / "runs" / "latest"
DEFAULT_DATA_DIR = DEFAULT_RADAR_ROOT / "data"
DEFAULT_OUT_PATH = Path(r"C:\Users\imda0\Desktop\해외구매대행_사입_추천상품_TOP50.xlsx")

EXCLUDE_PATTERNS = [
    r"월급만으로 부족", r"부업 \d+가지", r"왕초보 전용 자동화", r"무자본 창업",
    r"스마트스토어는 만들었는데", r"키워드북 공유", r"몸빵.*시스템",
    r"초보 셀러 마켓 포지셔닝", r"월 순수익", r"7일 압축 코스", r"방구석 온라인 창업",
    r"해외구매대행\s*실무", r"중국 사입에 여전히 적응이", r"도용 당해서 테무에",
    r"올바로 직구 수비대", r"할인 쿠폰 이벤트", r"일본 할인 쿠폰 모음",
    r"중국 제품\? 싸고 금방 고장", r"신규회원 알뜰마트 혜택", r"1\+2 대박 혜택",
    r"이번주 알리익스프레스 털어야", r"이번주 알리 당장 털러", r"알리 MD들이 직접 PICK",
    r"알리익스프레스 MD가 직접 엄선한", r"알리익스프레스\s*\d+\s*세일",
    r"쿠팡 구매대행,\s*컴맹도", r"사업자등록 준비", r"SHEIN이 유해물질",
    r"방탄소년단\(BTS\)", r"천원빵.*보존료", r"발명 끝말잇기 챌린지",
    r"샤넬|에르메스|루이비통|구찌|디올|프라다|롤렉스|헬로키티|키티|짱구|산리오|포켓몬|디즈니|폼폼푸린|미니언즈|패트릭 스타",
    r"\(냉동\)|얼큰 쭈꾸미|뚝배기불고기|구구 크러스터|아이스크림|밀키트|김치|삼겹살|한우|곱창|막창|닭갈비|떡볶이|과일 씻기",
    r"화이트소스|스테이크/바베큐소스|파운드.*혼합세트|츄러스 초코|목캔디|핑거별 양파|강아지 덴탈껌",
    r"홍로사과|세척사과|푸룬\s*자두|새송이\s*버섯|통오징어|훈제\s*연어|생새우살|프라임\s*등심|LA갈비|소갈비|잠봉",
    r"그릴스모크햄|비엔나\s*소시지|동그랑땡|바사삭닭다리|에어프라이어\s*치킨|갈비탕|깜빠뉴|숙식빵|바나나빵|버거번|버터롤",
    r"크림\s*치즈|모짜렐라|자연치즈|요거트|밀크\s*푸딩|감자칩|포테이토칩|초콜릿|초콜렛|쿠키|쿠크다스|에이스\s*과자|브이콘|포키",
    r"곤약젤리|구미\s*클리스터|커피캔디|커피믹스|스페셜\s*블랜드|에스프레소\s*블렌드|인스턴트커피|말차\s*파우더|미숫가루|검은콩가루",
    r"현미튀밥|치아씨드|전분믹스|바사삭치킨파우더|샘표\s*토장|스테비아|소불고기양념|굴소스|유즈코쇼|바질페스토|토마토\s*퓨레",
    r"참치액|어간장|멸치액젓|매실청|치킨스톡|핑크솔트|알룰로스|미고랭|햄통조림|곱창김|김치전스낵|코카콜라|삼다수|국산생수|탐사\s*샘물",
    r"샐러리주스|호박팥차|자스민\s*티|꽃송이버섯효소|강아지\s*건강사료",
    r"백화점발송|백화점정품|설화수|입생로랑|산타마리아노벨라|이솝|맥\s*러스터글래스|라부르켓|러쉬|자라\s*오드\s*퍼퓸|네블라이저",
    r"재팬딜리버리.*메루카리", r"지하철에 공유", r"로보락 한가위빅세일", r"공구예고",
    r"자취생의 주방템 모음집", r"2년차 신혼부부의 주방템", r"항상 사용하고 있는 조리 도구",
    r"JPFans", r"초간단 싱크대 배수구 청소법", r"데스크테리어|인테리어 소개",
    r"말랑이 천원대에", r"요즘 쿠팡 판매자라면 눈여겨볼 상품", r"타칭 테무 앰버서더",
    r"좁은 주방 넓게 쓰는 꿀템 BEST", r"취향별 키보드 추천 BEST", r"자기관리에 진심인 40대언니",
    r"친정엄마 가게 매출 살린 꿀팁", r"집 꾸며도 무조건 살 주방템 3가지", r"새 주방 채우면서.*6개 골랐어요",
    r"아마존프라임데이", r"광저우 의류시장투어", r"그랜드 세일 총정리", r"뉴욕 직구 소량 배송",
    r"입장권", r"드로잉 무작정따라하기", r"한복세트", r"암꽃게", r"삼각살", r"와사비나", r"로즈마리", r"만두피",
]
EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)


def _values(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return [x for x in value if isinstance(x, str)]
    return []


def _valid_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    try:
        p = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    if p.scheme not in {"http", "https"} or not p.hostname:
        return None
    host = p.hostname.lower().rstrip(".")
    if any(host == d or host.endswith("." + d) for d in (
        "instagram.com", "threads.net", "threads.com", "youtube.com",
        "youtu.be", "forms.gle", "docs.google.com", "blogspot.com",
        "blog.naver.com", "jpfans.com", "style-q.com", "kekewo.net"
    )):
        return None
    if host == "coupang.com":
        value = "https://www.coupang.com" + (p.path or "/") + (("?" + p.query) if p.query else "")
    return value


def load_coupang_cache() -> dict:
    cp_file = DEFAULT_DATA_DIR / "coupang_product_cache.json"
    if cp_file.exists():
        try:
            return json.loads(cp_file.read_text(encoding="utf-8")).get("products") or {}
        except Exception:
            pass
    return {}


def extract_coupang_pid(text_or_url: str) -> str | None:
    m = re.search(r"products/(\d+)", text_or_url or "")
    return m.group(1) if m else None


def collect_dirs(inputs) -> list[Path]:
    dirs = []
    for p in (inputs or []):
        path = Path(p)
        if path.is_dir():
            if path not in dirs:
                dirs.append(path)
        elif path.exists():
            if path.parent not in dirs:
                dirs.append(path.parent)
    if not dirs and DEFAULT_INPUT_DIR.exists():
        dirs.append(DEFAULT_INPUT_DIR)
    return dirs


def load_sqlite_entries() -> list[dict]:
    db_path = DEFAULT_DATA_DIR / "ideas.sqlite"
    entries = []
    if not db_path.exists():
        return entries
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # Load all product ideas (is_product_idea=1) plus any item with strong market score or store link
        q = """
        SELECT r.id, r.source, r.platform, r.url, r.title, r.text, r.author, r.published_at,
               r.media_json, r.metrics_json, r.tags_json, r.raw_json, r.fetched_at,
               s.category, s.summary_ko, s.novelty_score, s.virality_score, s.market_score,
               s.total_score, s.duplicate_key, s.reason, s.is_product_idea
        FROM raw_items r
        JOIN scored_ideas s ON r.id = s.item_id
        WHERE s.is_product_idea = 1 OR s.total_score >= 4.8 OR r.raw_json LIKE '%coupang_product%'
        """
        for row in cur.execute(q).fetchall():
            (
                item_id, source, platform, url, title, text, author, pub_at,
                media_j, metrics_j, tags_j, raw_j, fetched_at,
                cat, summary_ko, nov, vir, mkt, tot, dup_key, reason, is_prod
            ) = row
            try:
                media_urls = json.loads(media_j) if media_j else []
            except Exception:
                media_urls = []
            try:
                metrics = json.loads(metrics_j) if metrics_j else {}
            except Exception:
                metrics = {}
            try:
                raw = json.loads(raw_j) if raw_j else {}
            except Exception:
                raw = {}
            entries.append({
                "item": {
                    "id": item_id,
                    "source": source,
                    "platform": platform,
                    "url": url,
                    "title": title,
                    "text": text,
                    "author": author,
                    "published_at": pub_at,
                    "media_urls": media_urls,
                    "metrics": metrics,
                    "raw": raw,
                    "fetched_at": fetched_at,
                },
                "category": cat,
                "summary_ko": summary_ko,
                "novelty_score": nov,
                "virality_score": vir,
                "market_score": mkt,
                "total_score": tot,
                "duplicate_key": dup_key,
                "reason": reason,
                "is_product_idea": bool(is_prod),
            })
        conn.close()
    except Exception:
        pass
    return entries


def resolve_true_store_url(raw: dict, cp_cache: dict) -> tuple[str | None, int, dict]:
    """
    Returns (best_store_url, link_tier, cp_info)
    Priority order:
      1. raw.purchase_urls[] and raw.purchase_evidence[].resolver.final_url
      2. raw.resolved_purchase_url
      3. raw.commerce_url
    """
    p_urls = [_valid_url(u) for u in _values(raw.get("purchase_urls"))]
    p_urls = [u for u in p_urls if u]
    final_urls, raw_urls = [], []
    for pe in (raw.get("purchase_evidence") or []):
        if isinstance(pe, dict):
            fin = _valid_url((pe.get("resolver") or {}).get("final_url"))
            raw_u = _valid_url(pe.get("raw_url"))
            if fin:
                final_urls.append(fin)
            if raw_u:
                raw_urls.append(raw_u)

    resolved_u = _valid_url(raw.get("resolved_purchase_url"))
    commerce_u = _valid_url(raw.get("commerce_url"))

    candidates = p_urls + final_urls + raw_urls + [resolved_u, commerce_u]
    candidates = [u for u in candidates if u]
    best_url = candidates[0] if candidates else None

    cp_info = dict(raw.get("coupang_product") or {})
    pid = extract_coupang_pid(best_url or "")
    if pid and pid in cp_cache:
        cached = cp_cache[pid]
        if cached.get("matched") and cached.get("official_product_name"):
            cp_info = dict(cached)
        elif not cp_info.get("official_product_name") and cached.get("query"):
            cp_info.setdefault("query", cached.get("query"))

    # Also check naver_product if present
    nv_info = raw.get("naver_product")
    if isinstance(nv_info, dict) and nv_info.get("matched") and nv_info.get("price") and not cp_info.get("price"):
        cp_info["price"] = nv_info.get("price")
        cp_info["price_source"] = "naver_smartstore"
        if nv_info.get("title") and not cp_info.get("official_product_name"):
            cp_info["official_product_name"] = nv_info.get("title")

    link_tier = 3
    if best_url:
        if cp_info.get("matched") and cp_info.get("price"):
            link_tier = 1
        elif any(d in best_url.lower() for d in ["amazon.com/", "aliexpress.com/item/", "www.coupang.com/vp/products/", "toss.shopping/", "smartstore.naver.com/"]):
            link_tier = 1 if cp_info.get("price") else 2
        else:
            link_tier = 2

    return best_url, link_tier, cp_info


def load_and_merge_candidates(input_paths=None) -> list[dict]:
    dirs = collect_dirs(input_paths)
    cp_cache = load_coupang_cache()
    img_by_url = {}
    sibling_title_by_commerce = {}
    all_entries = []

    for d in dirs:
        for jname in ["cycle_ideas.json", "ideas.json", "catalog_ideas.json"]:
            jpath = d / jname
            if jpath.exists():
                try:
                    data = json.loads(jpath.read_text(encoding="utf-8"))
                    all_entries.extend(data)
                except Exception:
                    pass

        raw_jsonl = d / "raw_items.jsonl"
        if raw_jsonl.exists():
            try:
                with open(raw_jsonl, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        item = json.loads(line)
                        raw = item.get("raw") or {}
                        media = [u for u in (item.get("media_urls") or []) if u]
                        prod_img = raw.get("product_image") or (media[0] if media else "")
                        if prod_img and item.get("url"):
                            img_by_url[item["url"].rstrip("/")] = (prod_img, media)
            except Exception:
                pass

    all_entries.extend(load_sqlite_entries())

    # Pass 1: Index media by post URL / root_post_url and sibling link-card titles by commerce_url
    for entry in all_entries:
        item = entry.get("item") or {}
        raw = item.get("raw") or {}
        media = [u for u in (item.get("media_urls") or []) if u]
        prod_img = raw.get("product_image") or (media[0] if media else "")
        u = (item.get("url") or "").rstrip("/")
        orig_u = (raw.get("original_post_url") or "").rstrip("/")
        root_u = ((raw.get("provenance") or {}).get("root_post_url") or "").rstrip("/")
        c_url = (raw.get("commerce_url") or "").strip()

        if prod_img:
            if u:
                img_by_url[u] = (prod_img, media)
            if orig_u:
                img_by_url[orig_u] = (prod_img, media)
            if root_u:
                img_by_url[root_u] = (prod_img, media)
            if c_url:
                img_by_url[f"commerce:{c_url}"] = (prod_img, media)

        t_str = (item.get("title") or "").strip()
        if c_url and " - " in t_str and 6 <= len(t_str) <= 95:
            sibling_title_by_commerce[c_url] = t_str

    # Pass 2: Build merged candidate records
    candidates = []
    for entry in all_entries:
        item = entry.get("item") or {}
        raw = item.get("raw") or {}
        url = (item.get("url") or "").strip()
        c_url = (raw.get("commerce_url") or "").strip()
        root_u = ((raw.get("provenance") or {}).get("root_post_url") or "").rstrip("/")

        media = [u for u in (item.get("media_urls") or []) if u]
        prod_img = raw.get("product_image") or (media[0] if media else "")
        if not prod_img:
            for lookup_k in [url.rstrip("/"), root_u, f"commerce:{c_url}"]:
                if lookup_k and lookup_k in img_by_url:
                    prod_img, media = img_by_url[lookup_k]
                    break
        if not prod_img:
            continue

        cat = (entry.get("category") or "general").strip()
        if cat == "ai_software":
            continue

        title = (item.get("title") or "").strip()
        text = (item.get("text") or "").strip()
        summary_ko = (entry.get("summary_ko") or "").strip()
        sibling_title = sibling_title_by_commerce.get(c_url, "")

        full_text = f"{title} {text} {summary_ko} {sibling_title}"
        if EXCLUDE_RE.search(full_text):
            continue

        store_url, link_tier, cp_info = resolve_true_store_url(raw, cp_cache)

        # Parse Toss Shopping or caption price if present in text
        m_price = re.search(r"(?:쿠폰\s*할인가|판매가|가격\s*:?)\s*([\d,]{4,9})\s*원", full_text)
        if m_price:
            price_digits = (m_price.group(1) or "").replace(",", "")
            if price_digits.isdigit() and 1500 <= int(price_digits) <= 2000000:
                if not cp_info.get("price"):
                    cp_info["price"] = int(price_digits)
                    cp_info["price_source"] = "caption_verified"

        candidates.append({
            "entry": entry,
            "item": item,
            "raw": raw,
            "url": url,
            "prod_img": prod_img,
            "media": media,
            "cat": cat,
            "title": title,
            "text": text,
            "summary_ko": summary_ko,
            "sibling_title": sibling_title,
            "full_text": full_text,
            "store_url": store_url,
            "link_tier": link_tier,
            "cp_info": cp_info,
        })

    # Deterministic identity collapse before scoring
    dedup = {}
    for cand in candidates:
        pid = extract_coupang_pid(cand.get("store_url") or "")
        key = (
            (cand["entry"].get("duplicate_key") or "").strip()
            or (f"coupang:{pid}" if pid else "")
            or (cand.get("store_url") or "").split("?", 1)[0].lower()
            or re.sub(r"\W+", "", cand.get("sibling_title") or cand.get("title") or "").casefold()
        )
        if not key:
            continue
        old = dedup.get(key)
        quality = (
            int(bool(cand.get("store_url"))) * 3
            + int(bool(cand.get("cp_info", {}).get("price"))) * 2
            + int(bool(cand.get("prod_img")))
            + float(cand["entry"].get("total_score") or 0) / 100
        )
        if old is None or quality > old[0]:
            dedup[key] = (quality, cand)
    return [v[1] for v in dedup.values()]
