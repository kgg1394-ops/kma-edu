import os, json, time, datetime, subprocess, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_essential_with_links():
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
    end_dt = "2026-12-31" # 2026년 말까지 수집

    try:
        print(f"🚀 [필수평점 정밀 수집] 기간: {start_dt} ~ {end_dt}")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=1&sch_txt=&sch_es=Y&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(3)

            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            details = driver.find_elements(By.CSS_SELECTOR, "ul.cyberKindList")

            if not titles: break
            
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_first_title: break
            last_page_first_title = current_first_title

            for i in range(len(titles)):
                try:
                    title_raw = titles[i].text.strip()
                    detail_text = details[i].text.strip()
                    onclick_val = titles[i].get_attribute("onclick")
                    
                    # 1. 상세 페이지 ID 및 URL 추출 ($.viewer(12345) 형태 분석)
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    # 의협 상세 페이지 표준 URL 형식
                    reg_url = f"https://edu.kma.org/edu/schedule_view?idx={item_id}" if item_id else "#"

                    # 2. 필수평점 숫자 추출 (정규표현식 강화)
                    # '필수:1점' 또는 '필수 1' 또는 '평점 : 2점(필수:1점)' 등 대응
                    full_text = title_raw + " " + detail_text
                    # '필수' 뒤의 숫자를 우선 찾고, 없으면 일반 평점 숫자를 찾음
                    essential_match = re.search(r'필수\s*[:：]?\s*(\d+)', full_text)
                    if essential_match:
                        credits = essential_match.group(1)
                    else:
                        general_match = re.search(r'평점\s*[:：]?\s*(\d+)', full_text)
                        credits = general_match.group(1) if general_match else "0"
                    
                    # 제목 정제
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()
                    
                    lines = detail_text.split('\n')
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": clean_title,
                        "credits": credits,
                        "date": date,
                        "institution": inst,
                        "location": loc,
                        "reg_url": reg_url,
                        "is_online": "온라인" in title_raw or "온라인" in loc
                    })
                except: continue

            print(f"   - {page_num}페이지 수집 완료... (누적: {len(all_results)}건)", end="\r")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Fixed credits and added links: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print(f"\n✨ 총 {len(all_results)}건 업데이트 완료!")
        driver.quit()

if __name__ == "__main__":
    fetch_essential_with_links()