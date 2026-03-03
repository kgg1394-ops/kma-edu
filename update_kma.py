import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_kma_2months():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    results = []

    try:
        print("[1/3] 의협 사이트 접속 및 검색 실행...")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(4)

        # 날짜 입력 대신 바로 '검색' 버튼을 눌러 기본 2달치 리스트업
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        print("[2/3] 전체 페이지 순회하며 수집 시작...")
        
        while True:
            # 현재 페이지 데이터 추출
            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            details = driver.find_elements(By.CSS_SELECTOR, "ul.cyberKindList")

            for i in range(len(titles)):
                try:
                    title_text = titles[i].text.strip()
                    # 평점 분리 (예: "교육명 평점 2")
                    title = title_text.split('평점')[0].strip()
                    credits = title_text.split('평점')[-1].strip() if '평점' in title_text else "0"
                    
                    detail_text = details[i].text.strip()
                    lines = detail_text.split('\n')
                    
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    results.append({
                        "title": title, "credits": credits, "date": date,
                        "institution": inst, "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except: continue

            # [핵심] 다음 페이지 버튼 (>) 클릭 로직
            try:
                # 다음 페이지 버튼의 '>' 기호를 가진 요소를 찾습니다.
                next_btns = driver.find_elements(By.CSS_SELECTOR, ".paging a")
                next_btn = None
                for btn in next_btns:
                    if ">" == btn.text.strip():
                        next_btn = btn
                        break
                
                if next_btn:
                    # 다음 페이지가 활성화된 링크인지 확인
                    if "javascript:void(0)" in next_btn.get_attribute("href"):
                        break # 더 이상 갈 페이지가 없음
                    next_btn.click()
                    time.sleep(3)
                else:
                    break
            except:
                break

        print(f"성공: 총 {len(results)}건의 데이터를 수집했습니다.")

    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        if len(results) > 0:
            print("[3/3] GitHub 업데이트 중...")
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Full Update: {now}"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("✨ 사이트 반영 성공!")
        driver.quit()

if __name__ == "__main__":
    fetch_kma_2months()