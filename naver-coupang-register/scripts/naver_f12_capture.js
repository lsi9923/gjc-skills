// 네이버 쇼핑 F12(개발자도구) 패킷 수집기 — 이호 강의 2-1/2-3/2-5 자동화.
// F12 Network 탭에서 하던 일을 페이지 안에서 그대로 한다:
//   1) Network 목록  = performance resource 엔트리 + 지금부터의 fetch/XHR 가로채기
//   2) Preview/Response = 같은 로그인 세션으로 해당 JSON 응답을 다시 읽기(GET만)
//   3) #__NEXT_DATA__(서버 렌더 패킷) + 스크립트 태그 JSON 폴백까지 포함해
//      terms / intersectionTerms / 카테고리 relevance 를 키 이름·모양으로 전수 탐색
//      (NaverSEOStudio packet-discovery.js 방식, 경로를 함께 기록)
// f12_live 실측(2026-09) 반영: 차단은 405/418/429 HTTP 상태로 먼저 오므로,
//   (a) 이 스크립트는 캡처한 응답의 status 로도 차단을 판정하고(httpBlocked),
//   (b) 하네스(Playwright)는 page.goto 응답 resp.status 로 조기 차단 판정을 권장한다.
//   (SKILL.md §2-② 수집 절차 참조)
// 사용 (Aside REPL, search.shopping.naver.com/search/all?query=... 페이지에서):
//   const src = String(await fs.readFile('<skill>\\scripts\\naver_f12_capture.js'));
//   const ev = await page.evaluate(`(${src})(${JSON.stringify({ target: '모양펀치', title: '' })})`);
// target = 검색한 키워드, title = (검증 단계) 완성 상품명. 개인정보(쿠키·계정·주소)는 읽지 않는다.
async (opts = {}) => {
  const MAX_FETCH = 15, MAX_NODES = 60000, MAX_DEPTH = 12;
  const nf = (s) => String(s ?? "").normalize("NFC").trim();
  const compact = (s) => nf(s).replace(/\s+/g, "").toLowerCase();
  const started = Date.now();
  const packets = [];
  let httpBlocked = false;      // 405/418/429 등 차단 상태코드 관측 여부
  const blockStatuses = [];

  // --- 1. 서버 렌더 패킷
  try {
    const nd = document.querySelector("#__NEXT_DATA__")?.textContent;
    if (nd) packets.push({ source: "#__NEXT_DATA__", url: location.href, json: JSON.parse(nd) });
  } catch (e) { /* ignore */ }

  // --- 2. 지금부터 발생하는 fetch/XHR 가로채기 (F12 Network 녹화와 동일, 트래픽은 그대로 통과)
  const live = [];
  const okUrl = (u) => { try { const x = new URL(u, location.href); return /(^|\.)shopping\.naver\.com$/.test(x.hostname) && x.origin === location.origin; } catch { return false; } };
  const origFetch = window.fetch;
  window.fetch = async function (...args) {
    const res = await origFetch.apply(this, args);
    try {
      const u = typeof args[0] === "string" ? args[0] : args[0]?.url;
      if (okUrl(u)) {
        if ([405, 418, 429, 403].includes(res.status)) { httpBlocked = true; blockStatuses.push(res.status); }
        res.clone().text().then((t) => live.push({ url: u, text: t, status: res.status })).catch(() => {});
      }
    } catch { /* ignore */ }
    return res;
  };
  const OrigOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (m, u, ...rest) {
    this.addEventListener("load", () => {
      try {
        if (okUrl(u)) {
          if ([405, 418, 429, 403].includes(this.status)) { httpBlocked = true; blockStatuses.push(this.status); }
          live.push({ url: u, text: this.responseText, status: this.status });
        }
      } catch { }
    });
    return OrigOpen.call(this, m, u, ...rest);
  };
  // 추가 목록/필터 요청을 유도(사람이 스크롤하는 것과 같음)
  for (let i = 0; i < 4; i++) { window.scrollBy(0, Math.max(800, innerHeight)); await new Promise((r) => setTimeout(r, 700)); }
  window.scrollTo(0, 0);
  await new Promise((r) => setTimeout(r, 800));
  window.fetch = origFetch; XMLHttpRequest.prototype.open = OrigOpen;

  // --- 3. 이미 지나간 Network 목록 → 같은 세션으로 응답 본문 다시 읽기 (GET 전용)
  const seen = new Set(live.map((x) => x.url));
  const entries = performance.getEntriesByType("resource")
    .filter((e) => ["fetch", "xmlhttprequest"].includes(e.initiatorType) && okUrl(e.name))
    .map((e) => e.name)
    .filter((u) => !seen.has(u) && !/\.(js|css|png|jpe?g|gif|webp|svg|woff2?)(\?|$)/i.test(u) && !/log|beacon|collect|ad\.|nelo|lcs/i.test(u));
  const networkList = [...new Set([...live.map((x) => x.url), ...entries])];
  for (const u of [...new Set(entries)].slice(0, MAX_FETCH)) {
    try {
      const r = await origFetch(u, { credentials: "include", headers: { accept: "application/json, text/plain, */*" } });
      if ([405, 418, 429, 403].includes(r.status)) { httpBlocked = true; blockStatuses.push(r.status); }
      const t = await r.text();
      live.push({ url: u, text: t, status: r.status });
    } catch { /* ignore */ }
  }
  for (const x of live) {
    const t = (x.text || "").trim();
    if (!t.startsWith("{") && !t.startsWith("[")) continue;
    try { packets.push({ source: "network", url: x.url, json: JSON.parse(t) }); } catch { }
  }
  // 폴백: 페이지 내 <script type="application/json"> / __NEXT_DATA 외 JSON 스크립트도 훑는다
  try {
    document.querySelectorAll('script[type="application/json"], script[id*="DATA"], script[id*="state"]').forEach((s) => {
      const t = (s.textContent || "").trim();
      if ((t.startsWith("{") || t.startsWith("[")) && t.length > 20) {
        try { packets.push({ source: "script-json:" + (s.id || s.type), url: location.href, json: JSON.parse(t) }); } catch { }
      }
    });
  } catch { /* ignore */ }

  // --- 4. 전수 탐색 (키 이름 + 모양, JSON 경로 기록)
  const TERMS_KEY = /^(terms?|queryTerms|searchTerms|termList|analyzedTerms|morphemes?|tokens?)$/i;
  const INTER_KEY = /(intersection|commonTerms?|common_terms?|commonKeywords?)/i;
  const CAT_CONTAINER = /^(cmp|cmpOrg|CMP_ORG|CMPG|categoryRelevance|categories)$/i;
  const wordOf = (v) => typeof v === "string" ? nf(v) : (v && typeof v === "object") ? nf(v.word ?? v.term ?? v.keyword ?? v.text ?? v.value ?? v.name ?? v.query) : "";
  const found = { terms: [], intersection: [], categories: [] };
  for (const pk of packets) {
    const q = [{ v: pk.json, path: "$", key: "", d: 0 }];
    let nodes = 0;
    while (q.length && nodes < MAX_NODES) {
      const { v, path, key, d } = q.shift(); nodes++;
      if (d > MAX_DEPTH) continue;
      if (Array.isArray(v)) {
        if (TERMS_KEY.test(key) || INTER_KEY.test(key)) {
          const words = v.map(wordOf).filter(Boolean).slice(0, 128);
          if (words.length) (INTER_KEY.test(key) ? found.intersection : found.terms).push({ url: pk.url, source: pk.source, path, words });
        }
        const cats = v.filter((o) => o && typeof o === "object" && Number.isFinite(Number(o.relevance ?? o.score)) && (o.name ?? o.categoryName) && (o.id ?? o.categoryId))
          .map((o) => ({ id: nf(o.id ?? o.categoryId), name: nf(o.name ?? o.categoryName), relevance: Number(o.relevance ?? o.score) }));
        if (cats.length && cats.length === v.length) {
          const lv = /category([1-4])/i.exec(path);
          found.categories.push({ url: pk.url, source: pk.source, path, level: lv ? Number(lv[1]) : null, categories: cats.slice(0, 32) });
        }
        v.slice(0, 200).forEach((it, i) => { if (it && typeof it === "object") q.push({ v: it, path: `${path}[${i}]`, key, d: d + 1 }); });
      } else if (v && typeof v === "object") {
        for (const [k, it] of Object.entries(v)) {
          if (it && typeof it === "object") q.push({ v: it, path: `${path}.${k}`, key: k, d: d + 1 });
          else if (typeof it === "string" && (TERMS_KEY.test(k) || INTER_KEY.test(k)) && it.trim()) {
            const words = it.split(/[\s,|]+/).map(nf).filter(Boolean);
            (INTER_KEY.test(k) ? found.intersection : found.terms).push({ url: pk.url, source: pk.source, path: `${path}.${k}`, words });
          }
        }
        if (CAT_CONTAINER.test(key)) { /* 컨테이너 자체는 위 배열 탐색에서 잡힘 */ }
      }
    }
  }

  // --- 5. 이호 판정 (2-3 완성형/조합형, 2-5 교집합 검증)
  const allTerms = [...new Set(found.terms.flatMap((t) => t.words))];
  const allInter = [...new Set(found.intersection.flatMap((t) => t.words))];
  const classify = (kw) => {
    const c = compact(kw);
    if (!c) return null;
    const tokens = nf(kw).split(/\s+/).filter(Boolean);
    const whole = allTerms.some((t) => compact(t) === c);
    const inInter = allInter.some((t) => compact(t) === c);
    const parts = allTerms.filter((t) => c.includes(compact(t)) && compact(t).length > 0);
    let type;
    if (whole && tokens.length === 1) type = "완성형";
    else if (whole) type = "연결형(한 덩어리로 인식)";
    else if (inInter) type = "교집합(intersection)으로 이동";
    else if (parts.length >= 2 && parts.map(compact).join("").length >= c.length * 0.8) type = "조합형";
    else if (parts.length) type = "부분 인식";
    else type = allTerms.length ? "미적용" : "판정불가(terms 패킷 없음)";
    return { keyword: kw, type, matchedTerms: parts, inIntersection: inInter };
  };
  const titleCheck = opts.title ? nf(opts.title).split(/\s+/).filter(Boolean).map((w) => ({
    word: w,
    status: allTerms.some((t) => compact(t) === compact(w)) ? "terms"
      : allInter.some((t) => compact(t) === compact(w)) ? "intersection"
      : allTerms.some((t) => compact(w).includes(compact(t)) || compact(t).includes(compact(w))) ? "부분" : "누락",
  })) : [];

  const bodyBlocked = /비정상적인 접근|접속이 일시적으로 제한|보안문자|보안 확인을 완료|captcha|로봇이 아닙/i.test(document.body?.innerText?.slice(0, 3000) ?? "");
  const blocked = bodyBlocked || httpBlocked;
  return {
    tool: "naver_f12_capture.js v2",
    capturedAt: new Date().toISOString(),
    elapsedMs: Date.now() - started,
    pageUrl: location.href,
    blockedOrCaptcha: blocked,
    httpBlocked,
    blockStatuses: [...new Set(blockStatuses)],
    networkRequests: networkList.slice(0, 40),
    packetsParsed: packets.map((p) => ({ source: p.source, url: p.url })),
    termsPackets: found.terms.slice(0, 10),
    intersectionPackets: found.intersection.slice(0, 10),
    categoryPackets: found.categories.slice(0, 12),
    terms: allTerms,
    intersectionTerms: allInter,
    target: opts.target ? classify(opts.target) : null,
    titleCheck,
    schemaNote: blocked
      ? ("차단/캡차 감지" + (blockStatuses.length ? (" (HTTP " + [...new Set(blockStatuses)].join("/") + ")") : "") + " — 우회 금지. 사람이 캡차 통과 후 재시도.")
      : (found.terms.length ? "terms 패킷 발견" : "terms 키를 찾지 못함 — networkRequests 목록을 보고 스키마가 바뀌었는지 memory/sites 에 기록. 이 키워드는 '판정불가'로 표시(추측 금지)"),
  };
}
