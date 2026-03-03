import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_2_months():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    results = []
    try:
        # 1. 날짜 계산 (오늘 ~ 60일 후)
        start_date = datetime.datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%Y-%m-%d')
        
        print(f"[1/4] 기간 설정: {start_date} ~ {end_date}")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(3)

        # 2. 날짜 입력 및 검색
        # 의협 사이트의 날짜 입력 ID를 찾아 입력 (보통 sdate, edate 등)
        driver.execute_script(f"document.getElementById('start_date').value = '{start_date}'")
        driver.execute_script(f"document.getElementById('end_date').value = '{end_date}'")
        
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        print("[2/4] 전 페이지 데이터 수집 중...")
        
        while True:
            # 현재 페이지 데이터 추출
            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
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

                    results.append({
                        "title": title, "credits": credits, "date": date,
                        "institution": inst, "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except: continue

            # '다음 페이지' 버튼이 있는지 확인하고 클릭
            try:
                # 넥스트 버튼 (>) 찾기 - 사이트 구조에 따라 선택자가 다를 수 있음
                next_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Next')]") 
                if "disabled" in next_btn.get_attribute("class"): break
                next_btn.click()
                time.sleep(3)
            except:
                break # 다음 페이지가 없으면 종료

        print(f"성공: 총 {len(results)}건의 데이터를 수집했습니다.")

    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        if len(results) > 0:
            print("[4/4] GitHub 업데이트 진행 중...")
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "2-Month Update: {now}"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("Web Site Update Success!")
        driver.quit()

if __name__ == "__main__":
    fetch_2_months()