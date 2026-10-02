#!/usr/bin/env python3
"""상세페이지 메이커 완료폴더 1개 → 네이버/쿠팡 등록 계획(registration_plan.json) 생성.

- 메이커 산출물(1~5.png, detail_page.png, sections/*.png, source.json, metadata.json,
  copy_manifest.json, result.md)을 읽어 사실값만 추출한다. 값을 지어내지 않는다.
- 업로드용 이미지를 Aside 세션 폴더(--out) 안으로 ASCII 파일명으로 복사한다.
  (Aside 브라우저 setFiles 는 세션 디렉터리 밖 경로를 거부한다.)
- 마켓별 이미지 규격을 검사하고, 사람이 정해야 할 값은 needsUser 로 남긴다.

사용
  python prepare_product.py <완료폴더\\N 또는 N> --out <세션 tmp 폴더> [--cost-krw 5000 | --cost-cny 20]
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import struct
import sys
from datetime import datetime
from pathlib import Path

# Windows PowerShell(cp949) 콘솔에서 한글/em-dash 출력 시 UnicodeEncodeError 크래시 방지 (audit A1/A2)
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass

SKILL_DIR = Path(__file__).resolve().parent.parent
PROFILE = json.loads((SKILL_DIR / "config" / "seller_profile.json").read_text(encoding="utf-8"))

SITE_SUFFIX = re.compile(r"\s*\|\s*[^|]{1,15}$")  # " | 쿠팡", " | 토스쇼핑" 등 사이트명 꼬리
BLOCK_MARKERS = ("사용권한이 없습니다", "사용권한이 제한", "Access Denied", "로봇이 아닙니다", "captcha")

# A3: 옵션값(색상·수량·규격 선택) 판별 — 상품명/고시 품명에서 제거할 세그먼트
OPTION_VALUE = re.compile(
    r"(^\d+\s*(개|매|장|팩|세트|입|병|캔|포|묶음|박스|p|pcs?)$"
    r"|화이트|블랙|그레이|그레이지|아이보리|베이지|네이비|카키|브라운|레드|블루|그린|핑크|퍼플|옐로우"
    r"|웜그레이|민트|라벤더|버건디|와인|카멜|크림|실버|골드|로즈골드"
    r"|흰색|검정|검은색|회색|남색|빨강|파랑|초록|분홍|보라|노랑|주황|갈색|하늘색"
    r"|색상\s*(랜덤|선택)?|랜덤|택1|옵션\s*\d*|사이즈\s*(선택)?|[SML]사이즈)",
    re.IGNORECASE,
)
# 색상 쿠팡 표준명 정규화 (근거 있는 소량 매핑 — 색상 표준명은 사실. legacy coupang_category_matcher 개념 이식)
COUPANG_COLOR = {
    "흰색": "화이트", "하양": "화이트", "white": "화이트",
    "검정": "블랙", "검은색": "블랙", "블랙색": "블랙", "black": "블랙",
    "회색": "그레이", "그레이색": "그레이", "gray": "그레이", "grey": "그레이",
    "남색": "네이비", "navy": "네이비", "빨강": "레드", "빨간색": "레드", "red": "레드",
    "파랑": "블루", "파란색": "블루", "blue": "블루", "초록": "그린", "녹색": "그린", "green": "그린",
    "분홍": "핑크", "pink": "핑크", "보라": "퍼플", "purple": "퍼플", "노랑": "옐로우", "yellow": "옐로우",
}


def normalize_coupang_color(word: str) -> str:
    """색상 단어를 쿠팡 표준 색상명으로. 매핑 없으면 원문 유지(추측 금지)."""
    return COUPANG_COLOR.get(nfc_lower(word), word)


def nfc_lower(s: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFC", str(s or "")).strip().lower()


def source_blocked(title: str, text: str) -> bool:
    t = (title or "").strip()
    if t in ("", "쿠팡!", "쿠팡", "Coupang") or t.startswith("Loading ") or t.startswith("http"):
        return True
    return any(m.lower() in (text or "")[:600].lower() for m in BLOCK_MARKERS)


def png_size(p: Path):
    with open(p, "rb") as fh:
        head = fh.read(26)
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", head[16:24])
    if head[:2] == b"\xff\xd8":  # JPEG: 스캔
        data = p.read_bytes()
        i = 2
        while i < len(data):
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            seg = struct.unpack(">H", data[i + 2:i + 4])[0]
            i += 2 + seg
    return None


def load_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def product_id_from_url(url: str):
    m = re.search(r"/vp/products/(\d+)", url or "")
    if m:
        return ("coupang", m.group(1))
    m = re.search(r"toss\.shopping/t/(\d+)", url or "")
    if m:
        return ("toss", m.group(1))
    m = re.search(r"[?&]id=(\d+)", url or "") or re.search(r"offer/(\d+)", url or "")
    if m:
        return ("1688/tmall", m.group(1))
    m = re.search(r"/products/(\d+)", url or "")
    return ("naver", m.group(1)) if m else (None, None)


def parse_facts(facts):
    """'키\t값\t키\t값' 형태의 고시 행을 dict 로."""
    out = {}
    for row in facts or []:
        cells = [c.strip() for c in str(row).split("\t")]
        if len(cells) >= 2 and len(cells) % 2 == 0:
            for k, val in zip(cells[0::2], cells[1::2]):
                if k and val:
                    out[k] = val
    return out


def strip_option_values(raw: str) -> str:
    """쉼표 뒤 옵션값(색상/수량 등)을 제거. "무선청소기 YQ-669, 화이트, 1개" → "무선청소기 YQ-669".

    A3: 이호 규칙상 옵션포괄/옵션값은 상품명·고시 품명에 금지. 쉼표 세그먼트 중 옵션성만 컷.
    브랜드 제거는 하지 않는다(고시 품명은 제품 정체성 유지). 상품명/고시 품명 공통 사용.
    """
    name = (raw or "").strip()
    if "," in name:
        segs = [s.strip() for s in name.split(",")]
        kept = [segs[0]]
        for s in segs[1:]:
            if s and not OPTION_VALUE.search(s):
                kept.append(s)
        name = " ".join(kept).strip()
    return re.sub(r"\s+", " ", name).strip()


def clean_name(raw: str, brands):
    name = SITE_SUFFIX.sub("", raw or "").strip()
    # 쿠팡 제목의 " - 대표키워드" 꼬리 분리
    tail = ""
    if " - " in name:
        name, tail = [s.strip() for s in name.rsplit(" - ", 1)]
    # A3: 쉼표 뒤 옵션값(색상/수량 등) 제거
    name = strip_option_values(name)
    for b in brands:
        name = re.sub(rf"(^|\s){re.escape(b)}(\s|$)", " ", name).strip()
    name = re.sub(r"\s+", " ", name)
    return name, tail


def parse_prices(text: str):
    nums = [int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?=\s*원)", text or "")]
    return nums


MAKER_FALLBACK_WORDS = {"생활용품", "인테리어소품", "공간활용", "실용템", "집들이선물", "살림템", "신혼집",
                        "정리용품", "실용아이템", "공간연출", "감성조명"}
SEED_STOP = {"상품", "구성", "옵션", "사용", "제품", "확인", "이런", "분께", "좋아요", "하세요", "있어요", "1개", "개"}
# 섹션 제목은 문장이라 조사·어미가 붙은 토큰을 뺀다 (명사형 후보만 남김)
NON_NOUN_END = re.compile(r"(으로|에서|에게|까지|부터|처럼|보다|하게|하고|해서|했다면|였다면|웠다면|졌다면|다면|"
                          r"세요|어요|아요|해요|네요|니다|습니다|는데|지만|으면|려면|는|은|을|를|이|가|로|에|도|의|과|와|"
                          r"면|게|고|한|던|된|운|인|할|될|찾|다|요|만|지|든|기)$")
SECTION_STOP = {"때마다", "간편하게", "다양하게", "자연스럽게", "깔끔하게", "가볍고", "평범한", "복잡하지",
                "디자인", "분명한", "이것만", "살펴볼수록", "화면에서", "익숙하지", "충분합니다", "특히"}


def keyword_seeds(cleaned, tail, sections, maker_kw, secondary_title):
    """F12 검증 전 '후보' 키워드. source 로 출처를 남긴다. 확정 키워드가 아니다."""
    seeds = []

    def add(k, source, confidence):
        k = re.sub(r"[^0-9A-Za-z가-힣+ ]", "", str(k or "")).strip()
        if len(k.replace(" ", "")) < 2 or k in SEED_STOP or re.fullmatch(r"[\d ]+", k):
            return
        if any(s["keyword"].replace(" ", "") == k.replace(" ", "") for s in seeds):
            return
        seeds.append({"keyword": k, "source": source, "confidence": confidence, "f12": None})

    if cleaned:
        add(cleaned.split(",")[0], "원상품명(전체)", "high")
        for tok in cleaned.replace(",", " ").split():
            add(tok, "원상품명(토큰)", "high")
    if tail:
        for t in re.split(r"[/,]", tail):
            add(t, "원상품 대표키워드(제목 꼬리)", "high")
    for s in sections:
        name = s.get("section_name", "")
        for tok in re.findall(r"[가-힣A-Za-z0-9]{2,}", name):
            if len(tok) >= 3 and not NON_NOUN_END.search(tok) and tok not in SECTION_STOP:
                add(tok, "메이커 섹션 제목", "medium")
    for k in maker_kw:
        add(k, "메이커 seo_keywords.json(규칙기반)" if k not in MAKER_FALLBACK_WORDS else "메이커 고정 대체어(근거 약함)",
            "low")
    return {"seeds": seeds[:40],
            "from1688": {"title": secondary_title, "needsTranslation": bool(re.search(r"[\u4e00-\u9fff]", secondary_title or "")),
                         "howTo": "중국어 제목·옵션명을 한국어 상품 용어로 번역해 후보에 추가(source='1688 번역')"},
            "rule": "후보일 뿐이다. naver_f12_capture.js 판정이 '미적용/판정불가'이거나 카테고리 relevance 가 실제 상품 카테고리를 가리키지 않으면 상품명·태그에 쓰지 않는다"}


def load_maker_keywords(folder: Path):
    p = folder / "market" / "seo_keywords.json"
    data = load_json(p) if p.exists() else None
    out = []
    if isinstance(data, list):
        out = [x if isinstance(x, str) else (x.get("keyword") or x.get("text") or "") for x in data]
    elif isinstance(data, dict):
        for key in ("keywords", "related_keywords", "seo_keywords", "tags", "search_tags"):
            v = data.get(key)
            if isinstance(v, list):
                out += [x if isinstance(x, str) else (x.get("keyword") or "") for x in v]
    return [x for x in out if x]


def section_copy(manifest, result_md: str):
    out = []
    for s in manifest.get("sections", []) or []:
        out.append({k: s.get(k) for k in ("section_index", "section_name", "headline", "subcopy") if s.get(k)})
    if not any("headline" in s for s in out):
        heads = re.findall(r"- 헤드라인:\s*(.+)", result_md or "")
        for i, h in enumerate(heads):
            if i < len(out):
                out[i]["headline"] = h.strip()
            else:
                out.append({"section_index": i + 1, "headline": h.strip()})
    return out


def suggest_price(cost_krw):
    pr = PROFILE["pricing"]
    raw = (cost_krw + pr["shippingCostKrw"]) / (1 - pr["marginRate"])
    step = pr["roundTo"]
    sale = int(round(raw / step) * step)
    return {
        "naverSalePrice_paidShipping": int(round((cost_krw / (1 - pr["marginRate"])) / step) * step),
        "coupangSalePrice_freeShipping": sale,
        "coupangOriginalPrice": int(round(sale * pr["coupangOriginalPriceRatio"] / step) * step),
        "formula": f"(원가 {cost_krw} + 배송비 {pr['shippingCostKrw']}) / (1 - {pr['marginRate']})",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--out", required=True, help="Aside 세션 tmp 안의 작업 폴더")
    ap.add_argument("--cost-krw", type=float)
    ap.add_argument("--cost-cny", type=float)
    a = ap.parse_args()

    folder = Path(a.folder)
    if not folder.is_absolute() and not folder.exists():
        folder = Path(PROFILE["sourceFolders"]["makerDoneRoot"]) / a.folder
    folder = folder.resolve()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    blockers, warnings, needs_user = [], [], []
    src = load_json(folder / "source.json")
    meta = load_json(folder / "metadata.json")
    manifest = load_json(folder / "copy_manifest.json")
    result_md = (folder / "result.md").read_text(encoding="utf-8") if (folder / "result.md").exists() else ""
    if not src and not meta:
        blockers.append("source.json / metadata.json 이 없어 원상품 근거를 확인할 수 없습니다")

    url = src.get("url") or meta.get("url") or ""
    secondary = src.get("secondary_url") or meta.get("secondary_url") or ""
    kind, pid = product_id_from_url(url)
    meta_kind, meta_pid = product_id_from_url(meta.get("url", ""))
    if pid and meta_pid and pid != meta_pid:
        blockers.append(f"source.json 상품번호 {pid} 와 metadata.json 상품번호 {meta_pid} 가 다릅니다")

    facts = parse_facts(src.get("facts"))
    maker_of = facts.get("제조자(수입자)") or facts.get("제조자") or facts.get("제조사") or ""
    raw_title = src.get("product_name") or src.get("title") or meta.get("product_name") or ""
    first_token = (SITE_SUFFIX.sub("", raw_title).split() or [""])[0]
    brands = []
    if maker_of:
        brands.append(maker_of)
    if first_token and first_token == maker_of:
        pass
    elif first_token and maker_of and first_token in maker_of:
        brands.append(first_token)
    own = [b for b in PROFILE["seller"].get("ownBrands", []) if b and b in raw_title]
    brands = sorted(set(b for b in brands if b and not any(o in b for o in own)), key=len, reverse=True)
    blocked = source_blocked(raw_title, src.get("text", ""))
    needs_browser = []
    if blocked:
        cleaned, tail_kw = "", ""
        needs_browser.append(
            "원상품 페이지 수집이 차단/실패했습니다. Aside 브라우저로 source.url 을 직접 열어 상품명·가격·옵션·"
            "상품정보제공고시(제조자/제조국/인증)·브랜드를 읽고 plan.source 에 채운 뒤 진행하세요. "
            "그 전까지 상품명은 sectionCopy·1688 제목(secondaryTitle)으로만 추정 후보를 만들고 확정하지 않습니다")
    else:
        cleaned, tail_kw = clean_name(raw_title, brands)
    if own:
        warnings.append(f"자체 브랜드({', '.join(own)})로 판단해 브랜드를 유지합니다. 아니면 config ownBrands 에서 빼세요")

    origins = meta.get("source_image_counts_by_origin") or {}
    if "ownerclan" in origins or kind == "coupang":
        supply = "domestic"  # 국내 위탁/도매(오너클랜 등) → 국내 일반배송
    elif kind == "1688/tmall":
        supply = "overseas_or_unknown"
        needs_user.append("공급 방식: 1688 직구 해외구매대행인지 국내 재고/위탁인지 확인 (쿠팡 해외구매대행은 해외 출고지·인보이스 필요)")
    else:
        supply = "unknown"
        needs_user.append("공급 방식(국내배송/해외구매대행) 확인")

    prices = parse_prices(src.get("price_text") or meta.get("price_text") or "")
    cost = a.cost_krw or (a.cost_cny * PROFILE["pricing"]["cnyToKrw"] if a.cost_cny else None)
    pricing = {"sourcePriceTextKrw": prices, "note": "원상품(경쟁) 판매가 참고값. 원가 아님"}
    if cost:
        pricing["suggested"] = suggest_price(cost)
        pricing["costKrw"] = cost
    else:
        needs_user.append("판매가 또는 공급원가(원/위안) - 원가 근거가 없어 판매가를 계산하지 않았습니다")

    options = src.get("option_rows") or []
    if not options and not (src.get("options_text") or "").strip():
        warnings.append("수집된 옵션이 없습니다 → 단일상품으로 등록 (1688 원문 옵션이 있으면 확인)")

    # 이미지 — 완료된폴더는 루트에 1~5.png, 상세페이지 자동화 결과 폴더는 thumbnails/1~5.png 에 둔다.
    thumbs, missing = [], []
    for i in range(1, 6):
        candidates = [folder / f"{i}.png", folder / "thumbnails" / f"{i}.png"]
        p = next((c for c in candidates if c.exists()), candidates[0])
        (thumbs if p.exists() else missing).append(p)
    if missing:
        blockers.append("썸네일 누락: " + ", ".join(m.name for m in missing) + " (루트 또는 thumbnails\\ 폴더)")
    detail = folder / "detail_page.png"
    if not detail.exists():
        blockers.append("detail_page.png 누락")
    sections = sorted((folder / "sections").glob("*.png")) if (folder / "sections").exists() else []

    up = out / "upload"
    up.mkdir(exist_ok=True)
    files = {"thumbs": [], "detail": None, "sections": []}
    for i, p in enumerate(thumbs, 1):
        dst = up / f"thumb_{i}.png"
        shutil.copy2(p, dst)
        wh = png_size(dst)
        mb = dst.stat().st_size / 1e6
        files["thumbs"].append({"path": str(dst), "size": wh, "mb": round(mb, 2), "source": p.name})
        if i == 1 and (not wh or wh[0] != wh[1] or wh[0] < 500 or mb > 3):
            blockers.append(f"쿠팡 대표이미지 규격 위반(정사각형 500~5000px, 3MB 이하): {wh} {mb:.2f}MB")
        if wh and wh[0] != wh[1]:
            warnings.append(f"{p.name} 정사각형 아님 {wh}")
    if detail.exists():
        dst = up / "detail_page.png"
        shutil.copy2(detail, dst)
        mb = dst.stat().st_size / 1e6
        files["detail"] = {"path": str(dst), "size": png_size(dst), "mb": round(mb, 2)}
        if mb > 20:
            warnings.append(f"detail_page.png {mb:.1f}MB > 20MB: 네이버 에디터 업로드 실패 가능 → sections 순서 업로드로 대체")
    for i, p in enumerate(sections, 1):
        dst = up / f"section_{i:02d}.png"
        shutil.copy2(p, dst)
        files["sections"].append({"path": str(dst), "size": png_size(dst), "mb": round(dst.stat().st_size / 1e6, 2), "source": p.name})
    if not sections:
        warnings.append("sections 폴더가 없어 쿠팡 상세설명은 detail_page.png 1장으로 시도")

    plan = {
        "createdAt": datetime.now().isoformat(timespec="seconds"),
        "productFolder": str(folder),
        "workDir": str(out),
        "source": {"url": url, "platform": kind, "productId": pid, "secondaryUrl": secondary,
                   "rawTitle": raw_title, "tailKeyword": tail_kw, "category": src.get("category") or meta.get("category") or "",
                   "facts": facts, "optionsText": src.get("options_text", ""), "optionRows": options,
                   "supply": supply, "imageOrigins": origins, "blocked": blocked,
                   "secondaryTitle": (src.get("secondary_source") or {}).get("title", "")},
        "brand": {"removedFromMarketing": brands, "ownKept": own,
                  "rule": "브랜드/판매자명은 상품명·태그·홍보문구에서 제거. 고시정보 제조자·수입자·제조국은 사실대로 유지"},
        "cleanedName": cleaned,
        "notice": {"품명": strip_option_values(facts.get("품명 및 모델명") or cleaned), "제조국": facts.get("제조국(원산지)") or facts.get("제조국") or "",
                   "제조자/수입자": maker_of, "인증": facts.get("인증/허가 사항") or ""},
        "sectionCopy": section_copy(manifest, result_md),
        "keywordSeeds": keyword_seeds(cleaned, tail_kw, section_copy(manifest, result_md), load_maker_keywords(folder),
                                      (src.get("secondary_source") or {}).get("title", "")),
        "pricing": pricing,
        "images": {
            "naver": {"representative": files["thumbs"][0]["path"] if files["thumbs"] else None,
                      "additional": [t["path"] for t in files["thumbs"][1:]],
                      "detailEditor": [files["detail"]["path"]] if files["detail"] else [s["path"] for s in files["sections"]]},
            "coupang": {"representative": files["thumbs"][0]["path"] if files["thumbs"] else None,
                        "additional": [t["path"] for t in files["thumbs"][1:]],
                        "detailContents": [s["path"] for s in files["sections"]] or ([files["detail"]["path"]] if files["detail"] else [])},
            "files": files,
        },
        "naver": {"categoryPath": "", "categoryEvidence": {}, "f12Evidence": [], "keywordJudgements": [],
                  "productName": "", "tags": [], "salePrice": None},
        "coupang": {"categoryPath": "", "productName": "", "tags": [], "salePrice": None, "originalPrice": None,
                    "deliveryMethod": PROFILE["coupang"]["deliveryMethodDomestic"] if supply == "domestic" else None},
        "blockers": blockers,
        "warnings": warnings,
        "needsUser": needs_user,
        "needsBrowser": needs_browser,
    }
    if PROFILE["seller"].get("asPhone") in (None, ""):
        plan["needsUser"].append("A/S 전화번호 (한 번 받으면 config/seller_profile.json 에 저장)")
    path = out / "registration_plan.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"plan": str(path), "cleanedName": cleaned, "brandRemoved": brands, "supply": supply,
                      "sourceBlocked": blocked, "needsBrowser": needs_browser,
                      "blockers": blockers, "warnings": warnings, "needsUser": plan["needsUser"]}, ensure_ascii=False, indent=2))
    return 2 if blockers else 0


if __name__ == "__main__":
    sys.exit(main())
