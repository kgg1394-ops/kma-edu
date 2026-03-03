import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def fetch_all_gi_data():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    current_page = 1

    try:
        print("[1/3] 의협 사이트 접속 및 2개월치 검색 설정...")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(5)

        # 검색 버튼 클릭
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        print("[2/3] 페이지 넘기며 모든 데이터 수집 중 (나머지 화면까지!)")
        
        while True:
            # 1. 현재 화면 데이터 수집
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

            # 2. '다음' 버튼(>) 찾기 (더 정밀한 방식)
            try:
                # 페이징 영역에서 다음 페이지로 넘어가기 위한 '>' 버튼 또는 다음 숫자를 찾음
                next_page_num = current_page + 1
                # javascript:list(2), list(3)... 형태를 직접 실행하거나 클릭
                next_link = driver.find_element(By.XPATH, f"//div[@class='paging']//a[contains(@href, 'list({next_page_num})')]")
                
                driver.execute_script("arguments[0].click();", next_link)
                current_page += 1
                time.sleep(4) 
            except:
                # 만약 숫자가 없다면 진짜 '>' 버튼이 있는지 마지막으로 확인
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, ".paging .next")
                    if "disabled" in next_btn.get_attribute("class") or "#" in next_btn.get_attribute("href"):
                        break
                    next_btn.click()
                    current_page += 1
                    time.sleep(4)
                except:
                    print("   - 모든 페이지를 수집했습니다.")
                    break

        print(f"🎉 성공: 총 {len(all_results)}건의 데이터를 수집했습니다!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if len(all_results) > 0:
            print("[3/3] GitHub 업데이트 중...")
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "Full 2-Month Data: {len(all_results)} items"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("✨ 사이트 반영 성공!")
        driver.quit()

if __name__ == "__main__":
    fetch_all_gi_data()