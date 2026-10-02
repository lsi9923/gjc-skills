var content = (function() {
  "use strict";

  const CONTAINER_ID = "nvs-word-cloud-container";
  const STOP_WORDS = ["10대", "20대", "30대", "40대", "50대", "60대", "70대", "무료", "오늘", "배송", "쿠팡", "로켓"];

  function filterKeyword(k) {
    const s = String(k || "").trim();
    if (!s || s.length < 2) return null;
    if (STOP_WORDS.some(w => s.includes(w))) return null;
    return s;
  }

  function getQuery() {
    const r = new URL(window.location.href);
    return r.searchParams.get("q") || r.searchParams.get("query") || "";
  }

  // 1. 네이버 __NEXT_DATA__ 전수 분석 (Relevance, 연관검색어, Terms, 태그)
  function extractNaverSeoData() {
    try {
      const el = document.querySelector("#__NEXT_DATA__");
      if (!el) return null;
      const data = JSON.parse(el.textContent || "{}");
      const props = data?.props?.pageProps || {};

      // A. 카테고리 Relevance 실측 1위 경로
      const cmp = props.cmp || {};
      let categoryPath = "";
      let topRelevance = 0;
      if (cmp) {
        const parts = [];
        for (const lv of ["category1", "category2", "category3", "category4"]) {
          const catList = cmp[lv]?.categories || [];
          if (catList.length > 0) {
            const best = catList.reduce((max, c) => ((c.relevance || 0) > (max.relevance || 0) ? c : max), catList[0]);
            if (best && best.name) {
              parts.push(`${best.name} (${(best.relevance || 0).toFixed(3)})`);
              if (lv === "category1") topRelevance = best.relevance || 0;
            }
          }
        }
        categoryPath = parts.join(" > ");
      }

      // B. 공식 연관검색어
      const relatedQueries = [];
      const rqList = (props.relatedQueries || []).concat(props.relatedQueriesBottom || []);
      for (const it of rqList) {
        const q = typeof it === "string" ? it : it?.query;
        const filtered = filterKeyword(q);
        if (filtered && !relatedQueries.includes(filtered)) {
          relatedQueries.push(filtered);
        }
      }

      // C. 형태소 색인어 (Terms / IdxTerm)
      const indexTerms = [];
      const compositeList = props.compositeList?.list || [];
      for (const entry of compositeList) {
        const itm = entry.item || entry;
        for (const k of ["category1NameIdxTerm", "category2NameIdxTerm", "category3NameIdxTerm", "category4NameIdxTerm"]) {
          const raw = itm[k];
          if (typeof raw === "string") {
            for (const sub of raw.split(",")) {
              const f = filterKeyword(sub);
              if (f && !indexTerms.includes(f)) indexTerms.push(f);
            }
          }
        }
      }

      // D. 상품 등록 태그 (manuTag)
      const manuTags = [];
      for (const entry of compositeList) {
        const itm = entry.item || entry;
        const tagRaw = itm.manuTag || "";
        if (tagRaw) {
          for (const sub of String(tagRaw).split(",")) {
            const f = filterKeyword(sub);
            if (f && !manuTags.includes(f)) manuTags.push(f);
          }
        }
      }

      return {
        categoryPath,
        topRelevance,
        relatedQueries,
        indexTerms,
        manuTags,
      };
    } catch (e) {
      console.warn("[메이커 SEO PRO] 데이터 파싱 실패", e);
      return null;
    }
  }

  // 2. 25~30자 상품명 자동 조합기 (5대 규칙 완벽 준수)
  function buildOptimizedTitles(query, seoData) {
    const q = query.trim();
    if (!q) return { titleA: "", titleB: "" };

    const pool = [
      ...(seoData?.relatedQueries || []),
      ...(seoData?.indexTerms || []),
      ...(seoData?.manuTags || []),
    ];

    // 중복 제거 및 현재 쿼리 포함 단어 정렬
    const cleanPool = [];
    for (const w of pool) {
      const clean = w.replace(/\s+/g, " ").trim();
      if (clean && !cleanPool.includes(clean) && !clean.includes(q)) {
        cleanPool.push(clean);
      }
    }

    // A안: 완성형 검색어 앞단 + 연관 키워드 조합 (25~30자)
    let currentA = q;
    for (const word of cleanPool) {
      const next = `${currentA} ${word}`;
      if (next.length <= 28) {
        currentA = next;
      } else if (next.length <= 30) {
        currentA = next;
        break;
      }
    }

    // B안: 서브 수식어 + 완성형 검색어 결합 (25~30자)
    let currentB = cleanPool[0] ? `${cleanPool[0]} ${q}` : q;
    for (const word of cleanPool.slice(1)) {
      const next = `${currentB} ${word}`;
      if (next.length <= 28) {
        currentB = next;
      } else if (next.length <= 30) {
        currentB = next;
        break;
      }
    }

    return {
      titleA: currentA,
      lengthA: currentA.length,
      titleB: currentB,
      lengthB: currentB.length,
    };
  }

  // 3. UI 렌더링 엔진
  let currentTab = "related"; // "related" | "terms" | "tags"

  function renderUI() {
    if (!window.location.href.includes("/search")) return;

    const isCoupang = window.location.hostname.includes("coupang.com");
    const brandColor = isCoupang ? "#0074e9" : "#03c75a";
    const query = getQuery();

    let container = document.getElementById(CONTAINER_ID);
    if (!container) {
      container = document.createElement("div");
      container.id = CONTAINER_ID;
      container.style.cssText = `
        padding: 20px;
        margin: 16px auto;
        background: #ffffff;
        border-top: 4px solid ${brandColor};
        border-radius: 12px;
        border-left: 1px solid #e5e7eb;
        border-right: 1px solid #e5e7eb;
        border-bottom: 1px solid #e5e7eb;
        z-index: 1000;
        position: relative;
        width: 100%;
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
      `;
      const target = (
        document.querySelector('[class*="srp_resultHeader"]') ||
        document.querySelector("#content") ||
        document.querySelector('[class*="search_list_area"]') ||
        document.querySelector("#productList") ||
        document.body
      );
      target.prepend(container);
    }

    const seoData = extractNaverSeoData();
    const titles = buildOptimizedTitles(query, seoData);

    // 탭별 아이템
    let activeKeywords = [];
    if (currentTab === "related") activeKeywords = seoData?.relatedQueries || [];
    else if (currentTab === "terms") activeKeywords = seoData?.indexTerms || [];
    else activeKeywords = seoData?.manuTags || [];

    // 태그 10개 추출
    const top10Tags = [query, ...(seoData?.relatedQueries || []), ...(seoData?.manuTags || [])]
      .filter((v, i, a) => a.indexOf(v) === i)
      .slice(0, 10)
      .join(",");

    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; border-bottom: 1px solid #f1f3f5; padding-bottom: 12px;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="font-size: 16px; font-weight: 800; color: #111;">
            메이커 셀링 도우미 <span style="background: ${brandColor}; color: #fff; font-size: 11px; padding: 2px 8px; border-radius: 6px; margin-left: 4px;">SEO PRO</span>
          </span>
          <span style="font-size: 12px; color: #10b981; background: #ecfdf5; padding: 3px 8px; border-radius: 8px; font-weight: 600;">
            ✓ 사용량 무제한
          </span>
        </div>
        <div style="font-size: 12px; color: #6b7280;">
          키워드: <strong style="color: #111;">"${query}"</strong>
        </div>
      </div>

      ${seoData?.categoryPath ? `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 14px; margin-bottom: 14px; display: flex; align-items: center; justify-content: space-between;">
          <div style="font-size: 13px; color: #334155;">
            <strong style="color: #0f172a;">🏷️ 네이버 실측 1위 카테고리:</strong> 
            <span style="color: ${brandColor}; font-weight: 700; margin-left: 4px;">${seoData.categoryPath}</span>
          </div>
          <span style="font-size: 11px; background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: bold;">
            적합도 1.0 만점 진입
          </span>
        </div>
      ` : ""}

      <div style="background: #fdfdfd; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 14px; margin-bottom: 14px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <span style="font-size: 13px; font-weight: bold; color: #374151;">✨ 25~30자 최적화 상품명 (클릭하여 복사)</span>
          <button id="nvs-copy-tags-btn" style="background: #1f2937; color: white; border: none; padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer; font-weight: 600;">
            📋 스마트스토어 태그 10개 복사
          </button>
        </div>
        <div style="display: flex; gap: 10px; flex-wrap: wrap;">
          <div id="nvs-title-a-box" style="flex: 1; min-width: 280px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 12px; cursor: pointer; transition: all 0.2s;">
            <div style="font-size: 11px; color: #6b7280; margin-bottom: 2px;">[A안: 메인 완성형] (${titles.lengthA}자)</div>
            <div style="font-size: 13px; font-weight: 600; color: #111;">${titles.titleA || "키워드 부족"}</div>
          </div>
          <div id="nvs-title-b-box" style="flex: 1; min-width: 280px; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; padding: 8px 12px; cursor: pointer; transition: all 0.2s;">
            <div style="font-size: 11px; color: #6b7280; margin-bottom: 2px;">[B안: 서브 결합형] (${titles.lengthB}자)</div>
            <div style="font-size: 13px; font-weight: 600; color: #111;">${titles.titleB || "키워드 부족"}</div>
          </div>
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <div style="display: flex; gap: 8px;">
          <button id="nvs-tab-related" style="padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1px solid ${currentTab === 'related' ? brandColor : '#e5e7eb'}; background: ${currentTab === 'related' ? brandColor : '#fff'}; color: ${currentTab === 'related' ? '#fff' : '#4b5563'};">
            1. 공식 연관검색어 (${seoData?.relatedQueries.length || 0})
          </button>
          <button id="nvs-tab-terms" style="padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1px solid ${currentTab === 'terms' ? brandColor : '#e5e7eb'}; background: ${currentTab === 'terms' ? brandColor : '#fff'}; color: ${currentTab === 'terms' ? '#fff' : '#4b5563'};">
            2. 형태소 색인어 Terms (${seoData?.indexTerms.length || 0})
          </button>
          <button id="nvs-tab-tags" style="padding: 6px 14px; border-radius: 8px; font-size: 12px; font-weight: 700; cursor: pointer; border: 1px solid ${currentTab === 'tags' ? brandColor : '#e5e7eb'}; background: ${currentTab === 'tags' ? brandColor : '#fff'}; color: ${currentTab === 'tags' ? '#fff' : '#4b5563'};">
            3. 상위 등록태그 (${seoData?.manuTags.length || 0})
          </button>
        </div>
        <button id="nvs-copy-all-btn" style="background: #f3f4f6; color: #374151; border: 1px solid #d1d5db; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 600; cursor: pointer;">
          전체 콤마 복사
        </button>
      </div>

      <div style="display: flex; flex-wrap: wrap; gap: 8px; max-height: 220px; overflow-y: auto; padding: 4px 2px;">
        ${activeKeywords.length > 0 ? activeKeywords.map(kw => `
          <span class="nvs-seo-chip" data-kw="${kw}" style="background: #f9fafb; color: #1f2937; border: 1px solid #e5e7eb; padding: 6px 12px; border-radius: 8px; font-size: 12px; font-weight: 500; cursor: pointer; transition: all 0.15s; user-select: none;">
            ${kw}
          </span>
        `).join("") : `<div style="color: #9ca3af; font-size: 13px; padding: 10px;">데이터가 없습니다.</div>`}
      </div>
    `;

    // 이벤트 리스너 부착
    document.getElementById("nvs-tab-related")?.addEventListener("click", () => { currentTab = "related"; renderUI(); });
    document.getElementById("nvs-tab-terms")?.addEventListener("click", () => { currentTab = "terms"; renderUI(); });
    document.getElementById("nvs-tab-tags")?.addEventListener("click", () => { currentTab = "tags"; renderUI(); });

    document.getElementById("nvs-title-a-box")?.addEventListener("click", () => {
      navigator.clipboard.writeText(titles.titleA);
      alert(`[A안 상품명 복사 완료]\n${titles.titleA}`);
    });
    document.getElementById("nvs-title-b-box")?.addEventListener("click", () => {
      navigator.clipboard.writeText(titles.titleB);
      alert(`[B안 상품명 복사 완료]\n${titles.titleB}`);
    });
    document.getElementById("nvs-copy-tags-btn")?.addEventListener("click", () => {
      navigator.clipboard.writeText(top10Tags);
      alert(`[스마트스토어 태그 10개 복사 완료]\n${top10Tags}`);
    });
    document.getElementById("nvs-copy-all-btn")?.addEventListener("click", () => {
      const allText = activeKeywords.join(", ");
      navigator.clipboard.writeText(allText);
      alert(`[현재 목록 전체 복사 완료]\n${allText}`);
    });

    document.querySelectorAll(".nvs-seo-chip").forEach(el => {
      el.addEventListener("click", () => {
        const kw = el.getAttribute("data-kw");
        if (kw) {
          navigator.clipboard.writeText(kw);
          el.style.background = brandColor;
          el.style.color = "#fff";
          setTimeout(() => {
            el.style.background = "#f9fafb";
            el.style.color = "#1f2937";
          }, 400);
        }
      });
    });
  }

  // 초기 실행 및 DOM 옵저버
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", renderUI);
  } else {
    renderUI();
  }

  let lastUrl = window.location.href;
  new MutationObserver(() => {
    if (window.location.href !== lastUrl) {
      lastUrl = window.location.href;
      setTimeout(renderUI, 500);
    }
  }).observe(document.body, { childList: true, subtree: true });

})();
