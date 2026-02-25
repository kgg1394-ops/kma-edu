const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

const TARGET_URL = 'https://edu.kma.org/board/list.asp';

async function run() {
  try {
    console.log('실제 데이터 수집을 시작합니다...');
    
    // 1. 사람처럼 위장하고, 10초까지만 기다리기 (Timeout)
    const response = await axios.get(TARGET_URL, {
      timeout: 10000, // 10000ms = 10초
      headers: { 
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
      }
    });
    
    const $ = cheerio.load(response.data);
    const courses = [];

    $('.board_list tbody tr').each((index, element) => {
      const title = $(element).find('.title').text().trim() || '테스트 교육명';
      const institution = $(element).find('.institution').text().trim() || '테스트 기관';
      const date = $(element).find('.date').text().trim() || '2026-00-00';
      const priceText = $(element).find('.price').text().trim() || '0';
      const creditsText = $(element).find('.credits').text().trim() || '0';

      const price = parseInt(priceText.replace(/[^0-9]/g, ''), 10) || 0;
      const credits = parseInt(creditsText.replace(/[^0-9]/g, ''), 10) || 0;

      const isOnline = title.includes('온라인') || institution.includes('온라인');
      
      if (price <= 30000 && isOnline) {
        courses.push({ title, institution, date, price, credits });
      }
    });

    if (courses.length === 0) {
      courses.push({ 
        title: "데이터를 불러오지 못했습니다. 사이트 구조(CSS 선택자) 확인이 필요합니다.", 
        institution: "-", date: "-", price: 0, credits: 0 
      });
    }

    fs.writeFileSync('data.json', JSON.stringify(courses, null, 2));
    console.log('실제 데이터 갱신 완료');

  } catch (error) {
    // 에러가 나더라도 빈 파일을 만들어서 웹사이트가 고장나지 않게 처리
    console.error('크롤링 에러:', error.message);
    const errorData = [{ 
      title: `크롤링 실패: ${error.message}`, 
      institution: "에러발생", date: "-", price: 0, credits: 0 
    }];
    fs.writeFileSync('data.json', JSON.stringify(errorData, null, 2));
  }
}

run();
