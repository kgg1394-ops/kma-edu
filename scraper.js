const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

// 실제 크롤링할 대상 웹페이지 URL (예시)
const TARGET_URL = 'https://edu.kma.org/board/list.asp';

async function run() {
  try {
    console.log('실제 데이터 수집을 시작합니다...');
    
    // 1. 대상 사이트 접속해서 HTML 긁어오기
    const response = await axios.get(TARGET_URL, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)' }
    });
    
    const $ = cheerio.load(response.data);
    const courses = [];

    // 2. 게시판 표(Table)에서 한 줄씩(tr) 읽어오기
    // (주의: 아래 '.board_list tbody tr' 부분은 실제 사이트 구조에 맞춰 수정이 필요할 수 있습니다)
    $('.board_list tbody tr').each((index, element) => {
      const title = $(element).find('.title').text().trim() || '테스트 교육명';
      const institution = $(element).find('.institution').text().trim() || '테스트 기관';
      const date = $(element).find('.date').text().trim() || '2026-00-00';
      const priceText = $(element).find('.price').text().trim() || '0';
      const creditsText = $(element).find('.credits').text().trim() || '0';

      const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10) || 0;
      const credits = parseInt(creditsText.replace(/[^0-9]/g, ''), 10) || 0;

      // 3. 조건 필터링 (온라인 & 3만원 이하)
      const isOnline = title.includes('온라인') || institution.includes('온라인');
      
      if (price <= 30000 && isOnline) {
        courses.push({ title, institution, date, price, credits });
      }
    });

    // 만약 사이트 구조가 달라서 못 긁어왔다면, 안내 메시지를 띄웁니다.
    if (courses.length === 0) {
      courses.push({ 
        title: "데이터를 불러오지 못했습니다. 사이트 구조(CSS 선택자) 확인이 필요합니다.", 
        institution: "-", date: "-", price: 0, credits: 0 
      });
    }

    // 4. 수집한 데이터를 파일로 저장
    fs.writeFileSync('data.json', JSON.stringify(courses, null, 2));
    console.log('실제 데이터 갱신 완료');

  } catch (error) {
    console.error('크롤링 에러:', error.message);
  }
}

run();
