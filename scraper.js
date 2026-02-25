const axios = require('axios');
const cheerio = require('cheerio');
const fs = require('fs');

// 타겟: 구글 뉴스 "소화기 연수강좌" 검색 결과 (RSS 피드)
const TARGET_URL = 'https://news.google.com/rss/search?q=%EC%86%8C%ED%99%94%EA%B8%B0+%EC%97%B0%EC%88%98%EA%B0%95%EC%A2%8C&hl=ko&gl=KR&ceid=KR:ko';

async function run() {
  try {
    console.log('구글 뉴스 데이터 수집을 시작합니다...');
    
    // 구글 뉴스는 방화벽이 없어서 봇(GitHub)의 접근을 환영합니다!
    const response = await axios.get(TARGET_URL, { timeout: 10000 });
    
    // XML(RSS) 형식이라 xmlMode를 true로 설정하여 파싱합니다.
    const $ = cheerio.load(response.data, { xmlMode: true });
    const courses = [];

    // 뉴스 기사(item)들을 순회합니다.
    $('item').each((index, element) => {
      if (index >= 5) return false; // 너무 많으면 표가 안 예쁘니 상위 5개만 자릅니다.

      const rawTitle = $(element).find('title').text();
      const pubDate = $(element).find('pubDate').text();

      // 날짜를 보기 좋게 다듬기 (예: 2026-02-26)
      const dateObj = new Date(pubDate);
      const formattedDate = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`;

      // 수집한 뉴스 데이터를 우리 웹사이트 표 구조에 맞게 억지로(?) 끼워 맞춥니다.
      courses.push({ 
        title: rawTitle, 
        institution: "구글 뉴스", 
        date: formattedDate, 
        price: 0, 
        credits: 0 
      });
    });

    if (courses.length === 0) {
      courses.push({ 
        title: "검색된 소화기 연수강좌 뉴스가 없습니다.", 
        institution: "-", date: "-", price: 0, credits: 0 
      });
    }

    // 데이터를 파일로 저장
    fs.writeFileSync('data.json', JSON.stringify(courses, null, 2));
    console.log('성공적으로 데이터를 가져와 저장했습니다!');

  } catch (error) {
    console.error('크롤링 에러:', error.message);
    const errorData = [{ 
      title: `크롤링 실패: ${error.message}`, 
      institution: "에러발생", date: "-", price: 0, credits: 0 
    }];
    fs.writeFileSync('data.json', JSON.stringify(errorData, null, 2));
  }
}

run();
