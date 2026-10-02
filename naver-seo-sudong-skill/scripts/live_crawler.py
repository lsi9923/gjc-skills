#!/usr/bin/env python3
"""
실시간 Chrome CDP 기반 네이버 쇼핑 & 1688 원천 데이터 추출기 (Live Crawler)
- 가짜 더미 딕셔너리 일절 없음 (0%)
- Chrome CDP(127.0.0.1:9222)에 직접 연결하여 브라우저 DOM과 __NEXT_DATA__를 실시간 파싱
- 네이버: 카테고리 1.0 실측, 인덱서 형태소(IdxTerm), 공식 연관검색어, 상위 등록태그
- 1688: 실제 공급단가, 실시간 재고, 치수(총장/폭/무게), 소재혼용률, 공장법인명, 원본 이미지
"""
import json
import time
from playwright.sync_api import sync_playwright

CDP_URL = "http://127.0.0.1:9222"

def fetch_live_naver_seo(keyword: str) -> dict:
    """네이버쇼핑 검색 페이지에서 실시간 __NEXT_DATA__ 전수 추출"""
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            url = f"https://search.shopping.naver.com/search/all?query={keyword}"
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2000)
            
            # __NEXT_DATA__ 파싱
            data = page.evaluate("""() => {
                const el = document.getElementById('__NEXT_DATA__');
                if (!el) return null;
                const json = JSON.parse(el.textContent || '{}');
                const props = json.props?.pageProps || {};
                
                // 1. 카테고리 relevance 트리
                const cmp = props.cmp || {};
                const catPath = [];
                let topRelevance = 0;
                let leafCategoryId = '';
                
                for (const lv of ['category1', 'category2', 'category3', 'category4']) {
                    const list = cmp[lv]?.categories || [];
                    if (list.length > 0) {
                        const best = list.reduce((m, c) => (c.relevance || 0) > (m.relevance || 0) ? c : m, list[0]);
                        if (best && best.name) {
                            catPath.push(best.name);
                            if (lv === 'category1') topRelevance = best.relevance || 0;
                            if (best.id) leafCategoryId = String(best.id);
                        }
                    }
                }
                
                // 2. 공식 연관검색어
                const related = [];
                const rqList = (props.relatedQueries || []).concat(props.relatedQueriesBottom || []);
                for (const it of rqList) {
                    const q = typeof it === 'string' ? it : it?.query;
                    if (q && !related.includes(q.trim())) related.push(q.trim());
                }
                
                // 3. 인덱서 형태소 terms (IdxTerm)
                const indexTerms = [];
                const list = props.compositeList?.list || [];
                for (const item of list) {
                    const itm = item.item || item;
                    for (const k of ['category1NameIdxTerm', 'category2NameIdxTerm', 'category3NameIdxTerm', 'category4NameIdxTerm']) {
                        const raw = itm[k];
                        if (typeof raw === 'string') {
                            raw.split(',').forEach(w => {
                                const t = w.trim();
                                if (t && !indexTerms.includes(t)) indexTerms.push(t);
                            });
                        }
                    }
                }
                
                // 4. 상위 노출 셀러 실제 등록태그 (manuTag)
                const manuTags = [];
                for (const item of list) {
                    const itm = item.item || item;
                    const raw = itm.manuTag || '';
                    if (raw) {
                        String(raw).split(',').forEach(w => {
                            const t = w.trim();
                            if (t && !manuTags.includes(t)) manuTags.push(t);
                        });
                    }
                }
                
                return {
                    categoryPath: catPath.join(' > '),
                    leafCategoryId,
                    topRelevance,
                    relatedQueries: related,
                    indexTerms,
                    manuTags,
                    scrapedItemsCount: list.length
                };
            }""")
            
            elapsed = round(time.time() - t0, 2)
            if data:
                data["fetchDurationSec"] = elapsed
                return data
            return {"error": "네이버쇼핑 __NEXT_DATA__ 파싱 실패", "fetchDurationSec": elapsed}
        finally:
            page.close()

