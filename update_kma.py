import os, json, time, datetime, subprocess, re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_med_essential_debug():
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
        print(f"🚀 [디버그 모드] 데이터를 한 글자씩 정밀 분석합니다...")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=1&sch_txt=&sch_es=Y&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(4)

            # [핵심] li 태그(한 칸 전체)를 통째로 가져옵니다.
            items = driver.find_elements(By.CSS_SELECTOR, "div.boardList > ul > li")
            
            if not items: break
            
            # 중복 체크용 제목
            try:
                current_first_title = items[0].find_element(By.CSS_SELECTOR, "p.mb5").text.strip()
            except: break

            if current_first_title == last_page_first_title: break
            last_page_first_title = current_first_title

            for item in items:
                try:
                    # 1. 해당 칸의 모든 텍스트를 하나로 합침
                    raw_text = item.text.replace("\n", " ")
                    title_el = item.find_element(By.CSS_SELECTOR, "p.mb5")
                    title_raw = title_el.text.strip()
                    onclick_val = title_el.get_attribute("onclick")
                    
                    # 2. 링크 추출 (eduidx)
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    reg_url = f"https://edu.kma.org/edu/schedule_view?eduidx={item_id}"

                    # 3. [초정밀] 필수평점 숫자 추출
                    # "필수 1평점", "필수 2", "필수:2" 등 모든 숫자 패턴 대응
                    score = "0"
                    # 패턴 1: '필수'라는 글자 주변의 숫자를 찾음
                    essential_pattern = re.search(r'필수\s*(\d+)', raw_text)
                    if essential_pattern:
                        score = essential_pattern.group(1)
                    else:
                        # 패턴 2: '평점 X' 형태에서 괄호 안의 숫자를 다시 확인
                        fallback_pattern = re.findall(r'(\d+)', raw_text)
                        if len(fallback_pattern) >= 2: # 평점이 보통 2번 나오므로 (전체평점, 필수평점)
                            score = fallback_pattern[1]

                    # 디버그용 출력 (검은 창에서 확인 가능)
                    print(f"   🔎 분석 중: {title_raw[:20]}... -> 추출된 평점: {score}점")

                    # 제목 정제
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()
                    if "[필수]" not in clean_title: clean_title += " [필수]"

                    # 상세 정보
                    detail_text = item.find_element(By.CSS_SELECTOR, "ul.cyberKindList").text
                    lines = detail_text.split('\n')
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
        print(f"\n❌ 에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Emergency Credit Fix: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("\n✨ 데이터가 업데이트되었습니다. 이제 사이트를 확인해 보세요!")
        driver.quit()

if __name__ == "__main__":
    fetch_med_essential_debug()