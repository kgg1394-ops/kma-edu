import os, json, time, datetime, subprocess, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_essential_clean():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    page_num = 1
    last_page_first_title = ""

    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = "2026-12-31"

    try:
        print(f"🚀 [시스템 가동] 필수평점 교육 일정 수집을 시작합니다...")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=1&sch_txt=&sch_es=Y&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(3) 

            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            if not titles: break
            
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_first_title: break
            last_page_first_title = current_first_title

            for title_el in titles:
                try:
                    title_raw = title_el.text.strip()
                    onclick_val = title_el.get_attribute("onclick")
                    
                    # eduidx 링크 생성
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    reg_url = f"https://edu.kma.org/edu/schedule_view?eduidx={item_id}"

                    # 제목 정제 (평점 문구 및 [필수] 태그 정리)
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()
                    if "[필수]" not in clean_title: clean_title += " [필수]"

                    # 상세 데이터 파싱
                    detail_el = title_el.find_element(By.XPATH, "./following-sibling::ul[1]")
                    lines = detail_el.text.split('\n')
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": clean_title,
                        "date": date,
                        "institution": inst,
                        "location": loc,
                        "reg_url": reg_url,
                        "is_online": "온라인" in title_raw or "온라인" in loc
                    })
                except: continue

            print(f"   ✅ {page_num}페이지 수집 완료 (누적 {len(all_results)}건)")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Clean Schedule Update: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
        driver.quit()

if __name__ == "__main__":
    fetch_essential_clean()