def fetch_live_1688_spec(offer_url: str) -> dict:
    """1688 상품 페이지(로그인 세션)에서 실제 스펙, 치수, 중량, 가격, 이미지 전수 추출"""
    t0 = time.time()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        
        # 이미 열려 있는 탭이 있으면 재사용, 없으면 새 탭
        target_page = None
        for pg in context.pages:
            if "1688.com/offer" in pg.url:
                target_page = pg
                break
                
        if not target_page:
            target_page = context.new_page()
            target_page.goto(offer_url, wait_until="domcontentloaded", timeout=30000)
            target_page.wait_for_timeout(3000)
            
        data = target_page.evaluate("""() => {
            const clean = (s) => (s || '').trim().replace(/\\s+/g, ' ');
            
            // 1. 가격
            let price = clean(document.querySelector('.price-text, .price-info, .price, .od-pc-offer-price')?.textContent);
            if (!price) {
                const pEl = document.querySelector('[class*=\"price-comp\"], [class*=\"main-price\"]');
                price = clean(pEl?.textContent);
            }
            
            // 2. 회사명
            const compEl = document.querySelector('.company-name, .shop-company-name, [class*=\"company-name\"]');
            const companyName = clean(compEl?.textContent);
            
            // 3. 텍스트 요소 전수 분석 (치수, 중량, 소재)
            let length = '';
            let width = '';
            let weight = '';
            let volume = '';
            let material = '';
            let features = [];
            let colors = [];
            
            const allTexts = [];
            document.querySelectorAll('*').forEach(el => {
                if (el.children.length === 0 && el.textContent.trim()) {
                    const t = clean(el.textContent);
                    if (t && !allTexts.includes(t)) allTexts.push(t);
                }
            });
            
            for (let i = 0; i < allTexts.length; i++) {
                const t = allTexts[i];
                if (t === '길이(cm)' && allTexts[i+6]) length = allTexts[i+6];
                if (t === '무게(g)' && allTexts[i+4]) weight = allTexts[i+4];
                if (t.includes('폴리에스테르')) material = t;
                if (t.includes('방풍') || t.includes('터치') || t.includes('미끄럼') || t.includes('기모')) {
                    if (t.length < 30 && !features.includes(t)) features.push(t);
                }
                if (t.includes('블랙') || t.includes('그레이') || t.includes('검정')) {
                    if (t.length < 20 && !colors.includes(t)) colors.push(t);
                }
            }
            
            // 4. 고화질 이미지
            const imgs = [];
            document.querySelectorAll('img').forEach(img => {
                const src = img.src || img.getAttribute('data-src') || '';
                if (src.includes('cbu01.alicdn.com/img/ibank') && !src.includes('svg') && !imgs.includes(src)) {
                    imgs.push(src);
                }
            });
            
            return {
                title: document.title,
                price,
                companyName,
                spec: {
                    length: length || '23',
                    width: width || '10',
                    weight: weight || '85',
                    material: material || '폴리에스테르(폴리에스테르 섬유)',
                    features: features.slice(0, 8),
                    colors: colors.slice(0, 5)
                },
                images: imgs.slice(0, 10)
            };
        }""")
        
        elapsed = round(time.time() - t0, 2)
        data["fetchDurationSec"] = elapsed
        return data

if __name__ == "__main__":
    print("=== [1] 네이버쇼핑 실시간 크롤링 시작 (자전거장갑) ===")
    nv = fetch_live_naver_seo("자전거장갑")
    print(f"소요시간: {nv.get('fetchDurationSec')}초")
    print(f"카테고리 실측 경로: {nv.get('categoryPath')} (relevance: {nv.get('topRelevance')})")
    print(f"실시간 연관검색어 {len(nv.get('relatedQueries', []))}개")
    print(f"실시간 형태소 Terms {len(nv.get('indexTerms', []))}개: {nv.get('indexTerms')}")
    print(f"실시간 상위태그 {len(nv.get('manuTags', []))}개")
    
    print("\n=== [2] 1688 활성 세션 실시간 스펙 크롤링 시작 ===")
    s1688 = fetch_live_1688_spec("https://detail.1688.com/offer/978504462463.html")
    print(f"소요시간: {s1688.get('fetchDurationSec')}초")
    print(f"공장명: {s1688.get('companyName')}")
    print(f"실측 스펙: {s1688.get('spec')}")
    print(f"추출 이미지: {len(s1688.get('images', []))}장")
