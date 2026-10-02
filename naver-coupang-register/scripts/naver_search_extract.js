// 네이버 쇼핑 검색결과(__NEXT_DATA__)에서 공개 필드만 읽는 추출기.
// 출처: NaverSEOStudio dist/main/naver-search-page.js EXTRACT_NAVER_SEARCH_PAGE_SOURCE 포팅.
// 이호 강의 2-1(카테고리 relevance), 2-2(연관어), 2-3(terms) 근거 수집용.
// 사용 (Aside REPL):
//   const src = await fs.readFile('<skill>/scripts/naver_search_extract.js', 'utf8')  // 또는 read_file 결과
//   await page.goto('https://search.shopping.naver.com/search/all?query=' + encodeURIComponent(kw));
//   const ev = await page.evaluate(src);   // 파일 전체가 하나의 식(IIFE)이다
// 계정·쿠키·배송지 등 개인 데이터는 읽지 않는다.
(() => {
  const clean = (value, max = 500) => String(value ?? "").normalize("NFC").replace(/\s+/gu, " ").trim().slice(0, max);
  const page = (() => {
    try { return JSON.parse(document.querySelector("#__NEXT_DATA__")?.textContent ?? "{}"); }
    catch { return {}; }
  })();
  const props = page?.props?.pageProps ?? {};
  const product = (entry) => {
    const item = entry?.item ?? entry ?? {};
    return {
      id: clean(item.id ?? item.productId ?? item.nvMid ?? item.mallProductId, 80),
      title: clean(item.productTitle ?? item.productName ?? item.title, 300),
      tags: Array.isArray(item.manuTag) ? item.manuTag.slice(0, 40).map((x) => clean(x, 80)).filter(Boolean)
        : clean(item.manuTag, 1000).split(",").map((x) => x.trim()).filter(Boolean),
      brand: clean(item.brandName ?? item.brand, 120),
      maker: clean(item.makerName ?? item.maker, 120),
      mall: clean(item.mallName, 120),
      isAd: Boolean(item.adId || entry?.type === "ad" || item.adcrUrl),
      reviewCount: Number(item.reviewCount ?? item.reviewCountSum ?? 0) || 0,
      purchaseCount: Number(item.purchaseCnt ?? item.purchaseCount ?? 0) || 0,
      category: [1, 2, 3, 4].map((n) => clean(item[`category${n}Name`] ?? item[`fmpCategory${n}Name`], 60)).filter(Boolean).join(">"),
      categoryId: clean(item.category4Id || item.category3Id || item.category2Id || item.category1Id, 40),
    };
  };
  const related = (v) => typeof v === "string" ? clean(v, 120)
    : (v && typeof v === "object") ? clean(v.query ?? v.keyword ?? v.text ?? v.title ?? v.name, 120) : "";
  const levels = [1, 2, 3, 4].map((level) => {
    // f12_live 실측: 경로가 props.cmp.categoryN 또는 props.cmpOrg / CMP_ORG 로 바뀔 수 있어 폴백 순회
    const cont = props?.cmp?.["category" + level]
      || props?.cmpOrg?.["category" + level]
      || props?.CMP_ORG?.["category" + level]
      || props?.["category" + level];
    const rows = Array.isArray(cont?.categories) ? cont.categories : (Array.isArray(cont) ? cont : []);
    return {
      level,
      categories: rows.slice(0, 32).map((row) => ({
        id: clean(row?.id ?? row?.categoryId, 40),
        name: clean(row?.name ?? row?.categoryName, 120),
        relevance: Number(row?.relevance ?? row?.score),
      })).filter((c) => c.name),
    };
  });
  const products = (Array.isArray(props?.compositeList?.list) ? props.compositeList.list : [])
    .slice(0, 60).map(product).filter((p) => p.title);
  // 상위 비광고 상품 태그 빈도 (태그 후보 근거)
  const tagFreq = {};
  products.filter((p) => !p.isAd).slice(0, 40).forEach((p) => p.tags.forEach((t) => { tagFreq[t] = (tagFreq[t] || 0) + 1; }));
  return {
    sourceUrl: location.href,
    capturedAt: new Date().toISOString(),
    parser: "naver_search_extract.js v2 (NaverSEOStudio port + relevance 폴백)",
    query: clean(props?.searchParam?.query ?? props?.searchParam?.origQuery, 256),
    ok: levels.some((l) => l.categories.length > 0) && products.length > 0,
    blockedOrCaptcha: !document.querySelector("#__NEXT_DATA__")
      || /접속이 일시적으로 제한|보안 확인을 완료|비정상적인 접근|captcha/i.test(document.body?.innerText?.slice(0, 2000) ?? ""),
    categoryLevels: levels,
    relatedQueries: [
      ...(Array.isArray(props?.relatedQueries) ? props.relatedQueries : []),
      ...(Array.isArray(props?.relatedQueriesBottom) ? props.relatedQueriesBottom : []),
    ].slice(0, 40).map(related).filter(Boolean),
    topTagFrequency: Object.entries(tagFreq).sort((a, b) => b[1] - a[1]).slice(0, 40),
    products: products.slice(0, 20),
  };
})()
