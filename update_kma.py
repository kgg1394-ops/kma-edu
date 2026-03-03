import os, json, time, datetime, subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def fetch_all_pages():
    options = Options()
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    page_num = 1

    try:
        print("[1/3] 의협 사이트 접속 및 검색 실행...")
        driver.get("https://edu.kma.org/edu/schedule")
        time.sleep(4)

        # 검색 버튼 클릭 (기본 2달치 검색)
        search_btn = driver.find_element(By.CSS_SELECTOR, "input[value='검색'].search")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(5)

        print("[2/3] 전 페이지 순회하며 수집 시작 (나머지 화면까지 모두!)")
        
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

                    all_results.append({
                        "title": title, "credits": credits, "date": date,
                        "institution": inst, "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except: continue

            print(f"   - {page_num}페이지 수집 완료 (현재 누적: {len(all_results)}건)")

            # [핵심] 다음 페이지(>) 버튼 찾기 및 클릭
            try:
                # '다음'을 의미하는 > 버튼을 찾습니다.
                # 보통 <a href="javascript:list(2)"> > </a> 이런 식입니다.
                next_btn = driver.find_element(By.XPATH, "//div[@class='paging']//a[text()='>']")
                
                # 버튼의 href가 javascript:list(0) 이거나 비어있으면 마지막 페이지입니다.
                if "list(0)" in next_btn.get_attribute("href") or not next_btn.is_enabled():
                    print("   - 마지막 페이지에 도달했습니다.")
                    break
                
                # 다음 페이지로 이동
                driver.execute_script("arguments[0].click();", next_btn)
                page_num += 1
                time.sleep(4) # 로딩 대기
            except Exception as e:
                print("   - 더 이상 넘길 페이지가 없습니다.")
                break

        print(f"🎉 성공: 총 {len(all_results)}건의 데이터를 수집했습니다!")

    except Exception as e:
        print(f"❌ 에러 발생: {e}")
    finally:
        # 데이터 저장
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        if len(all_results) > 0:
            print("[3/3] GitHub 업데이트 중...")
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            subprocess.run("git add .", shell=True)
            subprocess.run(f'git commit -m "All Pages Update: {now}"', shell=True, capture_output=True)
            subprocess.run("git push origin main", shell=True)
            print("✨ 사이트 반영 성공!")
        driver.quit()

if __name__ == "__main__":
    fetch_all_pages()