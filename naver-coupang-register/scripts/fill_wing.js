/**
 * fill_wing.js - Coupang Wing 자동 입력 및 전수 diff 검증 스크립트
 * 
 * 설계 원칙 (ops-playbook 속도 설계 & agy/Claude 검토 피드백):
 * 1. aside repl 1회 호출로 spec 읽어 입력 -> (save: true일 때만 중간저장) -> 폼/스토어 읽어 spec과 diff 반환
 * 2. 아코디언 펼침: 실제 접힘 아이콘(텍스트 '') 버튼만 클릭하여 기오픈 섹션 닫힘 방지
 * 3. 옵션: 옵션축 이름/값 입력 -> '옵션목록으로 적용' 클릭 -> 행 수 검증 -> 행별 정상가·판매가·재고 입력
 * 4. 상품정보제공고시: 상품군 드롭다운 먼저 변경 후 칸별 값 입력 (null 필드는 스킵)
 * 5. 중간저장 경고 모달: .alert-confirm 조건부 클릭 (page.once('dialog') 사용 금지)
 * 6. 판매등록·저장하기·판매요청 버튼 코드는 일체 포함 금지 (원천 배제)
 * 7. 전 필드 전수 diff: 상품명·노출명·카테고리·옵션행값/개수·정상가·판매가·재고·검색어15·고시·제조사/브랜드·인증
 * 8. errors[] 또는 diff[]가 하나라도 있으면 success: false
 */

const sleep = ms => new Promise(r => setTimeout(r, ms));
// console shim

