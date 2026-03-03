import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_with_loop_check():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    page_num = 1
    last_page_content = "" # 이전 페이지의 첫 번째 제목을 저장

    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%Y-%m-%d')

    try:
        print(f"🚀 [스마트 수집] {start_dt} ~ {end_dt} 일정을 수집합니다.")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=&sch_txt=&sch_es=&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(3)

            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            
            # 1. 아예 데이터가 없는 경우
            if not titles:
                print(f"\n✅ {page_num-1}페이지에서 종료 (데이터 없음)")
                break

            # 2. [중요] 이전 페이지와 데이터가 똑같은 경우 (무한 루프 방지)
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_content:
                print(f"\n✅ {page_num-1}페이지가 실제 마지막입니다. 수집을 종료합니다.")
                break
            
            last_page_content = current_first_title # 현재 첫 제목을 기록

            details = driver.find_elements(By.CSS_SELECTOR, "ul.cyberKindList")
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
            
            print(f"   - {page_num}페이지 수집 완료... (누적 {len(all_results)}건)", end="\r")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Smart Scan: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("\n✨ 업데이트 완료!")
        driver.quit()

if __name__ == "__main__":
    fetch_with_loop_check()