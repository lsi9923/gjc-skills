// '메이커 셀링 도우미' 크롬 확장(mahaehkollojpjbngbifikgpdenkflih)이 페이지에 끼워 넣은
// 분석 결과(완성형/조합형 텀 칩, 카테고리, 검색량, 스마트스토어 태그)를 읽는 보조 수집기.
//
// 규칙 (중요):
//  - 이 데이터는 'F12 근거(naver_f12_capture.js)를 보조하는 참고자료'로만 쓴다.
//    상품명·태그 확정 근거는 어디까지나 F12 terms/intersectionTerms/relevance 다.
//  - 확장이 없거나 패널이 안 뜨면 { available:false } 를 반환하고, 호출부는 이 단계를 건너뛴다.
//  - 확장 파일은 절대 수정하지 않는다(읽기 전용). 외부 서버(searchad/maker39)를 이 스크립트가 직접 부르지 않는다.
//    확장이 이미 렌더한 값만 DOM/Shadow DOM 에서 읽는다.
//
// v2 (2026-09, 격리 런타임 검증 반영):
//   실제 확장은 검색결과 페이지에서 UI 전체를 #nvs-word-cloud-container-host 의
//   **Shadow DOM(open)** 안에 렌더한다. Light DOM 에는 폰트 style 노드와 host div 뿐이다.
//   따라서 chips/panels 는 shadow root 안에서 찾아야 한다(v1 은 light DOM 만 봐서 항상 빈 결과였다).
//   실제 칩 구조(content.js 함수 Zi 확인):
//     <span class="nvs-terms-chip">
//       <span>유산균</span>                              ← 키워드 (클래스 없음)
//       <span style="color:#2563eb;background:#eff6ff">terms</span>            ← 완성형 배지
//       <span style="color:#d97706;background:#fef3c7">intersectionTerms</span> ← 조합형 배지
//     </span>
//   배지는 클래스가 없고 텍스트가 정확히 'terms' / 'intersectionTerms' 이며 색으로도 구분된다
//   (terms=#2563eb 파랑, intersectionTerms=#d97706 주황). 한 칩에 배지가 여러 개일 수 있다.
//   스마트스토어(smartstore.js)는 #nvs-smartstore-seller-tags-host 의 shadow root 에 태그를 렌더한다.
//
// 하위호환: 예전 합성 fixture 처럼 배지가 <span class="nvs-chip-badge">terms</span> 형태이거나
//   칩이 light DOM 에 있어도 그대로 읽는다.
//
// 사용 (Aside REPL):
//   const src = await fs.readFile('<skill>/scripts/maker_helper_extract.js','utf8');
//   const ev = await page.evaluate(src);   // 파일 전체가 IIFE
//   if (ev.available) { /* ev.terms / ev.intersectionTerms / ev.categories 를 참고자료로 병기 */ }
(() => {
  const nf = (s) => String(s ?? "").normalize("NFC").replace(/\s+/g, " ").trim();

  // Light DOM + 모든 open shadow root 를 재귀적으로 훑어 querySelectorAll 을 합친다.
  const roots = [];
  (function collect(root) {
    roots.push(root);
    const all = root.querySelectorAll ? root.querySelectorAll("*") : [];
    for (const el of all) {
      if (el.shadowRoot) collect(el.shadowRoot);
    }
  })(document);

  const qa = (sel) => {
    const out = [];
    for (const r of roots) {
      try { r.querySelectorAll(sel).forEach((e) => out.push(e)); } catch { /* ignore */ }
    }
    return out;
  };
  const q1 = (sel) => {
    for (const r of roots) {
      try { const e = r.querySelector(sel); if (e) return e; } catch { /* ignore */ }
    }
    return null;
  };

  // 확장 활성 판정: 확장이 삽입하는 host/패널/칩 중 하나라도 존재?
  // (실제 확장은 host div #nvs-word-cloud-container-host 를 항상 만들지만, 칩/패널은
  //  서버 분석 응답이 와야 shadow 안에 렌더된다.)
  const host = q1("#nvs-word-cloud-container-host");
  const ssHost = document.getElementById("nvs-smartstore-seller-tags-host");
  const anyChip = q1(".nvs-terms-chip");
  const anyPanel = q1(".nvs-ns-tab-panel, .nvs-terms-sub-panel, [class*='nvs-ns-']");
  if (!host && !ssHost && !anyChip && !anyPanel) {
    return {
      tool: "maker_helper_extract.js v2", available: false,
      note: "메이커 셀링 도우미 host/패널을 찾지 못함 — 확장 비활성/미로드로 보고 이 단계 건너뜀(F12 근거만 사용)",
      capturedAt: new Date().toISOString(), role: "F12 보조 참고자료",
    };
  }

  // 칩 하나를 {keyword, badges[]} 로 해석.
  // 배지 판정 우선순위: (1) 텍스트가 정확히 terms/intersectionTerms (2) 인라인 color
  //   terms=#2563eb, intersectionTerms=#d97706 (3) 예전 fixture: class*=badge/type + 텍스트.
  const BLUE = /#2563eb/i;      // terms 색
  const ORANGE = /#d97706/i;    // intersectionTerms 색
  const badgeKind = (span) => {
    const t = nf(span.textContent).toLowerCase();
    const style = span.getAttribute("style") || "";
    const cls = (typeof span.className === "string" ? span.className : "") || "";
    if (t === "intersectionterms" || /intersection|조합/.test(t)) return "intersection";
    if (t === "terms" || /(^|[^a-z])term($|[^a-z])|완성/.test(t)) return "terms";
    if (ORANGE.test(style)) return "intersection";
    if (BLUE.test(style)) return "terms";
    if (/badge|type/i.test(cls)) {
      if (/intersection|조합/i.test(t)) return "intersection";
      if (/term|완성/i.test(t)) return "terms";
    }
    return null;
  };

  const terms = [], intersection = [], unknownChips = [];
  qa(".nvs-terms-chip").forEach((chip) => {
    const spans = Array.from(chip.querySelectorAll("span"));
    // 배지 span 들과 키워드 span 을 분리
    const badgeSpans = spans.filter((s) => badgeKind(s) !== null && !s.querySelector("span"));
    const kinds = new Set(badgeSpans.map(badgeKind).filter(Boolean));
    // 키워드 = 칩 전체 텍스트에서 배지 텍스트를 뺀 것 (배지 없는 첫 span 우선)
    let keyword = "";
    const nonBadge = spans.filter((s) => badgeKind(s) === null && !s.querySelector("span"));
    if (nonBadge.length) keyword = nf(nonBadge[0].textContent);
    if (!keyword) {
      let full = nf(chip.textContent);
      badgeSpans.forEach((b) => { full = full.replace(nf(b.textContent), "").trim(); });
      keyword = full;
    }
    if (!keyword) return;
    if (kinds.has("terms")) terms.push(keyword);
    else if (kinds.has("intersection")) intersection.push(keyword);
    else unknownChips.push({ text: keyword, badge: nf(badgeSpans.map((b) => b.textContent).join("|")) });
  });

  // 요약(비율) 패널
  const summary = nf(q1(".nvs-terms-sub-panel")?.textContent || "");

  // 카테고리 패널/카드 텍스트 (카테고리 relevance 추출 탭)
  const categoryText = qa(".nvs-ns-categories-panel, .nvs-category-item-card, [class*='categories']")
    .map((el) => nf(el.textContent)).filter((t) => t && !/추출된 카테고리 정보가 없습니다/.test(t)).slice(0, 6);

  // 검색량 셀(searchad 키가 있을 때만 값이 참). 값 없으면 표시 안 됨.
  const volumeCells = qa("[data-tooltip*='검색수'], .nvs-cell-total-search, [class*='search-volume'], [class*='searchVolume']")
    .map((el) => nf(el.getAttribute("data-tooltip") || el.textContent)).filter(Boolean).slice(0, 60);

  // 스마트스토어 판매자 태그(경쟁상품 상세, Shadow DOM 진입)
  let smartstoreTags = null;
  if (ssHost && ssHost.shadowRoot) {
    smartstoreTags = Array.from(ssHost.shadowRoot.querySelectorAll(".nvs-tags__chip")).map((c) => ({
      text: nf(c.textContent),
      reflected: c.classList.contains("nvs-tags__chip--on"),
    }));
  }

  const hasData = terms.length || intersection.length || categoryText.length || (smartstoreTags && smartstoreTags.length);

  return {
    tool: "maker_helper_extract.js v2",
    available: true,
    role: "F12 보조 참고자료 (확정 근거 아님)",
    capturedAt: new Date().toISOString(),
    pageUrl: location.href,
    // 확장 host 는 있으나 서버 분석 응답 전이라 칩이 아직 없을 수 있음 → hasData 로 표시
    hasData: !!hasData,
    renderedInShadow: !!(host && host.shadowRoot),
    terms: [...new Set(terms)],
    intersectionTerms: [...new Set(intersection)],
    unknownChips,
    termsSummary: summary,
    categoryText,
    volumeCells,
    smartstoreTags,
    note: "값은 확장이 이미 렌더한 것만 읽음(Shadow DOM 포함). host 만 있고 칩이 없으면 hasData:false — 확장이 서버 분석 응답을 기다리는 상태. 검색량은 사용자 searchad 키가 있을 때만 참값. 상품명·태그 확정은 F12(naver_f12_capture.js) 근거로 한다.",
  };
})()
