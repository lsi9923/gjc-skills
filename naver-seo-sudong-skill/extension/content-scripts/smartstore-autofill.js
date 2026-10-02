/**
 * 메이커 셀링 도우미 × 네이버 SEO PRO
 * 스마트스토어 센터 (sell.smartstore.naver.com) 상품등록 Auto-fill 브릿지
 */
(function () {
  "use strict";

  if (!window.location.hostname.includes("sell.smartstore.naver.com")) {
    return;
  }

  const PANEL_ID = "seo-pro-autofill-panel";
  const TOGGLE_BTN_ID = "seo-pro-autofill-toggle";

  let parsedPayload = null;

  // 1. 플로팅 토글 버튼 생성
  function createToggleBtn() {
    if (document.getElementById(TOGGLE_BTN_ID)) return;

    const btn = document.createElement("button");
    btn.id = TOGGLE_BTN_ID;
    btn.innerHTML = "⚡ SEO PRO Auto-fill";
    btn.style.cssText = `
      position: fixed;
      top: 140px;
      right: 24px;
      z-index: 999999;
      background: linear-gradient(135deg, #03c75a 0%, #029a46 100%);
      color: #ffffff;
      border: none;
      border-radius: 24px;
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 700;
      box-shadow: 0 4px 16px rgba(3, 199, 90, 0.35);
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s ease;
    `;

    btn.addEventListener("mouseenter", () => {
      btn.style.transform = "scale(1.05)";
      btn.style.boxShadow = "0 6px 20px rgba(3, 199, 90, 0.45)";
    });
    btn.addEventListener("mouseleave", () => {
      btn.style.transform = "scale(1)";
      btn.style.boxShadow = "0 4px 16px rgba(3, 199, 90, 0.35)";
    });

    btn.addEventListener("click", togglePanel);
    document.body.appendChild(btn);
  }

  // 2. 패널 토글
  function togglePanel() {
    const panel = document.getElementById(PANEL_ID);
    if (!panel) {
      renderPanel();
    } else {
      panel.style.display = panel.style.display === "none" ? "block" : "none";
    }
  }

  // 3. 패널 UI 렌더링
  function renderPanel() {
    let panel = document.getElementById(PANEL_ID);
    if (panel) return;

    panel = document.createElement("div");
    panel.id = PANEL_ID;
    panel.style.cssText = `
      position: fixed;
      top: 190px;
      right: 24px;
      width: 440px;
      max-height: 80vh;
      overflow-y: auto;
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
      z-index: 999999;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      color: #1f2937;
      display: flex;
      flex-direction: column;
    `;

    panel.innerHTML = `
      <div style="background: #03c75a; color: #fff; padding: 12px 16px; border-radius: 12px 12px 0 0; display: flex; justify-content: space-between; align-items: center;">
        <span style="font-weight: 700; font-size: 14px;">⚡ 스마트스토어 AI Auto-fill 브릿지</span>
        <button id="seo-pro-close-btn" style="background: none; border: none; color: #fff; font-size: 18px; cursor: pointer;">&times;</button>
      </div>

      <div style="padding: 16px; display: flex; flex-direction: column; gap: 12px;">
        <div style="font-size: 12px; color: #6b7280; line-height: 1.4;">
          에이전트가 출력한 <b>SmartStoreListingPayload</b> JSON 또는 텍스트를 붙여넣으세요.
        </div>

        <div style="display: flex; gap: 8px;">
          <button id="seo-pro-paste-clipboard" style="flex: 1; padding: 8px 12px; background: #f3f4f6; border: 1px solid #d1d5db; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">
            📋 클립보드에서 불러오기
          </button>
          <button id="seo-pro-apply-autofill" style="flex: 1; padding: 8px 12px; background: #03c75a; color: #fff; border: none; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
            🚀 원클릭 폼 자동입력
          </button>
        </div>

        <textarea id="seo-pro-json-input" placeholder="여기에 JSON을 붙여넣으세요..." style="width: 100%; height: 100px; padding: 8px; font-size: 11px; border: 1px solid #d1d5db; border-radius: 6px; resize: vertical; box-sizing: border-box; font-family: monospace;"></textarea>

        <div id="seo-pro-preview-section" style="display: none; border-top: 1px solid #e5e7eb; padding-top: 12px; font-size: 12px;">
          <div style="font-weight: 700; margin-bottom: 8px; color: #111827;">인식된 데이터 항목 (클릭 시 개별 복사)</div>
          <div id="seo-pro-field-list" style="display: flex; flex-direction: column; gap: 6px;"></div>
        </div>

        <div id="seo-pro-status-msg" style="display: none; padding: 8px 12px; border-radius: 6px; font-size: 12px; font-weight: 600;"></div>
      </div>
    `;

    document.body.appendChild(panel);

    document.getElementById("seo-pro-close-btn").addEventListener("click", () => {
      panel.style.display = "none";
    });

    document.getElementById("seo-pro-paste-clipboard").addEventListener("click", async () => {
      try {
        const text = await navigator.clipboard.readText();
        document.getElementById("seo-pro-json-input").value = text;
        parseAndPreview(text);
      } catch (err) {
        showStatus("클립보드 접근 권한이 필요합니다. 아래 입력창에 직접 붙여넣으세요.", "warning");
      }
    });

    document.getElementById("seo-pro-json-input").addEventListener("input", (e) => {
      parseAndPreview(e.target.value);
    });

    document.getElementById("seo-pro-apply-autofill").addEventListener("click", () => {
      const text = document.getElementById("seo-pro-json-input").value;
      const data = parseAndPreview(text);
      if (data) {
        executeAutofill(data);
      } else {
        showStatus("유효한 JSON 데이터를 입력해주세요.", "error");
      }
    });
  }

  // 4. 데이터 파싱 및 프리뷰 렌더링
  function parseAndPreview(rawText) {
    const previewSec = document.getElementById("seo-pro-preview-section");
    const fieldList = document.getElementById("seo-pro-field-list");
    if (!rawText || !rawText.trim()) {
      previewSec.style.display = "none";
      return null;
    }

    let json = null;
    try {
      json = JSON.parse(rawText.trim());
    } catch {
      // 텍스트 내에서 JSON 블록 탐색
      const match = rawText.match(/\{[\s\S]*\}/);
      if (match) {
        try {
          json = JSON.parse(match[0]);
        } catch {}
      }
    }

    if (!json || typeof json !== "object") {
      previewSec.style.display = "none";
      return null;
    }

    parsedPayload = json;
    previewSec.style.display = "block";
    fieldList.innerHTML = "";

    const fields = [
      { label: "카테고리", key: "category", val: json.category },
      { label: "상품명", key: "productName", val: json.productName },
      { label: "판매가", key: "salePrice", val: json.salePrice ? `${Number(json.salePrice).toLocaleString()}원` : null },
      { label: "재고수량", key: "stockQuantity", val: json.stockQuantity },
      { label: "태그(10개)", key: "tags", val: Array.isArray(json.tags) ? json.tags.join(", ") : null },
      { label: "원산지", key: "origin", val: json.origin || "중국" },
      { label: "배송비", key: "shipping", val: json.shipping?.fee ? `${Number(json.shipping.fee).toLocaleString()}원` : null },
    ];

    fields.forEach((f) => {
      if (!f.val) return;
      const item = document.createElement("div");
      item.style.cssText = `
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: #f9fafb;
        padding: 6px 8px;
        border-radius: 4px;
        border: 1px solid #f3f4f6;
      `;
      item.innerHTML = `
        <span style="font-weight: 600; color: #4b5563;">${f.label}:</span>
        <span style="color: #111827; max-width: 240px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${f.val}</span>
        <button style="background: #e5e7eb; border: none; border-radius: 4px; padding: 2px 6px; font-size: 11px; cursor: pointer;">복사</button>
      `;

      item.querySelector("button").addEventListener("click", () => {
        const copyText = typeof f.val === "string" ? f.val : String(json[f.key] || "");
        navigator.clipboard.writeText(copyText);
        showStatus(`${f.label} 값이 클립보드에 복사되었습니다.`, "success");
      });

      fieldList.appendChild(item);
    });

    return json;
  }

  // 5. DOM 폼 자동입력 (Auto-fill) 엔진
  function executeAutofill(payload) {
    let successCount = 0;

    // A. 상품명 입력
    const nameInput = document.querySelector('input[name="name"], input[placeholder*="상품명"], input[id*="productName"]');
    if (nameInput && payload.productName) {
      setInputValue(nameInput, payload.productName);
      successCount++;
    }

    // B. 판매가 입력
    const priceInput = document.querySelector('input[name="salePrice"], input[placeholder*="판매가"], input[id*="salePrice"]');
    if (priceInput && payload.salePrice) {
      setInputValue(priceInput, String(payload.salePrice));
      successCount++;
    }

    // C. 재고수량 입력
    const stockInput = document.querySelector('input[name="stockQuantity"], input[placeholder*="재고수량"], input[id*="stockQuantity"]');
    if (stockInput && payload.stockQuantity) {
      setInputValue(stockInput, String(payload.stockQuantity));
      successCount++;
    }

    // D. 태그 자동입력 시도
    const tagInput = document.querySelector('input[placeholder*="태그"], input[id*="tag"]');
    if (tagInput && Array.isArray(payload.tags)) {
      payload.tags.forEach((tag) => {
        setInputValue(tagInput, tag);
        tagInput.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", keyCode: 13, bubbles: true }));
      });
      successCount++;
    }

    showStatus(
      `Auto-fill 완료! ${successCount}개 주요 필드가 자동 입력되었습니다. (입력되지 않은 항목은 패널의 [복사] 버튼으로 즉시 붙여넣으세요.)`,
      "success"
    );
  }

  // React/Vue Controlled Input 대응 트리거
  function setInputValue(el, value) {
    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
    if (nativeInputValueSetter) {
      nativeInputValueSetter.call(el, value);
    } else {
      el.value = value;
    }
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
  }

  // 상태 메시지 노출
  function showStatus(msg, type) {
    const box = document.getElementById("seo-pro-status-msg");
    if (!box) return;
    box.textContent = msg;
    box.style.display = "block";
    if (type === "success") {
      box.style.background = "#def7ec";
      box.style.color = "#03543f";
    } else if (type === "error") {
      box.style.background = "#fde8e8";
      box.style.color = "#9b1c1c";
    } else {
      box.style.background = "#fef08a";
      box.style.color = "#713f12";
    }
    setTimeout(() => {
      box.style.display = "none";
    }, 5000);
  }

  // 초기화 (DOM 로드 후 버튼 주입)
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", createToggleBtn);
  } else {
    createToggleBtn();
  }
})();
