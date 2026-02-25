const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

async function run() {
  // 실제 사이트에 맞춰 파싱 로직은 수정해야 합니다. 여기서는 구조만 잡습니다.
  const courses = [
    { title: "[온라인] 2026 소화기 연수강좌", institution: "소화기내과학회", date: "2026-04-10", price: 20000, credits: 2 }
  ];

  // 긁어온 데이터를 'data.json' 이라는 파일로 저장합니다. (DB 역할을 대신함)
  fs.writeFileSync('data.json', JSON.stringify(courses, null, 2));
  console.log('데이터 갱신 완료');
}

run();
