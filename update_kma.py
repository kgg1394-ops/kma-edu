import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_all_pages_perfectly():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    current_page = 1

    try:
        print(f"[1/3] 의협 사이트 접속 (2개월치 일정 수집)")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(5)

        # 검색 버튼 클릭
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        print("[2/3] 모든 페이지 횡단 수집 시작...")
        
        while True:
            # 1. 데이터 추출
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

                    all_results.append({
                        "title": title, "credits": credits, "date": date,
                        "institution": inst, "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except: continue

            print(f"   - {current_page}페이지 완료 (누적: {len(all_results)}건)")

            # 2. '다음 페이지' 버튼 찾기 (숫자 기반)
            try:
                # 현재 페이지 다음 숫자(2, 3, 4...)를 가진 버튼을 찾습니다.
                next_page_num = current_page + 1
                # 텍스트가 숫자인 버튼을 찾거나 '>' 버튼을 찾습니다.
                next_btn = driver.find_element(By.XPATH, f"//div[@class='paging']//a[text()='{next_page_num}']")
                
                driver.execute_script("arguments[0].click();", next_btn)
                current_page += 1
                time.sleep(4) 
            except:
                # 숫자가 없다면 진짜 '>' 버튼이 있는지 확인
                try:
                    next_arrow = driver.find_element(By.XPATH, "//div[@class='paging']//a[text()='>']")
                    # 클릭 가능한지 확인 (마지막 페이지면 javascript:list(0) 등일 수 있음)
                    if "list(0)" in next_arrow.get_attribute("href"):
                        break
                    driver.execute_script("arguments[0].click();", next_arrow)
                    current_page += 1
                    time.sleep(4)
                except:
                    break # 더 이상 페이지가 없음

        print(f"🎉 성공: 총 {len(all_results)}건의 데이터를 수집했습니다!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if len(all_results) > 0:
            print("[3/3] GitHub 업데이트 중...")
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Full 2-month update: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("✨ 사이트 반영 성공!")
        driver.quit()

if __name__ == "__main__":
    fetch_all_pages_perfectly()