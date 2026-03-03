import os, json, time, datetime, subprocess, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_med_essential_final():
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

    # 2026년 말까지 수집
    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = "2026-12-31"

    try:
        print(f"🚀 [MED Essential] 필수평점 정밀 추출 모드 가동...")
        
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
                    
                    # 1. eduidx 링크 생성
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    reg_url = f"https://edu.kma.org/edu/schedule_view?eduidx={item_id}"

                    # 2. 필수평점 정밀 추출 (선생님이 주신 샘플 기준)
                    # 예: "평점 6 (필수 1평점 포함)" -> 1 추출
                    full_text = title_raw + " " + detail_text
                    essential_match = re.search(r'필수\s*(\d+)\s*평점', full_text)
                    
                    if essential_match:
                        credits = essential_match.group(1)
                    else:
                        # 예비: "평점 2 (필수 2평점 포함)" 에서 숫자만 가져오기
                        match = re.search(r'\(필수\s*(\d+)', full_text)
                        credits = match.group(1) if match else "0"
                    
                    # 제목 정제 (뒤의 [필수] 태그 유지)
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()
                    if not clean_title.endswith('[필수]'):
                        clean_title += " [필수]"

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

            print(f"   - {page_num}페이지 수집 완료 (누적: {len(all_results)}건)", end="\r")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            msg = f"Essential Credit Logic Fix: {len(all_results)} items"
            subprocess.run(f'git commit -m "{msg}"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print(f"\n✨ {len(all_results)}건의 평점과 링크가 수정되었습니다!")
        driver.quit()

if __name__ == "__main__":
    fetch_med_essential_final()