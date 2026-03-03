import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_by_url_param():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    
    # 날짜 설정 (오늘 ~ 60일 후)
    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%Y-%m-%d')

    try:
        print(f"[1/3] URL 직접 공략 시작 ({start_dt} ~ {end_dt})")
        
        for page_num in range(1, 11): # 최대 10페이지(150건)까지 확인
            # 선생님이 발견하신 URL 구조를 그대로 활용합니다.
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=&sch_txt=&sch_es=&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            
            print(f"   - {page_num}페이지 접속 중...")
            driver.get(target_url)
            time.sleep(4) # 로딩 대기

            # 데이터 추출
            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            details = driver.find_elements(By.CSS_SELECTOR, "ul.cyberKindList")

            if not titles:
                print("   - 더 이상 가져올 데이터가 없습니다. 수집을 종료합니다.")
                break

            for i in range(len(titles)):
                try:
                    title_text = titles[i].text.strip()
                    title = title_text.split('평점')[0].strip()
                    credits = title_text.split('평점')[-1].strip() if '평점' in title_text else "0"
                    detail_text = details[i].text.strip()
                    lines = detail_text.split('\n')
                    
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": title, "credits": credits, "date": date,
                        "institution": inst, "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except: continue

            print(f"   - {page_num}페이지 수집 완료 (현재 누적: {len(all_results)}건)")

        print(f"🎉 성공: 총 {len(all_results)}건의 데이터를 수집했습니다!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if len(all_results) > 0:
            print("[3/3] GitHub 업데이트 중...")
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Full URL-based Update: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("✨ 사이트 반영 성공!")
        driver.quit()

if __name__ == "__main__":
    fetch_by_url_param()