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

def fetch_kma_unlimited():
    # 1. 크롬 옵션 설정 (GitHub Actions 및 로컬 공용)
    options = Options()
    options.add_argument("--headless")           # 화면 없이 실행 (서버용 필수)
    options.add_argument("--disable-gpu")        # GPU 가속 끄기
    options.add_argument("--no-sandbox")         # 보안 컨테이너 해제
    options.add_argument("--disable-dev-shm-usage") # 공유 메모리 부족 방지
    options.add_argument("--disable-blink-features=AutomationControlled") # 자동화 감지 우회
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    all_results = []
    page_num = 1
    last_page_first_title = "" # 무한 루프 방지용 변수

    # 2. 검색 기간 설정 (오늘 ~ 60일 후)
    start_dt = datetime.datetime.now().strftime('%Y-%m-%d')
    end_dt = (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%Y-%m-%d')

    try:
        print(f"🚀 [데이터 수집 시작] 기간: {start_dt} ~ {end_dt}")
        
        while True:
            # 선생님이 발견하신 최적의 URL 구조 활용
            target_url = f"https://edu.kma.org/edu/schedule?pageNo={page_num}&start_dt={start_dt}&end_dt={end_dt}&sch_type=&sch_txt=&sch_es=&s_smallcode_Nm=&s_place=&siidx=&s_escidx=&s_scode="
            
            driver.get(target_url)
            time.sleep(3) # 페이지 로딩 대기

            # 데이터 추출 대상 (제목 및 상세 정보)
            titles = driver.find_elements(By.CSS_SELECTOR, "p.mb5[onclick^='$.viewer']")
            details = driver.find_elements(By.CSS_SELECTOR, "ul.cyberKindList")

            # [체크 1] 데이터가 아예 없는 경우 종료
            if not titles:
                print(f"\n✅ {page_num-1}페이지에서 수집 종료 (더 이상 데이터 없음)")
                break

            # [체크 2] 이전 페이지와 똑같은 내용이 나오면 종료 (의협 사이트 특성 방어)
            current_first_title = titles[0].text.strip()
            if current_first_title == last_page_first_title:
                print(f"\n✅ {page_num-1}페이지가 실제 마지막 페이지입니다.")
                break
            
            last_page_first_title = current_first_title

            # 데이터 파싱
            for i in range(len(titles)):
                try:
                    title_raw = titles[i].text.strip()
                    # 제목과 평점 분리
                    title = title_raw.split('평점')[0].strip()
                    credits = title_raw.split('평점')[-1].strip() if '평점' in title_raw else "0"
                    
                    detail_text = details[i].text.strip()
                    lines = detail_text.split('\n')
                    
                    date, inst, loc = "", "", ""
                    for line in lines:
                        if "교육일자" in line: date = line.replace("교육일자", "").strip()
                        if "기관명" in line: inst = line.replace("기관명", "").strip()
                        if "장소" in line: loc = line.replace("장소", "").strip()

                    all_results.append({
                        "title": title,
                        "credits": credits,
                        "date": date,
                        "institution": inst,
                        "location": loc,
                        "is_online": "온라인" in title or "온라인" in loc
                    })
                except Exception as e:
                    continue

            print(f"   - {page_num}페이지 수집 완료... (누적: {len(all_results)}건)", end="\r")
            page_num += 1

    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
    finally:
        # 3. JSON 파일로 저장
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 4. Git 자동 업데이트 (로컬 run.bat 실행 시 작동)
        if all_results:
            print(f"\n[업데이트 중] 총 {len(all_results)}건 데이터를 저장했습니다.")
            try:
                subprocess.run("git add .", shell=True)
                # 커밋 메시지에 날짜와 건수 포함
                msg = f"Auto-update: {datetime.datetime.now().strftime('%Y-%m-%d')} ({len(all_results)} items)"
                subprocess.run(f'git commit -m "{msg}"', shell=True, capture_output=True)
                subprocess.run("git push origin main", shell=True)
                print("✨ GitHub 반영 성공!")
            except:
                print("⚠️ Git 업데이트는 수동으로 진행하거나 GitHub Actions를 기다리세요.")
        
        driver.quit()

if __name__ == "__main__":
    fetch_kma_unlimited()