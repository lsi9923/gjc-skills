import { harvestProductReviews } from "./harvest_top50_reviews.ts";

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
    name: "동물 자석 커플 키링 짝꿍 우정템 가방 장식",
    category: "pet",
    url: "https://www.coupang.com/vp/products/9677889356",
    platform: "쿠팡"
  },
  {
    rank: 3,
    name: "27리빙 여행용 깔끔한 소분 파우치",
    category: "fashion",
    url: "https://www.coupang.com/vp/products/7017794926?itemId=17270237540",
    platform: "쿠팡"
  },
  {
    rank: 4,
    name: "비비돔 무선 미니 고데기 휴대용 앞머리 고데기 빗 고데기 볼륨 빗고데기",
    category: "mobile",
    url: "https://www.coupang.com/vp/products/9496534378?itemId=28288113971",
    platform: "쿠팡"
  },
  {
    rank: 5,
    name: "의자 커버 사계절 공용 만능 식탁 의자 커버",
    category: "home",
    url: "https://www.coupang.com/vp/products/8336463087?itemId=24071820530",
    platform: "쿠팡"
  },
  {
    rank: 6,
    name: "파스텔펫 강아지 도트베어 후디 망토 레인코트",
    category: "fashion",
    url: "https://www.coupang.com/vp/products/7292236947?itemId=18641250551",
    platform: "쿠팡"
  },
  {
    rank: 7,
    name: "Zeekr 차량용 차문 접이식 컵홀더 휴대폰 거치대",
    category: "automotive",
    url: "https://www.coupang.com/vp/products/9742001478?itemId=29159793918",
    platform: "쿠팡"
  },
  {
    rank: 8,
    name: "베베데코 고탄력 만능 스판 올핏 뱀부 쇼파커버 덮개",
    category: "automotive",
    url: "https://www.coupang.com/vp/products/8678095886",
    platform: "쿠팡"
  }
];

const results = [];

for (const target of TARGETS) {
  const reviews = await harvestProductReviews(target);
  results.push({
    ...target,
    reviews
  });
  console.log(`[DONE] ${target.name}: ${reviews.length} reviews`);
}

await Bun.write("C:/tmp/harvested_reviews.json", JSON.stringify(results, null, 2));
console.log("[SAVED JSON] C:/tmp/harvested_reviews.json");

// Now invoke build_review_excel.py
const p = Bun.spawn([
  "C:/Users/imda0/AppData/Local/Programs/Python/Python313/python.exe",
  "C:/Users/imda0/.gjc/agent/skills/crawling-overseas-sourcing-excel/scripts/build_review_excel.py",
  "C:/tmp/harvested_reviews.json",
  "C:/Users/imda0/Desktop/해외구매대행_사입_TOP50_상품리뷰_수집분석.xlsx"
], { stdout: "pipe", stderr: "pipe" });

const out = await new Response(p.stdout).text();
const err = await new Response(p.stderr).text();
console.log("EXCEL_BUILD_OUT:\n", out);
if (err) console.error("EXCEL_BUILD_ERR:\n", err);
