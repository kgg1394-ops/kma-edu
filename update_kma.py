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

    # 수집 기간 설정
    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = "2026-12-31"

    try:
        print(f"🚀 [데이터 분석] 필수평점 항목을 정밀 스캔합니다...")
        
        while True:
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=1&sch_txt=&sch_es=Y&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            driver.get(target_url)
            time.sleep(3)

            # 각 교육 항목의 컨테이너를 먼저 찾습니다.
            items = driver.find_elements(By.CSS_SELECTOR, "div#edu > div.boardList > ul > li")
            
            if not items:
                # 위 선택자로 안 잡힐 경우 기존 방식으로 시도
                titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
                if not titles: break
            else:
                # 컨테이너 방식 (더 정확함)
                titles = [item.find_element(By.CSS_SELECTOR, "p.mb5") for item in items]

            # 중복 체크
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_first_title: break
            last_page_first_title = current_first_title

            for i in range(len(titles)):
                try:
                    # 해당 항목의 전체 텍스트를 가져와서 평점을 찾습니다.
                    # li 태그 내부의 모든 텍스트를 합쳐서 검색 범위에 넣습니다.
                    parent_item = titles[i].find_element(By.XPATH, "./..") 
                    full_text = parent_item.text.replace("\n", " ")
                    
                    title_raw = titles[i].text.strip()
                    onclick_val = titles[i].get_attribute("onclick")
                    
                    # 1. eduidx 링크 생성
                    idx_match = re.search(r'viewer\((\d+)\)', onclick_val)
                    item_id = idx_match.group(1) if idx_match else ""
                    reg_url = f"https://edu.kma.org/edu/schedule_view?eduidx={item_id}"

                    # 2. 필수평점 정밀 추출
                    # "평점 6 (필수 1평점 포함)" -> '1' 추출
                    # "평점 6 (필수 2평점 포함)" -> '2' 추출
                    score = "0"
                    # 패턴: '필수' 뒤에 오는 숫자를 찾음
                    essential_match = re.search(r'필수\s*(\d+)', full_text)
                    if essential_match:
                        score = essential_match.group(1)
                    
                    # 제목에서 [필수] 태그 정제
                    clean_title = re.sub(r'\[?평점.*?\]?', '', title_raw).strip()
                    if not clean_title.endswith('[필수]'):
                        clean_title += " [필수]"

                    # 상세 정보 추출
                    detail_text = parent_item.find_element(By.CSS_SELECTOR, "ul.cyberKindList").text
                    lines = detail_text.split('\n')
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": clean_title,
                        "credits": score,
                        "date": date,
                        "institution": inst,
                        "location": loc,
                        "reg_url": reg_url,
                        "is_online": "온라인" in title_raw or "온라인" in loc
                    })
                except Exception as e:
                    continue

            print(f"   - {page_num}페이지 분석 완료 (누적: {len(all_results)}건)", end="\r")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if all_results:
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Fixed credits logic: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print(f"\n✨ 업데이트 완료! 이제 평점이 정상적으로 표시됩니다.")
        driver.quit()

if __name__ == "__main__":
    fetch_med_essential_final()