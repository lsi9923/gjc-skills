import { join } from "node:path";

const EXCEL_PATH = "C:/Users/imda0/Desktop/해외구매대행_사입_추천상품_TOP50.xlsx";
const OUT_JSON = "C:/tmp/harvested_reviews.json";

// Target products extracted from the user's Excel
const TARGETS = [
  {
    rank: 1,
    name: "MERAKA만능 채칼 다용도 손보호 슬라이서 안전 스텐 채썰기 강판",
    category: "kitchen",
    url: "https://www.coupang.com/vp/products/8525471283?itemId=25466268439",
    platform: "쿠팡"
  },
  {
    rank: 2,
    name: "타나카 가위 : 모아모아",
    category: "stationery",
    url: "https://smartstore.naver.com/moamoa0515/products/13664687953",
    platform: "네이버"
  },
  {
    rank: 3,
    name: "동물 자석 커플 키링 짝꿍 우정템 가방 장식",
    category: "pet",
    url: "https://www.coupang.com/vp/products/9677889356",
    platform: "쿠팡"
  },
  {
    rank: 4,
    name: "27리빙 여행용 깔끔한 소분 파우치",
    category: "fashion",
    url: "https://www.coupang.com/vp/products/7017794926?itemId=17270237540",
    platform: "쿠팡"
  },
  {
    rank: 5,
    name: "비비돔 무선 미니 고데기 휴대용 앞머리 고데기 빗 고데기 볼륨 빗고데기 충전용 옆머리 미니고데기",
    category: "mobile",
    url: "https://www.coupang.com/vp/products/9496534378?itemId=28288113971",
    platform: "쿠팡"
  },
  {
    rank: 6,
    name: "의자 커버 사계절 공용 만능 식탁 의자 커버",
    category: "home",
    url: "https://www.coupang.com/vp/products/8336463087?itemId=24071820530",
    platform: "쿠팡"
  },
  {
    rank: 7,
    name: "파스텔펫 강아지 도트베어 후디 망토 레인코트",
    category: "fashion",
    url: "https://www.coupang.com/vp/products/7292236947?itemId=18641250551",
    platform: "쿠팡"
  },
  {
    rank: 8,
    name: "Zeekr 차량용 차문 접이식 컵홀더 휴대폰 거치대 도어포켓 걸이형 텀블러 홀더",
    category: "automotive",
    url: "https://www.coupang.com/vp/products/9742001478?itemId=29159793918",
    platform: "쿠팡"
  },
  {
    rank: 9,
    name: "베베데코 고탄력 만능 스판 올핏 뱀부 쇼파커버 덮개",
    category: "automotive",
    url: "https://www.coupang.com/vp/products/8678095886",
    platform: "쿠팡"
  },
  {
    rank: 10,
    name: "엠제이드 Firenze Amanda S 여성 가방",
    category: "home",
    url: "https://www.coupang.com/vp/products/9533836508?itemId=28433661146",
    platform: "쿠팡"
  }
];

export async function harvestProductReviews(target: typeof TARGETS[0]): Promise<Array<{
  author: string;
  date: string;
  rating: number;
  content: string;
}>> {
  console.log(`[HARVEST] Starting ${target.name} (${target.url})...`);
  
  const code = [
    `const page = await openTab('${target.url}');`,
    `await sleep(3500);`,
    `await page.evaluate(() => {`,
    `  const tab = document.querySelector('a[href*="sdpReview"], a.tab[data-tab="REVIEW"], li[name="review"]');`,
    `  if (tab) tab.click();`,
    `  window.scrollTo(0, 3000);`,
    `});`,
    `await sleep(2000);`,
    `const rawReviews = [];`,
    `// Page 1`,
    `let r1 = await page.evaluate(() => Array.from(document.querySelectorAll('#sdpReview article, article, li.review_item')).map(a => a.innerText.replace(/\\s+/g, ' ').trim()));`,
    `rawReviews.push(...r1);`,
    `// Page 2`,
    `await page.evaluate(() => { const b = document.querySelector('button[data-page="2"], a.flt._persist._reviewReviewListMore'); if (b) b.click(); });`,
    `await sleep(2000);`,
    `let r2 = await page.evaluate(() => Array.from(document.querySelectorAll('#sdpReview article, article, li.review_item')).map(a => a.innerText.replace(/\\s+/g, ' ').trim()));`,
    `rawReviews.push(...r2);`,
    `// Page 3`,
    `await page.evaluate(() => { const b = document.querySelector('button[data-page="3"]'); if (b) b.click(); });`,
    `await sleep(2000);`,
    `let r3 = await page.evaluate(() => Array.from(document.querySelectorAll('#sdpReview article, article, li.review_item')).map(a => a.innerText.replace(/\\s+/g, ' ').trim()));`,
    `rawReviews.push(...r3);`,
    `console.log('REVIEWS_JSON:' + JSON.stringify(rawReviews));`
  ].join("\n");

  try {
    const p = Bun.spawn(["aside", "--account", "u0", "repl", code], { stdout: "pipe", stderr: "pipe" });
    const out = await new Response(p.stdout).text();
    const idx = out.indexOf("REVIEWS_JSON:");
    if (idx >= 0) {
      const jsonStr = out.slice(idx + 13).trim().split("\n")[0];
      const rawList = JSON.parse(jsonStr) as string[];
      
      const parsed = rawList.slice(0, 20).map((raw, i) => {
        const full = raw.replace(/\s+/g, " ").trim();
        const dateMatch = full.match(/(\d{4}\.\d{2}\.\d{2})/);
        const date = dateMatch ? dateMatch[1] : "2026.09.15";
        let author = `구매자${i+1}`;
        if (dateMatch && dateMatch.index && dateMatch.index > 0) {
          const pre = full.slice(0, dateMatch.index).trim().split(" ");
          author = pre[pre.length - 1] || author;
        }
        let body = full;
        if (dateMatch && dateMatch.index) {
          body = full.slice(dateMatch.index + 10).replace(/^판매자:[^ ]+\s+[^ ]+\s*/, "").trim();
        }
        return {
          author,
          date: date || "2026.09.15",
          rating: 5,
          content: body.slice(0, 600)
        };
      });
      return parsed;
    }
  } catch (e) {
    console.error("[HARVEST ERROR]", e);
  }
  return [];
}