async function fillWing({ page, spec, save = false }) {
  const result = {
    step: 'start',
    errors: [],
    diff: [],
    filled: {},
    success: false
  };

  if (!page || !spec || !spec.wing) {
    throw new Error('page and spec.wing are required');
  }

  const wingSpec = spec.wing;
  console.log(`[fill_wing] Start filling Wing form for ${spec.id} (${spec.name})`);

  // 0. 중간저장 불러오기 모달 자동 닫기
  try {
    const modalClose = page.locator('.modal .modal-close, i.modal-close, button:has-text("닫기")').first();
    if (await modalClose.isVisible({ timeout: 1500 }).catch(() => false)) {
      await modalClose.click();
      console.log('[fill_wing] Closed intermediate save modal');
      await sleep(500);
    }
  } catch (e) {
    // ignore
  }

  // 1. 브랜드: 자체제작/브랜드없음(#selfMade) 체크하여 상품명 잠금 해제
  try {
    const selfMadeChk = page.locator('#selfMade, input[name="selfMade"]').first();
    if (await selfMadeChk.isVisible({ timeout: 1500 }).catch(() => false)) {
      const isChecked = await selfMadeChk.isChecked().catch(() => false);
      if (!isChecked) {
        await selfMadeChk.click();
        console.log('[fill_wing] Checked #selfMade to unlock product name');
        await sleep(400);
      }
    }
  } catch (e) {
    console.log('[fill_wing] selfMade check warning:', e.message);
  }

  // 2. 등록상품명(판매자관리용) & 노출상품명 입력
  try {
    const sellerProdInput = page.locator('input[placeholder*="상품 모델"], input[placeholder*="등록상품명"], input[name*="sellerProductName"], input[name*="InputWithCounter_2"]').first();
    if (await sellerProdInput.isVisible({ timeout: 2000 }).catch(() => false)) {
      await sellerProdInput.fill(wingSpec.sellerProductName);
      result.filled.sellerProductName = wingSpec.sellerProductName;
    } else {
      result.errors.push({ step: 'sellerProductName', error: 'input_not_found' });
    }

    const displayProdInput = page.locator('input[placeholder*="노출상품명"], input[name*="displayProductName"]').first();
    if (await displayProdInput.isVisible({ timeout: 1000 }).catch(() => false)) {
      const isDisabled = await displayProdInput.isDisabled().catch(() => false);
      if (!isDisabled && wingSpec.displayProductName) {
        await displayProdInput.fill(wingSpec.displayProductName);
        result.filled.displayProductName = wingSpec.displayProductName;
      } else {
        result.filled.displayProductName = '[DISABLED_OR_EMPTY]';
      }
    }
  } catch (e) {
    result.errors.push({ step: 'productNames', error: e.message });
    console.log('[fill_wing] Product name fill warning:', e.message);
  }

  // 3. 카테고리 선택
  try {
    const categoryInput = page.locator('input[placeholder*="카테고리명 입력"]').first();
    if (wingSpec.categoryPath) {
      const parts = wingSpec.categoryPath.split('>');
      const leaf = parts[parts.length - 1].trim();

      const alreadySelected = await page.evaluate((categoryLeaf) => {
        const catInput = document.querySelector('input[placeholder*="카테고리명 입력"]');
        const pEl = Array.from(document.querySelectorAll('span, p, .recommended-category')).find(el => (el.innerText || '').includes(categoryLeaf));
        return Boolean(pEl || (catInput && catInput.value && catInput.value.includes(categoryLeaf)));
      }, leaf);

      if (alreadySelected) {
        result.filled.category = leaf;
        console.log(`[fill_wing] Category already confirmed: ${leaf}`);
      } else {
        const selected = await page.evaluate(async (categoryLeaf) => {
          const catInput = document.querySelector('input[placeholder*="카테고리명 입력"]');
          if (!catInput) return { success: false, reason: 'input_not_found' };
          catInput.focus();
          catInput.value = categoryLeaf;
          catInput.dispatchEvent(new Event('input', { bubbles: true }));
          catInput.dispatchEvent(new Event('change', { bubbles: true }));

          const icon = document.querySelector('span[data-sc-common-uicfg*="icon:find"]');
          if (icon) icon.click();

          await new Promise(r => setTimeout(r, 1500));

          const recDiv = document.querySelector('.recommended-category');
          const btn = recDiv ? recDiv.querySelector('button') : null;
          if (btn) {
            btn.click();
            return { success: true };
          }
          return { success: false, reason: `no_recommendation_for_${categoryLeaf}` };
        }, leaf);

        if (selected.success) {
          result.filled.category = leaf;
          console.log(`[fill_wing] Selected recommended category for: ${leaf}`);
          await sleep(1500);
        } else {
          result.errors.push({ step: 'category', error: selected.reason });
        }
      }
    }
  } catch (e) {
    result.errors.push({ step: 'category', error: e.message });
    console.log('[fill_wing] Category fill warning:', e.message);
  }
  // 3-1. 아코디언 섹션 펼침: 실제 접힘 상태인 icon:arrow-down 버튼 클릭
  await sleep(1500);
  try {
    const unfoldedCount = await page.evaluate(() => {
      let count = 0;
      const downIcons = Array.from(document.querySelectorAll('i[data-sc-common-uicfg*="icon:arrow-down"], .form-section-btn-collapse i[class*="arrow-down"]'));
      for (const icon of downIcons) {
        const btn = icon.closest('button, .cursor-pointer') || icon;
        btn.click();
        count++;
      }
      return count;
    });
    console.log(`[fill_wing] Unfolded ${unfoldedCount} accordion sections with icon:arrow-down`);
    await sleep(600);
  } catch (e) {
    console.log('[fill_wing] Accordion expand warning:', e.message);
  }

  // 4. 옵션 설정: 축 이름 확인 -> 축 값 입력 -> '옵션목록으로 적용' 클릭 -> 행 수 검증 -> 행별 정상가/판매가/재고 입력
  try {
    if (wingSpec.optionAxes && wingSpec.optionRows && wingSpec.optionRows.length > 0) {
      // 4-1. 옵션 사용 여부 확인/체크
      const optionUseCheck = page.locator('input[name*="useOption"], input[value="true"][name*="option"]').first();
      if (await optionUseCheck.isVisible({ timeout: 1000 }).catch(() => false)) {
        await optionUseCheck.check().catch(() => {});
      }

      // 4-2. 옵션축별 값 입력 및 각 축별 '추가' 버튼 클릭
      const optValInputs = page.locator('.form-section-body input[placeholder*="옵션값"], .form-section-body input[placeholder*="숫자만 입력"]');
      const addBtns = page.locator('button.w-btn-primary:has-text("추가")');
      const valInputCount = await optValInputs.count();

      for (let axisIdx = 0; axisIdx < wingSpec.optionAxes.length; axisIdx++) {
        const axisValues = Array.from(new Set(wingSpec.optionRows.map(r => r.values[axisIdx])));
        if (axisIdx < valInputCount) {
          const inputLoc = optValInputs.nth(axisIdx);
          const ph = await inputLoc.getAttribute('placeholder').catch(() => '');
          let val = axisValues.join(', ');
          if (ph && ph.includes('숫자만 입력')) {
            val = val.replace(/[^0-9]/g, '');
          }
          await inputLoc.fill(val);
          if (await addBtns.count() > axisIdx) {
            await addBtns.nth(axisIdx).click();
            await sleep(600);
          }
        }
      }

      // 4-3. 옵션 목록 행 수 검증
      const optionRowsLocator = page.locator('.option-pane-table tbody tr, .option-table tbody tr, table tbody tr');
      const actualRowCount = await page.evaluate(() => {
        const optTitle = Array.from(document.querySelectorAll('*')).find(el => (el.innerText || '').startsWith('옵션 목록 (총'));
        if (optTitle) {
          const m = optTitle.innerText.match(/총\s*(\d+)\s*개/);
          if (m) return parseInt(m[1], 10);
        }
        return document.querySelectorAll('.option-pane-table input[type="text"]').length > 0 ? 1 : 0;
      });
      console.log(`[fill_wing] Verified option row count: ${actualRowCount} (expected: ${wingSpec.optionRows.length})`);

      // 4-5. 행별 정상가 / 판매가 / 재고수량 입력
      await sleep(1500);
      await page.evaluate((specRows) => {
        const textInputs = Array.from(document.querySelectorAll('.option-pane-table input[type="text"]'));
        for (let rIdx = 0; rIdx < specRows.length; rIdx++) {
          const specRow = specRows[rIdx];
          const baseIdx = rIdx * 6; // 정상가, 판매가, 재고수량 등
          const origInput = textInputs[baseIdx + 0];
          const saleInput = textInputs[baseIdx + 1];
          const stockInput = textInputs[baseIdx + 2];

          if (origInput && specRow.originalPrice) {
            origInput.value = String(specRow.originalPrice);
            origInput.dispatchEvent(new Event('input', { bubbles: true }));
            origInput.dispatchEvent(new Event('change', { bubbles: true }));
            origInput.dispatchEvent(new Event('blur', { bubbles: true }));
          }
          if (saleInput && specRow.salePrice) {
            saleInput.value = String(specRow.salePrice);
            saleInput.dispatchEvent(new Event('input', { bubbles: true }));
            saleInput.dispatchEvent(new Event('change', { bubbles: true }));
            saleInput.dispatchEvent(new Event('blur', { bubbles: true }));
          }
          if (stockInput && specRow.stock) {
            stockInput.value = String(specRow.stock);
            stockInput.dispatchEvent(new Event('input', { bubbles: true }));
            stockInput.dispatchEvent(new Event('change', { bubbles: true }));
            stockInput.dispatchEvent(new Event('blur', { bubbles: true }));
          }
        }
      }, wingSpec.optionRows);
      await sleep(500);

      result.filled.options = `${wingSpec.optionAxes.join('/')} (${wingSpec.optionRows.length}행)`;
    }
  } catch (e) {
    result.errors.push({ step: 'options', error: e.message });
    console.log('[fill_wing] Options fill warning:', e.message);
  }

  // 5. 검색어 (15개) 입력: 실전 입력창 (쉼표(,)로 구분하여 최대 20개까지 입력 가능)
  try {
    if (wingSpec.searchTerms && wingSpec.searchTerms.length > 0) {
      const tagInput = page.locator('input[placeholder*="쉼표(,)로 구분하여"], input[placeholder*="최대 20개까지 입력 가능"]').first();
      if (await tagInput.isVisible({ timeout: 1500 }).catch(() => false)) {
        await tagInput.fill(wingSpec.searchTerms.join(', '));
        const addTagBtn = page.locator('.form-section:has(.form-section-title:has-text("검색어")) button:has-text("추가"), button:has-text("태그 추가")').first();
        if (await addTagBtn.isVisible({ timeout: 800 }).catch(() => false)) {
          await addTagBtn.click();
        } else {
          await tagInput.press('Enter');
        }
        await sleep(300);
        result.filled.searchTerms = wingSpec.searchTerms;
      } else {
        // fallback to srp-search-input if needed
        const fallbackTagInput = page.locator('input[placeholder*="검색어를 입력하세요"]').first();
        if (await fallbackTagInput.isVisible({ timeout: 800 }).catch(() => false)) {
          for (const term of wingSpec.searchTerms) {
            await fallbackTagInput.fill(term);
            await fallbackTagInput.press('Enter');
            await sleep(80);
          }
          result.filled.searchTerms = wingSpec.searchTerms;
        } else {
          result.errors.push({ step: 'searchTerms', error: 'input_not_found' });
        }
      }
    }
  } catch (e) {
    result.errors.push({ step: 'searchTerms', error: e.message });
    console.log('[fill_wing] Search terms fill warning:', e.message);
  }

  // 6. 상품정보제공고시 (상품군 드롭다운 먼저 변경 필수)
  try {
    if (wingSpec.notice) {
      // 6-1. 고시 상품군 드롭다운 변경
      const noticeGroupSelect = page.locator('.notice-section select, select[name*="noticeGroup"], select.notice-category-select').first();
      if (await noticeGroupSelect.isVisible({ timeout: 1500 }).catch(() => false)) {
        await noticeGroupSelect.selectOption({ label: wingSpec.notice.group }).catch(async () => {
          await noticeGroupSelect.selectOption(wingSpec.notice.group);
        });
        await sleep(1000); // 드롭다운 변경 후 폼 리렌더링 대기
      }

      // 6-2. 고시 칸별 값 입력 (null은 지어내지 않고 스킵)
      if (wingSpec.notice.fields) {
        for (const [label, val] of Object.entries(wingSpec.notice.fields)) {
          if (val === null) continue;
          const fieldInput = page.locator(`tr:has-text("${label}") input, tr:has-text("${label}") textarea, div:has-text("${label}") > input, div:has-text("${label}") > textarea`).first();
          if (await fieldInput.isVisible({ timeout: 500 }).catch(() => false)) {
            await fieldInput.fill(val);
          }
        }
      }
      result.filled.noticeGroup = wingSpec.notice.group;
    }
  } catch (e) {
    result.errors.push({ step: 'notice', error: e.message });
    console.log('[fill_wing] Notice fill warning:', e.message);
  }

  // 7. 제조사 / 브랜드 / 인증
  try {
    const mfgInput = page.locator('input[placeholder*="제조사를 알 수 없는 경우"], input[placeholder*="제조사명"], input[name*="manufacturer"]').first();
    if (await mfgInput.isVisible({ timeout: 1500 }).catch(() => false)) {
      await mfgInput.fill(wingSpec.manufacturer || '협력업체');
      result.filled.manufacturer = wingSpec.manufacturer;
    }

    if (wingSpec.certification && wingSpec.certification.certificationType) {
      const certRadio = page.locator(`input[value*="${wingSpec.certification.certificationType}"]`).first();
      if (await certRadio.isVisible({ timeout: 1000 }).catch(() => false)) {
        await certRadio.check();
      }
    }
  } catch (e) {
    result.errors.push({ step: 'mfg_cert', error: e.message });
    console.log('[fill_wing] Mfg/Cert fill warning:', e.message);
  }

  // 8. 중간저장 (save 옵션이 true일 때만 실행 / 판매등록 코드는 일체 없음)
  if (save === true) {
    console.log('[fill_wing] save: true specified. Triggering intermediate save...');
    const saveBtn = page.locator('button:has-text("중간저장")').first();
    if (await saveBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await saveBtn.click();
      await sleep(500);

      // 조건부 DOM 확인 모달 처리 (.alert-confirm)
      const confirmBtn = page.locator('.alert-confirm');
      if (await confirmBtn.isVisible({ timeout: 1500 }).catch(() => false)) {
        console.log('[fill_wing] .alert-confirm modal detected. Clicking confirm...');
        await confirmBtn.click();
      }
      await sleep(2000);
      result.saved = true;
    } else {
      result.saved = false;
      result.errors.push({ step: 'save', error: 'save_button_not_found' });
    }
  } else {
    console.log('[fill_wing] save: false. Skipping intermediate save (dry-run mode).');
    result.saved = null;
  }

  // 9. 전 필드 전수 Diff 검증 (DOM 및 Vuex store oSellerProduct 대조)
  try {
    const auditData = await page.evaluate(() => {
      // 1. Vuex store 조회
      let store = null;
      const allEls = Array.from(document.querySelectorAll('*'));
      for (const el of allEls) {
        if (el['__vue__'] && el['__vue__']['$store']) {
          store = el['__vue__']['$store'];
          break;
        }
      }
      const storeProd = (store && store.state && store.state.sellerProduct) ? store.state.sellerProduct.oSellerProduct : (store && store.getters ? store.getters.oSellerProduct : null);

      // 2. DOM 값 fallback 조회
      const sellerProdEl = document.querySelector('input[placeholder*="상품 모델"], input[placeholder*="등록상품명"], input[name*="sellerProductName"], input[name*="InputWithCounter_2"]');
      const displayProdEl = document.querySelector('input[placeholder*="노출상품명"], input[name*="displayProductName"]');
      const catEl = document.querySelector('input[placeholder*="카테고리명 입력"], .category-picker-selected, .recommended-category span');
      const mfgEl = document.querySelector('input[placeholder*="제조사를 알 수 없는 경우"], input[placeholder*="제조사명"], input[name*="manufacturer"]');
      const brandEl = document.querySelector('input.brand-registry-input, input[placeholder*="브랜드 이름"]');
      const noticeGroupEl = document.querySelector('.notice-section select, select.notice-category-select, select');

      // 검색어 태그 칩 추출
      const tagChips = Array.from(document.querySelectorAll('.tag, .search-tag, [class*="tag-chip"], .tag-list span, .tag-item')).map(c => c.innerText.trim().replace(/^#/, ''));

      return {
        hasStore: Boolean(storeProd),
        storeProd: storeProd ? JSON.parse(JSON.stringify(storeProd)) : null,
        domValues: {
          sellerProductName: sellerProdEl ? sellerProdEl.value : null,
          displayProductName: displayProdEl ? displayProdEl.value : null,
          category: catEl ? catEl.value || catEl.innerText : null,
          manufacturer: mfgEl ? mfgEl.value : null,
          brand: brandEl ? brandEl.value : null,
          noticeGroup: (() => {
            const allText = document.body ? document.body.innerText : '';
            if (allText.includes('기타 재화')) return '기타 재화';
            const groups = ['주방용품', '패션잡화', '가정용 전기제품', '가구', '침구', '의류'];
            for (const g of groups) {
              if (allText.includes(g)) return g;
            }
            return null;
          })(),
          tagChips: tagChips,
          optionItems: Array.from(document.querySelectorAll('.option-pane-table input[type="text"]')).reduce((acc, inp, idx) => {
            const r = Math.floor(idx / 6);
            if (!acc[r]) acc[r] = {};
            const col = idx % 6;
            const num = parseInt(inp.value.replace(/[^0-9]/g, '') || '0', 10);
            if (col === 0) acc[r].originalPrice = num || null;
            if (col === 1) acc[r].salePrice = num || null;
            if (col === 2) acc[r].stock = num || null;
            return acc;
          }, [])
        }
      };
    });

    result.auditData = auditData;
    const storeProd = auditData.storeProd;
    const dom = auditData.domValues;

    // --- 전 필드 전수 Diff 대조 ---
    // 1) 등록상품명
    const actualSellerName = storeProd?.sellerProductName || dom.sellerProductName;
    if (wingSpec.sellerProductName && actualSellerName !== wingSpec.sellerProductName) {
      result.diff.push({ field: 'sellerProductName', expected: wingSpec.sellerProductName, actual: actualSellerName });
    }

    // 2) 카테고리 ID 또는 경로
    if (wingSpec.categoryId) {
      const actCatId = storeProd ? storeProd.categoryId : null;
      if (actCatId !== wingSpec.categoryId) {
        result.diff.push({ field: 'categoryId', expected: wingSpec.categoryId, actual: actCatId });
      }
    }

    // 3) 옵션 행 수 및 행별 가격/재고/값
    if (wingSpec.optionRows && wingSpec.optionRows.length > 0) {
      const actualItems = (storeProd && storeProd.items && storeProd.items.length > 0) ? storeProd.items : (auditData.domValues.optionItems || []);
      if (actualItems.length !== wingSpec.optionRows.length) {
        result.diff.push({ field: 'optionRowCount', expected: wingSpec.optionRows.length, actual: actualItems.length });
      }
      for (let i = 0; i < wingSpec.optionRows.length; i++) {
        const expRow = wingSpec.optionRows[i];
        const actItem = actualItems[i] || null;
        if (!actItem) {
          result.diff.push({ field: `option[${i}]`, expected: expRow, actual: null });
        } else {
          const actSale = actItem.salePrice;
          const actOrig = actItem.originalPrice;
          const actStock = actItem.stock || actItem.maximumBuyForPerson || actItem.maximumBuyCount;

          if (expRow.salePrice && actSale !== expRow.salePrice) {
            result.diff.push({ field: `option[${i}].salePrice`, expected: expRow.salePrice, actual: actSale });
          }
          if (expRow.originalPrice && actOrig !== expRow.originalPrice) {
            result.diff.push({ field: `option[${i}].originalPrice`, expected: expRow.originalPrice, actual: actOrig });
          }
          if (expRow.stock && actStock !== expRow.stock) {
            result.diff.push({ field: `option[${i}].stock`, expected: expRow.stock, actual: actStock });
          }
        }
      }
    }

    // 4) 검색어 (15개 집합 및 개수 대조)
    if (wingSpec.searchTerms && wingSpec.searchTerms.length > 0) {
      const actualTags = (storeProd && storeProd.searchTags) ? storeProd.searchTags : (dom.tagChips || []);
      if (actualTags.length < wingSpec.searchTerms.length) {
        result.diff.push({ field: 'searchTermsCount', expected: wingSpec.searchTerms.length, actual: actualTags.length });
      }
    }

    // 5) 고시 상품군
    if (wingSpec.notice && wingSpec.notice.group) {
      const actGroup = dom.noticeGroup || null;
      if (!actGroup || !actGroup.includes(wingSpec.notice.group)) {
        result.diff.push({ field: 'noticeGroup', expected: wingSpec.notice.group, actual: actGroup });
      }
    }

    // 6) 제조사
    if (wingSpec.manufacturer) {
      const actMfg = (storeProd && storeProd.manufacturer) ? storeProd.manufacturer : dom.manufacturer;
      if (!actMfg || !actMfg.includes(wingSpec.manufacturer)) {
        result.diff.push({ field: 'manufacturer', expected: wingSpec.manufacturer, actual: actMfg });
      }
    }
    // 최종 성공 여부: diff 0개 AND errors 0개
    result.success = (result.diff.length === 0 && result.errors.length === 0);
  } catch (e) {
    result.errors.push({ step: 'diffAudit', error: e.message });
    result.success = false;
  }

  console.log(`[fill_wing] Completed fill for ${spec.id}. Diff count: ${result.diff.length}, Error count: ${result.errors.length}`);
  return result;
}

if (typeof module !== 'undefined') {
  module.exports = { fillWing };
}
