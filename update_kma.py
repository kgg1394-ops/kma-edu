import os
import json
import time
import datetime
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_with_selenium():
    options = Options()
    # 안정성을 위한 옵션들
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # 눈으로 확인하기 위해 창을 띄웁니다.
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    results = []
    try:
        print("[1/4] KMA Edu Center 접속 중...")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(5)

        print("[2/4] 검색 버튼 클릭 및 데이터 로딩 대기...")
        # 검색 버튼 클릭
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(8) 

        print("[3/4] 데이터 분석 시작...")
        # 선생님이 보내주신 HTML 구조에 맞춘 추출 로직
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
            except:
                continue

        print(f"성공: {len(results)}건의 데이터를 수집했습니다.")

    except Exception as e:
        print(f"에러 발생: {e}")
    finally:
        # 데이터 저장
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        if len(results) > 0:
            print("[4/4] GitHub 업데이트 진행 중...")
            try:
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
                # 윈도우 환경에서 안정적인 Git 실행을 위해 shell=True 사용
                subprocess.run("git add data.json", shell=True)
                subprocess.run(f'git commit -m "Auto-update: {now}"', shell=True, capture_output=True)
                subprocess.run("git push origin main", shell=True)
                print("Web Site Update Success!")
            except Exception as ge:
                print(f"Git Push Error: {ge}")

        driver.quit()

if __name__ == "__main__":
    fetch_with_selenium()