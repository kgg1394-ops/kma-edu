import os, json, time, datetime, subprocess, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_essential_perfect():
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

    # 2026년 말까지 장기 수집
    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = "2026-12-31"

    try:
        print(f"🚀 [Deep Scan] 필수평점 정밀 분석을 시작합니다.")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=1&sch_txt=&sch_es=Y&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(5) 

            # [핵심] 제목 p태그들을 먼저 잡습니다.
            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            if not titles: break
            
            # 중복 체크
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_first_title: break
            last_page_first_title = current_first_title

            # [핵심] 각 항목의 컨테이너를 부모 레벨에서 통째로 텍스트화합니다.
            # 의협 사이트의 div#edu 내부 구조를 전체 텍스트로 읽어 숫자를 찾습니다.
            for title_el in titles:
                try:
                    # 제목 바로 위의 부모(li 또는 div) 텍스트를 통째로 가져옵니다.
                    parent_el = title_el.find_element(By.XPATH, "./..")
                    full_block_text = parent_el.text.replace("\n", " ")
                    
                    title_raw = title_el.text.strip()
                    onclick_val = title_el.get_attribute("onclick")
                    
                    # 1. eduidx 링크 추출
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    reg_url = f"https://edu.kma.org/edu/schedule_view?eduidx={item_id}"

                    # 2. [필살] 필수평점 숫자 추출 로직
                    # '필수'와 '평점' 사이에 있는 숫자를 가장 먼저 찾습니다.
                    score = "0"
                    # 패턴: 필수 1평점, 필수 2평점, 필수 1 평점 등
                    essential_match = re.search(r'필수\s*(\d+)\s*평점', full_block_text)
                    if not essential_match:
                        # 패턴: 필수:2, 필수 2 등
                        essential_match = re.search(r'필수\s*[:：]?\s*(\d+)', full_block_text)
                    
                    if essential_match:
                        score = essential_match.group(1)
                    
                    # 디버그 출력 (검은 창에서 숫자가 올라가는지 꼭 확인하세요!)
                    print(f"   🔎 확인: {title_raw[:15]}... -> 필수 {score}점")

                    # 제목 정제 (평점 문구 제거)
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()

                    # 상세 정보 (ul 내 데이터)
                    detail_el = title_el.find_element(By.XPATH, "./following-sibling::ul[1]")
                    lines = detail_el.text.split('\n')
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": clean_title, "credits": score, "date": date,
                        "institution": inst, "location": loc, "reg_url": reg_url,
                        "is_online": "온라인" in title_raw or "온라인" in loc
                    })
                except: continue

            print(f"   ✅ {page_num}페이지 완료 (누적 {len(all_results)}건)")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Final Score Fix: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
        driver.quit()

if __name__ == "__main__":
    fetch_essential_perfect()